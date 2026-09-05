"""Regenerate the frozen Panel-D whole-view review pair.

Frozen geometry:
- c_plus
- 3x3x1 periodic buffer
- phase_half_a
- FOV 0.75 x matched 111 reference
"""

from pathlib import Path
import numpy as np
from d_config import D_I,D_II,OUT_ROOT,VIEW_COEFFS,PAIR_MARGIN,DPI
from d_common import build_pipeline,direction_from_coeffs,auto_fov,make_renderer,lattice_matrix
from ovito.modifiers import ReplicateModifier
from ovito.vis import Viewport

OUT=OUT_ROOT/"23_D_frozen_whole_review"
IMAGE_SIZE=(3200,2400)

def render_shifted(pipe,direction,fov,shift,outpath):
    outpath=Path(outpath); outpath.parent.mkdir(parents=True,exist_ok=True)
    pipe.add_to_scene()
    try:
        vp=Viewport(type=Viewport.Type.Ortho,camera_dir=tuple(direction))
        vp.zoom_all()
        vp.camera_pos=tuple(np.asarray(vp.camera_pos,dtype=float)+np.asarray(shift,dtype=float))
        vp.fov=float(fov)
        vp.render_image(
            filename=str(outpath),size=IMAGE_SIZE,background=(1,1,1),renderer=make_renderer()
        )
    finally:
        pipe.remove_from_scene()
    try:
        from PIL import Image
        with Image.open(outpath) as im: im.save(outpath,dpi=(DPI,DPI))
    except Exception: pass

def main():
    OUT.mkdir(parents=True,exist_ok=True)

    r1,b1=build_pipeline(D_I,hide_h=True)
    r2,b2=build_pipeline(D_II,hide_h=True)
    d1=direction_from_coeffs(b1,VIEW_COEFFS["c_plus"])
    d2=direction_from_coeffs(b2,VIEW_COEFFS["c_plus"])
    ref=max(auto_fov(r1,d1),auto_fov(r2,d2))*PAIR_MARGIN
    fov=ref*0.75

    H1=lattice_matrix(b1); H2=lattice_matrix(b2)
    shift1=H1@np.array([0.5,0,0])
    shift2=H2@np.array([0.5,0,0])

    p1,_=build_pipeline(D_I,hide_h=True)
    p2,_=build_pipeline(D_II,hide_h=True)
    p1.modifiers.append(ReplicateModifier(num_x=3,num_y=3,num_z=1,adjust_box=True))
    p2.modifiers.append(ReplicateModifier(num_x=3,num_y=3,num_z=1,adjust_box=True))

    render_shifted(p1,d1,fov,shift1,OUT/"D_i_WHOLE_FROZEN.png")
    render_shifted(p2,d2,fov,shift2,OUT/"D_ii_WHOLE_FROZEN.png")
    print("Output:",OUT)

if __name__=="__main__":
    main()
