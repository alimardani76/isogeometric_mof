from __future__ import annotations
from pathlib import Path
import csv, json, hashlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from .style import ROOT, apply_style


def _sha(p: Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def _contact(paths, out, title, cols=2):
    if not paths: return
    apply_style(7.0)
    rows=(len(paths)+cols-1)//cols
    fig,axs=plt.subplots(rows,cols,figsize=(cols*6.1,rows*4.5))
    import numpy as np
    axs=np.atleast_1d(axs).ravel()
    for ax,p in zip(axs,paths):
        ax.imshow(mpimg.imread(p)); ax.axis('off'); ax.set_title(p.stem.replace('_200dpi',''),loc='left',fontsize=9,fontweight='bold')
    for ax in axs[len(paths):]: ax.axis('off')
    fig.suptitle(title,fontsize=12,fontweight='bold',y=0.995)
    fig.tight_layout()
    fig.savefig(out,dpi=150,bbox_inches='tight'); plt.close(fig)


def build_contact_sheets():
    prev=ROOT/'outputs'/'previews'; prev.mkdir(parents=True,exist_ok=True)
    main=[]
    for n in ['Figure_01','Figure_02','Figure_03','Figure_04','Figure_06']:
        p=ROOT/'outputs'/'main'/n/f'{n}_200dpi.png'
        if p.exists(): main.append(p)
    si=[]
    for n,base in [
        ('Figure_S01','Figure_S01_Additional_Controls_200dpi.png'),
        ('Figure_S02','Figure_S02_HOA_Associations_200dpi.png'),
        ('Figure_S03','Figure_S03_Guest_Pressure_Specificity_200dpi.png'),
        ('Figure_S04','Figure_S04_Robustness_Geometry_Sensitivity_200dpi.png'),
        ('Figure_S05','Figure_S05_Structural_Geometry_Control_200dpi.png'),
        ('Figure_S06','Figure_S06_RASPA_Eight_Pair_Detail_200dpi.png')]:
        p=ROOT/'outputs'/'si'/n/base
        if p.exists(): si.append(p)
    _contact(main,prev/'MAIN_contact_sheet.png','Paper 7B · redesigned main quantitative figures',cols=2)
    _contact(si,prev/'SI_contact_sheet.png','Paper 7B · redesigned Supporting Information figures',cols=2)


def build_global_manifests():
    mdir=ROOT/'manifests'; mdir.mkdir(parents=True,exist_ok=True)
    files=[]
    for p in sorted((ROOT/'data').rglob('*')):
        if p.is_file(): files.append(('source',p))
    for p in sorted((ROOT/'outputs').rglob('*')):
        if p.is_file(): files.append(('output',p))
    with (mdir/'all_files_sha256.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['kind','path','sha256','bytes'])
        for kind,p in files: w.writerow([kind,str(p.relative_to(ROOT)),_sha(p),p.stat().st_size])
    rows=[]
    for mf in sorted((ROOT/'outputs').rglob('manifest.json')):
        try:
            obj=json.loads(mf.read_text(encoding='utf-8'))
            rows.append([obj.get('figure'),obj.get('font_resolved'),str(mf.relative_to(ROOT))])
        except Exception: pass
    with (mdir/'figure_manifest_index.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['figure','resolved_font','manifest']); w.writerows(rows)
