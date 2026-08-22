#!/usr/bin/env python3
"""Project 7B2 Step 3, file 05: freeze figure blueprint and caption architecture.

Place inside: Step 3 production/
Run: python "Step 3 production/05_freeze_figure_blueprint.py"

No scientific values are recalculated. The script verifies the packaged source
registry and writes the final panel plan for Figures 1--6.
"""
from pathlib import Path
import json, hashlib, sys
from datetime import datetime
import pandas as pd

STEP3=Path(__file__).resolve().parent
ROOT=STEP3.parent
SRC=ROOT/'Step 3 results'/'figure_source_data'
OUT=ROOT/'Step 3 results'/'figure_blueprint';OUT.mkdir(parents=True,exist_ok=True)
REG=SRC/'04_source_registry.csv';INDEX=SRC/'04_figure_index.csv';MISS=SRC/'04_missing_optional_sources.csv'

def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 for p in [REG,INDEX,MISS]:
  if not p.exists():raise FileNotFoundError(p)
 reg=pd.read_csv(REG);idx=pd.read_csv(INDEX)
 if set(idx.figure)!=set(range(1,7)):raise RuntimeError('Figure index is not exactly Figures 1--6')
 if set(reg.figure)!=set(range(1,7)):raise RuntimeError('Source registry does not cover exactly Figures 1--6')

 panels=[
 [1,'a','Concept','Why matched natural experiments are needed','Conceptual confounding diagram: chemistry and geometry co-vary in global databases; matched design constrains measured structure.','diagram','No numerical estimate','Main'],
 [1,'b','Cohort','What evidence enters the study?','Cohort flow from ARC--MOF reference through chemistry verification to 13,072 primary pairs.','flow','Exact frozen counts','Main'],
 [1,'c','Matching','How was structural control defined?','Seven geometry controls, exact topology/dimensionality, and fixed caliper tiers.','schematic+table','Predeclared physical limits','Main'],
 [1,'d','Support','Where is support available?','Pairs, related groups, exact changes, and support contraction across tiers.','dot/line','Counts only','Main'],

 [2,'a','Primary evidence','Do linker changes exceed matched background variation?','Control-relative linker contrasts across 18 conditions for absolute-log and standardized measures.','forest/interval','Common-support-cell bootstrap','Main'],
 [2,'b','Symmetric control','Does the result survive equal pair selection in both arms?','Symmetric nearest-pair chemistry-minus-control contrasts.','forest/interval','Cell bootstrap','Main'],
 [2,'c','Energetic correlate','Does energetic separation track adsorption separation?','Condition-level Spearman association between absolute HOA contrast and adsorption separation; linker primary, metal secondary.','heatmap/forest','Related-group bootstrap','Main'],
 [2,'d','Residual adjustment','Does measured residual geometry explain the linker result?','Unadjusted versus seven-variable adjusted linker-control contrast.','paired interval','Support-cell bootstrap','Main'],

 [3,'a','Pressure response','How does adsorption separation change with pressure?','Low/high absolute-log adsorption separation for linker and metal classes.','slope/dumbbell','Related-group summaries','Main'],
 [3,'b','Energetic persistence','Does HOA contrast disappear at high pressure?','Low/high absolute HOA contrast showing persistence or increase in most comparisons.','slope/dumbbell','Related-group summaries','Main'],
 [3,'c','Guest specificity','Is CO2 more chemistry-sensitive than co-guests?','Paired CO2-minus-co-guest absolute-log and HOA contrasts across four processes and two regimes.','diverging forest','Paired-family bootstrap','Main'],
 [3,'d','Boundary','Where does energetic and uptake sensitivity decouple?','High-pressure pre-combustion CO2/H2 reversal: HOA remains CO2-dominant while absolute-log adsorption separation becomes H2-dominant.','focused paired panel','Paired-family bootstrap','Main'],

 [4,'a','Calipers','Does the conclusion survive alternative geometric similarity definitions?','Support and pressure-direction stability across very-tight, tight, primary, and moderate tiers.','support+direction matrix','Group bootstrap','Main'],
 [4,'b','Reciprocal design','Does outcome-blind reciprocal matching change conclusions?','Class and exact-transition agreement under reciprocal covariance matching.','agreement matrix','Frozen comparisons','Main'],
 [4,'c','Topology','Does topology provenance alter metal conclusions?','High-confidence topology restriction and exact-transition agreement.','agreement matrix','Frozen comparisons','Main'],
 [4,'d','Residual geometry','How much measured geometry remains associated with effect magnitude?','Residual-geometry correlations and adjusted attenuation.','forest/interval','Group/support-cell bootstrap','Main'],
 [4,'e','Family dominance','Are results driven by the largest families?','Relative effect changes after excluding the largest and ten largest groups.','compact interval/dot','Group bootstrap','Main or SI'],

 [5,'a','Strong linker','What does a large linker contrast look like?','Frozen strong linker/process-aligned case with structures, geometry, adsorption, HOA, process, and charge fingerprint.','case card','Descriptive selected case','Main'],
 [5,'b','Strong metal','What does a strong coordination-compatible metal contrast look like?','Frozen Cu--Zn process-aligned case.','case card','Descriptive selected case','Main'],
 [5,'c','Pressure exception','How can the same nominal metal contrast behave differently?','Frozen Cu--Zn pressure-exception case.','case card','Descriptive selected case','Main'],
 [5,'d','Near null','When does a chemistry change produce little adsorption separation?','Frozen near-null linker case.','case card','Descriptive selected case','Main'],
 [5,'e','Process discordance','When does uptake separation fail process translation?','Frozen process-discordant linker case.','case card','Descriptive selected case','Main'],
 [5,'f','Functional motif','What can be shown without a class-level claim?','Frozen functional-motif example labelled exploratory.','case card','Descriptive selected case','Main/SI'],

 [6,'a','Working capacity','Does uptake separation survive retained loading?','Uptake--working-capacity concordance and oriented differences by process and intervention.','forest/dot','Related-group bootstrap','Main'],
 [6,'b','Selectivity','Does uptake separation survive competitive performance?','Uptake--selectivity concordance, highlighting weaker pre-combustion alignment.','forest/dot','Related-group bootstrap','Main'],
 [6,'c','Bounded design map','What can a chemist safely infer?','Evidence map: linker strong, metal conditional, functional motif unsupported; supported gases/pressures/process consequences and failure boundaries.','evidence matrix','Claim-evidence matrix','Main'],
 ]
 cols=['figure','panel','panel_title','chemical_question','content','recommended_visual','uncertainty_or_status','placement']
 bp=pd.DataFrame(panels,columns=cols);bp.to_csv(OUT/'05_panel_blueprint.csv',index=False)

 headlines={
 1:'A matched natural-experiment design separates defined chemistry changes from major measured structural variation.',
 2:'Linker chemistry produces adsorption and energetic separation beyond matched same-chemistry variation, with partial attenuation after residual-geometry adjustment.',
 3:'CO2 is generally more energetically and multiplicatively chemistry-sensitive than co-guests, but high-pressure H2 provides a clear uptake boundary.',
 4:'The principal conclusions survive alternative matching, topology restrictions, and family exclusions, while residual geometry remains a measurable modifier.',
 5:'Structure-resolved cases show strong, null, exceptional, discordant, and exploratory outcomes within the matched domain.',
 6:'Adsorption advantages often persist into working capacity but less reliably into selectivity, defining bounded rather than universal chemical guidance.'}
 cap=[]
 for fig in range(1,7):
  ps=bp[bp.figure.eq(fig)]
  cap.append(f"\\textbf{{Figure {fig}. {headlines[fig]}}} ")
  cap.append('Panels: '+ '; '.join(f"({r.panel}) {r.panel_title}" for _,r in ps.iterrows())+'. ')
  cap.append('Each final caption must define the plotted cohort, effect measure, dependence unit, uncertainty interval, and unsupported cells.\n')
 (OUT/'05_caption_skeletons.tex').write_text('\n'.join(cap),encoding='utf-8',newline='\n')

 figsum=bp.groupby('figure').agg(panels=('panel','count'),main_panels=('placement',lambda s:int(s.str.contains('Main').sum()))).reset_index()
 figsum['headline']=figsum.figure.map(headlines);figsum.to_csv(OUT/'05_figure_summary.csv',index=False)
 report=['PROJECT 7B2 FIGURE BLUEPRINT','='*72,'Decision: PANEL ARCHITECTURE FROZEN FOR FIGURES 1--6','']
 for _,r in figsum.iterrows():report.append(f"Figure {r.figure}: {r.panels} panels | {r.headline}")
 report += ['', 'Rules:', '- one chemical question per panel', '- no SHAP/model leaderboard panels',
 '- Figure 3 carries the energetic/guest-specificity advance and CO2/H2 boundary',
 '- Figure 4 states residual-geometry imbalance rather than hiding it',
 '- Figure 5 uses charge only as a selected-case fingerprint',
 '- Figure 6 is bounded guidance, not directional substitution rules']
 (OUT/'05_report.txt').write_text('\n'.join(report),encoding='utf-8',newline='\n')
 man={'stage':'figure blueprint freeze','created':datetime.now().isoformat(timespec='seconds'),'script':'05_freeze_figure_blueprint.py',
 'inputs':{str(REG):sha(REG),str(INDEX):sha(INDEX),str(MISS):sha(MISS)},'new_analysis':False,'figure_count':6,'panel_count':len(bp),
 'outputs':['05_panel_blueprint.csv','05_figure_summary.csv','05_caption_skeletons.tex','05_report.txt'],'python':sys.version,'pandas':pd.__version__}
 (OUT/'05_manifest.json').write_text(json.dumps(man,indent=2),encoding='utf-8',newline='\n')
 print('\n'.join(report));print(f'\nOutputs: {OUT}')
if __name__=='__main__':main()
