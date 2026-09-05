"""Panel C Round 2 — final whole-view periodic-buffer/framing screen.

Frozen camera:
    view normal = c
    camera up   = b

Reference visible family:
    2×2×1

This round only removes finite-edge ambiguity and selects final framing.
"""

from pathlib import Path
import csv

from c_config import C_I,C_II,OUT_ROOT,PAIR_MARGIN
from c_common import (
    build_pipeline,projected_up,auto_fov_up,render_up
)
from ovito.modifiers import ReplicateModifier

OUT = OUT_ROOT / "61_C_periodic_refine"

VIEW = (0,0,1)
UP   = (0,1,0)

# label, replication, FOV factor relative to original 2x2x1 shared reference
CASES = [
    ("CONTROL_221",        (2,2,1), 1.00),

    ("BUFFER_331_ref",     (3,3,1), 1.00),

    ("BUFFER_441_tight",   (4,4,1), 0.94),
    ("BUFFER_441_ref",     (4,4,1), 1.00),
    ("BUFFER_441_context", (4,4,1), 1.08),

    ("BUFFER_551_ref",     (5,5,1), 1.00),
]

def add_rep(pipe,rep):
    pipe.modifiers.append(
        ReplicateModifier(
            num_x=rep[0],
            num_y=rep[1],
            num_z=rep[2],
            adjust_box=True
        )
    )

def reference_fov():
    pi,bi=build_pipeline(C_I,hide_h=True)
    pii,bii=build_pipeline(C_II,hide_h=True)

    add_rep(pi,(2,2,1))
    add_rep(pii,(2,2,1))

    di,upi=projected_up(bi,VIEW,UP)
    dii,upii=projected_up(bii,VIEW,UP)

    return max(
        auto_fov_up(pi,di,upi),
        auto_fov_up(pii,dii,upii)
    ) * PAIR_MARGIN

def main():
    OUT.mkdir(parents=True,exist_ok=True)

    ref_fov = reference_fov()
    rows=[]

    print("="*96)
    print("PANEL C — FINAL WHOLE-VIEW PERIODIC BUFFER / FRAMING")
    print("="*96)
    print("Frozen camera : view c / up b")
    print("Reference     : 2x2x1")
    print(f"Reference FOV : {ref_fov:.6f}")
    print("="*96)

    for label,rep,factor in CASES:
        print("\nrender:",label)
        print("  rep    =",rep)
        print("  factor =",factor)

        pi,bi=build_pipeline(C_I,hide_h=True)
        pii,bii=build_pipeline(C_II,hide_h=True)
        add_rep(pi,rep)
        add_rep(pii,rep)

        di,upi=projected_up(bi,VIEW,UP)
        dii,upii=projected_up(bii,VIEW,UP)

        fov=ref_fov*factor

        oi=OUT/f"{label}__C_i.png"
        oii=OUT/f"{label}__C_ii.png"

        render_up(pi,di,upi,fov,oi)
        render_up(pii,dii,upii,fov,oii)

        rows.extend([
            {
                "case":label,
                "endpoint":"i",
                "rep":str(rep),
                "fov":fov,
                "file":str(oi)
            },
            {
                "case":label,
                "endpoint":"ii",
                "rep":str(rep),
                "fov":fov,
                "file":str(oii)
            },
        ])

    mp=OUT/"C_periodic_refine_manifest.csv"
    with mp.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    print("\nOutput:",OUT)
    print("Manifest:",mp)

if __name__=="__main__":
    main()
