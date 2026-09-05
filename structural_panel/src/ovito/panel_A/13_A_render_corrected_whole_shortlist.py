"""Panel A — corrected whole-view shortlist after adding Zn-N.

Only four paired cases are rendered:
1. M1 mapped 2x2 family, current finite control
2. M1 large periodic buffer at FOV 0.82
3. M1 large periodic buffer at FOV 0.88
4. M3 mapped 2x2 backup (one sanity check)

No broad geometry sweep is repeated.
"""

from pathlib import Path
import csv

from a_config import A_I,A_II,OUT_ROOT,DPI
from a_common import build_pipeline,direction_from_coeffs,auto_fov,render
from ovito.modifiers import ReplicateModifier

OUT=OUT_ROOT/"35_A_corrected_whole_shortlist"

CASES=[
    ("M1_control_fov0p82",(1,0,0),(0,0,1),(1,2,2),(2,2,1),"M1",0.82),
    ("M1_buffer_fov0p82",(1,0,0),(0,0,1),(1,5,5),(5,5,1),"M1",0.82),
    ("M1_buffer_fov0p88",(1,0,0),(0,0,1),(1,5,5),(5,5,1),"M1",0.88),
    ("M3_backup_plane22",(0,0,1),(1,0,0),(2,2,1),(1,2,2),"M3",1.00),
]

def add_rep(pipe,rep):
    pipe.modifiers.append(
        ReplicateModifier(num_x=rep[0],num_y=rep[1],num_z=rep[2],adjust_box=True)
    )

def ref_fov(family):
    if family=="M1":
        vi,vii=(1,0,0),(0,0,1)
        ri,rii=(1,2,2),(2,2,1)
    else:
        vi,vii=(0,0,1),(1,0,0)
        ri,rii=(2,2,1),(1,2,2)

    pi,bi=build_pipeline(A_I,hide_h=True)
    pii,bii=build_pipeline(A_II,hide_h=True)
    add_rep(pi,ri); add_rep(pii,rii)
    di=direction_from_coeffs(bi,vi)
    dii=direction_from_coeffs(bii,vii)
    return max(auto_fov(pi,di),auto_fov(pii,dii))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    refs={"M1":ref_fov("M1"),"M3":ref_fov("M3")}
    rows=[]

    for label,vi,vii,ri,rii,family,factor in CASES:
        print("render:",label)
        pi,bi=build_pipeline(A_I,hide_h=True)
        pii,bii=build_pipeline(A_II,hide_h=True)
        add_rep(pi,ri); add_rep(pii,rii)
        di=direction_from_coeffs(bi,vi)
        dii=direction_from_coeffs(bii,vii)
        fov=refs[family]*factor

        oi=OUT/f"{label}__A_i.png"
        oii=OUT/f"{label}__A_ii.png"
        render(pi,di,fov,oi)
        render(pii,dii,fov,oii)
        rows.extend([
            {"case":label,"endpoint":"i","fov":fov,"file":str(oi)},
            {"case":label,"endpoint":"ii","fov":fov,"file":str(oii)},
        ])

    with (OUT/"manifest.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)

    print("Output:",OUT)

if __name__=="__main__":
    main()
