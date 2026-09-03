"""Render the frozen Panel B whole-view review pair.

Frozen:
- c_plus
- B04 style
- 3x3x1 periodic buffer
- phase_00
- FOV = 0.96 × one-cell reference
"""

from pathlib import Path
from p7b_ovito_config import (
    OUT_ROOT, VIEW_COEFFS_FULL, cif_paths, B_PAIRWISE_CUTOFFS, PAIR_MARGIN
)
from p7b_ovito_common import (
    build_pipeline, direction_from_coeffs, auto_fov, render_with_fov
)

PAL_CLEAN={
    "H":(0.91,0.91,0.91),"C":(0.28,0.28,0.28),"N":(0.20,0.38,0.78),
    "O":(0.84,0.20,0.20),"Zn":(0.25,0.48,0.72),"Cu":(0.82,0.42,0.16),
    "V":(0.40,0.55,0.70),"I":(0.42,0.18,0.52)
}
RECIPE=dict(
    h_mode="hide",h_radius=0.10,particle_scale=1.0,
    radii={"C":0.28,"O":0.34,"Zn":0.62,"Cu":0.62,"I":0.37},
    bond_width=0.12,bond_color=(0.48,0.48,0.48),bond_coloring="uniform",
    palette=PAL_CLEAN,show_cell=False,ao=False,bond_mode="pairwise",
    pair_cutoffs=B_PAIRWISE_CUTOFFS
)

def main():
    paths=cif_paths("B")
    outdir=OUT_ROOT/"09_B_frozen_whole_review"
    outdir.mkdir(parents=True,exist_ok=True)

    # matched 111 reference FOV
    r1,b1=build_pipeline(paths["i"],rep=(1,1,1),recipe=RECIPE)
    r2,b2=build_pipeline(paths["ii"],rep=(1,1,1),recipe=RECIPE)
    d1=direction_from_coeffs(b1,VIEW_COEFFS_FULL["c_plus"])
    d2=direction_from_coeffs(b2,VIEW_COEFFS_FULL["c_plus"])
    ref=max(auto_fov(r1,d1),auto_fov(r2,d2))*PAIR_MARGIN

    p1,_=build_pipeline(paths["i"],rep=(3,3,1),recipe=RECIPE)
    p2,_=build_pipeline(paths["ii"],rep=(3,3,1),recipe=RECIPE)

    fov=ref*0.96
    render_with_fov(p1,d1,fov,outdir/"B_i_WHOLE_FROZEN.png",ao=False)
    render_with_fov(p2,d2,fov,outdir/"B_ii_WHOLE_FROZEN.png",ao=False)
    print("Output:",outdir)

if __name__=="__main__":
    main()
