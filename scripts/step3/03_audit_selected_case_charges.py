#!/usr/bin/env python3
"""Project 7B2 Step 3, file 03: selected-case REPEAT-charge feasibility.

Place inside: Step 3 production/
Run: python "Step 3 production/03_audit_selected_case_charges.py"

Audits only the 12 frozen case frameworks. Charge columns are discovered from
CIF atom-site loop fields and accepted only when row-aligned with atom-site
symbols. No linker/site assignment, oxidation state, direction, or mechanism
is inferred.
"""
from __future__ import annotations
import hashlib, json, re, sys, tarfile
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from pymatgen.core import Element
from pymatgen.io.cif import CifFile

STEP3=Path(__file__).resolve().parent
ROOT=STEP3.parent
CASES=ROOT/'Step 3 results'/'case_selection'/'02_final_case_set.csv'
OUT=ROOT/'Step 3 results'/'case_chemistry'; OUT.mkdir(parents=True,exist_ok=True)
SYMBOL_KEYS=['_atom_site_type_symbol']
LABEL_KEYS=['_atom_site_label']
OCC_KEYS=['_atom_site_occupancy']
PREFERRED_CHARGE_KEYS=[
 '_atom_site_charge','_atom_site_partial_charge','_atom_site_charge_repeat',
 '_atom_type_partial_charge','_atom_site_fract_charge','_atom_site_repeated_charge'
]

def sha256(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def cid(x):
 x=str(x).strip();x=re.sub(r'(?i)\.cif$','',x);x=re.sub(r'(?i)_repeat$','',x);return x
def archive():
 xs=list(ROOT.rglob('ARCMOF_20241004.tar.gz'))
 if len(xs)!=1:raise RuntimeError(f'Expected one ARCMOF_20241004.tar.gz, found {xs}')
 return xs[0]
def is_metal(sym):
 try:
  e=Element(sym);return bool(e.is_metal or e.is_metalloid)
 except Exception:return False
def as_list(x):return list(x) if isinstance(x,(list,tuple)) else [x]
def first(block,keys):
 for k in keys:
  if k in block.data:return k,as_list(block.data[k])
 return None,None
def clean_symbol(x):
 m=re.match(r'([A-Z][a-z]?)',str(x).strip());return m.group(1) if m else str(x).strip()
def discover_charge(block,nrows):
 keys=list(block.data.keys())
 candidates=[]
 for k in keys:
  kl=k.lower()
  if 'charge' not in kl and not ('partial' in kl and ('atom' in kl or 'site' in kl)):
   continue
  values=as_list(block.data[k])
  numeric=pd.to_numeric(pd.Series(values),errors='coerce')
  candidates.append({'key':k,'rows':len(values),'numeric':int(numeric.notna().sum()),'values':values})
 # preferred exact names first, then fully numeric row-aligned discovered fields
 candidates.sort(key=lambda d:(0 if d['key'] in PREFERRED_CHARGE_KEYS else 1,d['key']))
 valid=[d for d in candidates if d['rows']==nrows and d['numeric']==nrows]
 if len(valid)==1:return valid[0],candidates
 if len(valid)>1:
  preferred=[d for d in valid if d['key'] in PREFERRED_CHARGE_KEYS]
  if len(preferred)==1:return preferred[0],candidates
  raise ValueError('Ambiguous row-aligned charge columns: '+', '.join(d['key'] for d in valid))
 return None,candidates

def parse_one(mof_id,raw,member):
 rec={'mof_id':mof_id,'archive_member':member,'mapping_ok':False,'error':None,
      'all_cif_keys':None,'charge_like_fields':None}
 try:
  cf=CifFile.from_str(raw.decode('utf-8','strict'))
  if len(cf.data)!=1:raise ValueError(f'Expected one CIF block, found {len(cf.data)}')
  block=next(iter(cf.data.values()));rec['all_cif_keys']=';'.join(map(str,block.data.keys()))
  sk,symbols=first(block,SYMBOL_KEYS);lk,labels=first(block,LABEL_KEYS);ok,occ=first(block,OCC_KEYS)
  if sk is None:raise ValueError('No atom-site type-symbol column')
  n=len(symbols);charge,cands=discover_charge(block,n)
  rec['charge_like_fields']=';'.join(f"{d['key']}[rows={d['rows']},numeric={d['numeric']}]" for d in cands)
  if charge is None:raise ValueError('No unique numeric charge-like field row-aligned with atom-site symbols')
  labels=labels if labels is not None else [None]*n;occ=occ if occ is not None else [1.0]*n
  lens={'charge':len(charge['values']),'symbol':len(symbols),'label':len(labels),'occupancy':len(occ)}
  if len(set(lens.values()))!=1:raise ValueError(f'Atom-row length mismatch: {lens}')
  q=pd.to_numeric(pd.Series(charge['values']),errors='coerce');o=pd.to_numeric(pd.Series(occ),errors='coerce')
  if q.isna().any():raise ValueError(f'Non-numeric charges: {int(q.isna().sum())}')
  if o.isna().any() or (o<=0).any() or (o>1).any():raise ValueError('Invalid occupancies')
  atoms=pd.DataFrame({'mof_id':mof_id,'atom_row':np.arange(n),'label':labels,
   'element':[clean_symbol(x) for x in symbols],'occupancy':o.astype(float),'repeat_charge':q.astype(float)})
  atoms['is_metal']=atoms.element.map(is_metal);atoms['occupancy_weighted_charge']=atoms.occupancy*atoms.repeat_charge
  rec.update({'mapping_ok':True,'charge_column':charge['key'],'symbol_column':sk,'label_column':lk,
   'occupancy_column':ok,'atom_rows':n,'numeric_charges':n,'minimum_occupancy':float(atoms.occupancy.min()),
   'charge_sum':float(atoms.repeat_charge.sum()),'occupancy_weighted_charge_sum':float(atoms.occupancy_weighted_charge.sum()),
   'metal_atom_rows':int(atoms.is_metal.sum()),'elements':';'.join(sorted(atoms.element.unique())),
   'metals':';'.join(sorted(atoms.loc[atoms.is_metal,'element'].unique()))})
  return rec,atoms
 except Exception as e:rec['error']=f'{type(e).__name__}: {e}';return rec,None

def main():
 if not CASES.exists():raise FileNotFoundError(CASES)
 cases=pd.read_csv(CASES);ids=set(cases.id_a.map(cid))|set(cases.id_b.map(cid));arc=archive();found={};members={}
 with tarfile.open(arc,'r:gz') as t:
  for m in t:
   if not m.isfile():continue
   name=cid(Path(m.name).name)
   if name in ids:
    found[name]=t.extractfile(m).read();members[name]=m.name
    if len(found)==len(ids):break
 audit=[];parts=[]
 for x in sorted(ids):
  if x not in found:audit.append({'mof_id':x,'mapping_ok':False,'error':'archive member not found'});continue
  rec,a=parse_one(x,found[x],members[x]);audit.append(rec)
  if a is not None:parts.append(a)
 ad=pd.DataFrame(audit);ad.to_csv(OUT/'03_charge_mapping_audit.csv',index=False)
 if not ad.mapping_ok.all():
  raise RuntimeError(f'Charge mapping failed for {int((~ad.mapping_ok).sum())} frameworks; inspect 03_charge_mapping_audit.csv')
 atoms=pd.concat(parts,ignore_index=True);atoms.to_csv(OUT/'03_atom_charge_rows.csv',index=False)
 fw=atoms.groupby('mof_id').agg(atom_rows=('atom_row','size'),charge_sum=('repeat_charge','sum'),
  occupancy_weighted_charge_sum=('occupancy_weighted_charge','sum'),charge_mean=('repeat_charge','mean'),
  charge_std=('repeat_charge','std'),charge_min=('repeat_charge','min'),charge_max=('repeat_charge','max'),metal_rows=('is_metal','sum')).reset_index()
 fw.to_csv(OUT/'03_framework_charge_summaries.csv',index=False)
 el=atoms.groupby(['mof_id','element','is_metal']).agg(atom_rows=('atom_row','size'),charge_mean=('repeat_charge','mean'),
  charge_median=('repeat_charge','median'),charge_std=('repeat_charge','std'),charge_min=('repeat_charge','min'),
  charge_max=('repeat_charge','max'),occupancy_weighted_charge_sum=('occupancy_weighted_charge','sum')).reset_index()
 el.to_csv(OUT/'03_element_charge_summaries.csv',index=False)
 rows=[]
 for _,r in cases.iterrows():
  a,b=cid(r.id_a),cid(r.id_b);ea=el[el.mof_id.eq(a)];eb=el[el.mof_id.eq(b)]
  ma=sorted(ea.loc[ea.is_metal,'element'].unique());mb=sorted(eb.loc[eb.is_metal,'element'].unique())
  rows.append({'selection_category':r.selection_category,'pair_key':r.pair_key,'intervention':r.intervention,
   'transition':r.transition,'id_a':a,'id_b':b,'shared_elements':';'.join(sorted(set(ea.element)&set(eb.element))),
   'metals_a':';'.join(ma),'metals_b':';'.join(mb),'framework_charge_sum_a':float(fw.loc[fw.mof_id.eq(a),'charge_sum'].iloc[0]),
   'framework_charge_sum_b':float(fw.loc[fw.mof_id.eq(b),'charge_sum'].iloc[0]),'same_metal_identity':ma==mb,
   'metal_charge_comparison_status':'COMPARABLE_SAME_METAL_ELEMENT' if ma==mb else 'DIFFERENT_METAL_ELEMENTS_DESCRIPTIVE_ONLY'})
 pd.DataFrame(rows).to_csv(OUT/'03_pair_charge_contrasts.csv',index=False)
 report=['PROJECT 7B2 SELECTED-CASE CHARGE FEASIBILITY','='*72,'Decision: PASS',f'Frozen cases: {len(cases)}',
  f'Frameworks audited: {len(ids)}',f'Exact charge-row mappings: {int(ad.mapping_ok.sum())}',f'Atom rows extracted: {len(atoms)}','',
  'Permitted use: element-level and metal-element charge summaries for the six selected examples.',
  'Not permitted: automatic linker assignment, adsorption-site maps, oxidation states, causal mechanism, or global charge rule.']
 (OUT/'03_report.txt').write_text('\n'.join(report),encoding='utf-8',newline='\n')
 manifest={'stage':'selected-case REPEAT-charge feasibility','created':datetime.now().isoformat(timespec='seconds'),
  'script':'03_audit_selected_case_charges.py','inputs':{str(CASES):sha256(CASES),str(arc):sha256(arc)},
  'case_count':len(cases),'framework_count':len(ids),'mapping_failures':0,'imputation':False,
  'site_or_linker_assignment':False,'mechanism_claim':False,
  'outputs':['03_charge_mapping_audit.csv','03_atom_charge_rows.csv','03_framework_charge_summaries.csv','03_element_charge_summaries.csv','03_pair_charge_contrasts.csv','03_report.txt'],
  'python':sys.version,'pandas':pd.__version__}
 (OUT/'03_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
 print('\n'.join(report));print(f'\nOutputs: {OUT}')
if __name__=='__main__':main()
