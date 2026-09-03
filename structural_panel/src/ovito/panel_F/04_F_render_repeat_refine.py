"""Panel F Round 2 — final repeated-scaffold periodic-buffer/framing screen.

Frozen primary family:
    view normal = a
    camera up   = c
    original visual family = 1x2x2

Backup roll:
    view normal = a
    camera up   = b

The larger 1x3x3 / 1x5x5 cells act as periodic data buffers.
The visible field remains tied to the original 1x2x2 family.
"""

from pathlib import Path
import csv
import numpy as np

from f_config import F_I,F_II,OUT_ROOT,IMAGE_SIZE,DPI
from f_common import (
    build_pipeline,projected_up,auto_fov_up,render_up
)
from ovito.modifiers import ReplicateModifier

OUT = OUT_ROOT / "51_F_repeat_refine"

VIEW = (1,0,0)

# label, up-vector, replication, FOV factor relative to that roll's 1x2x2 reference
CASES = [
    ("PRIMARY_control_122",        (0,0,1), (1,2,2), 1.00),
    ("PRIMARY_buffer_133_ref",     (0,0,1), (1,3,3), 1.00),
    ("PRIMARY_buffer_155_ref",     (0,0,1), (1,5,5), 1.00),
    ("PRIMARY_buffer_155_tight",   (0,0,1), (1,5,5), 0.92),
    ("PRIMARY_buffer_155_context", (0,0,1), (1,5,5), 1.08),
    ("BACKUP_up_b_155_ref",        (0,1,0), (1,5,5), 1.00),
    ("BACKUP_up_b_155_context",    (0,1,0), (1,5,5), 1.08),
]

def add_rep(pipe,rep):
    pipe.modifiers.append(
        ReplicateModifier(
            num_x=rep[0],num_y=rep[1],num_z=rep[2],adjust_box=True
        )
    )

def reference_fov(up):
    pi,bi=build_pipeline(F_I,hide_h=True)
    pii,bii=build_pipeline(F_II,hide_h=True)
    add_rep(pi,(1,2,2))
    add_rep(pii,(1,2,2))

    di,upi=projected_up(bi,VIEW,up)
    dii,upii=projected_up(bii,VIEW,up)

    return max(
        auto_fov_up(pi,di,upi),
        auto_fov_up(pii,dii,upii)
    )

def main():
    OUT.mkdir(parents=True,exist_ok=True)

    ref_c=reference_fov((0,0,1))
    ref_b=reference_fov((0,1,0))

    rows=[]

    print("="*94)
    print("PANEL F — FINAL REPEATED-SCAFFOLD PERIODIC / FRAMING SCREEN")
    print("="*94)
    print("Primary family: view a / up c")
    print("Backup roll   : view a / up b")
    print(f"Reference FOV (up c): {ref_c:.6f}")
    print(f"Reference FOV (up b): {ref_b:.6f}")
    print("="*94)

    for label,up,rep,factor in CASES:
        print("\nrender:",label)
        print("  up     =",up)
        print("  rep    =",rep)
        print("  factor =",factor)

        pi,bi=build_pipeline(F_I,hide_h=True)
        pii,bii=build_pipeline(F_II,hide_h=True)
        add_rep(pi,rep)
        add_rep(pii,rep)

        di,upi=projected_up(bi,VIEW,up)
        dii,upii=projected_up(bii,VIEW,up)

        base = ref_c if up==(0,0,1) else ref_b
        fov = base*factor

        oi=OUT/f"{label}__F_i.png"
        oii=OUT/f"{label}__F_ii.png"

        render_up(pi,di,upi,fov,oi)
        render_up(pii,dii,upii,fov,oii)

        rows.extend([
            {"case":label,"endpoint":"i","rep":str(rep),"fov":fov,"file":str(oi)},
            {"case":label,"endpoint":"ii","rep":str(rep),"fov":fov,"file":str(oii)},
        ])

    mp=OUT/"F_repeat_refine_manifest.csv"
    with mp.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    print("\nOutput:",OUT)

if __name__=="__main__":
    main()
