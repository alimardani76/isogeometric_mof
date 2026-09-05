"""Panel E Round 3 — final whole-view periodic-buffer + framing screen.

Freeze family:
    P1_U2_up_b_to_a

That means:
- E_i:  normal = a, up = b
- E_ii: normal = c, up = a

Round 3 tests only:
- finite control
- larger periodic context
- a few framing factors

No new camera family exploration.
"""

from pathlib import Path
import csv
import numpy as np

from e_config import E_I, E_II, OUT_ROOT, IMAGE_SIZE, DPI
from e_common import build_pipeline, direction_from_coeffs, make_renderer
from ovito.modifiers import ReplicateModifier
from ovito.vis import Viewport

OUT = OUT_ROOT / "42_E_periodic_crop"

# label, rep_i, rep_ii, fov_factor
CASES = [
    ("REF_plane22",        (1,2,2), (2,2,1), 1.00),
    ("BUFFER_144_ref",     (1,4,4), (4,4,1), 1.00),
    ("BUFFER_144_tight",   (1,4,4), (4,4,1), 0.92),
    ("BUFFER_144_context", (1,4,4), (4,4,1), 1.08),
    ("BUFFER_133_mid",     (1,3,3), (3,3,1), 0.96),
]

VIEW_I = (1,0,0)   # a
VIEW_II = (0,0,1)  # c
UP_I = (0,1,0)     # b
UP_II = (1,0,0)    # a

def add_rep(pipe, rep):
    pipe.modifiers.append(
        ReplicateModifier(num_x=rep[0], num_y=rep[1], num_z=rep[2], adjust_box=True)
    )

def projected_up(base, view_coeffs, up_coeffs):
    d = direction_from_coeffs(base, view_coeffs)
    u = direction_from_coeffs(base, up_coeffs)
    u = u - np.dot(u, d) * d
    n = np.linalg.norm(u)
    if n < 1e-8:
        raise RuntimeError("Selected up axis is parallel to view axis.")
    return d, u/n

def auto_fov_up(pipe, direction, up):
    pipe.add_to_scene()
    try:
        vp = Viewport(type=Viewport.Type.Ortho)
        vp.camera_dir = tuple(direction)
        vp.camera_up = tuple(up)
        vp.zoom_all(size=IMAGE_SIZE)
        return float(vp.fov)
    finally:
        pipe.remove_from_scene()

def render_up(pipe, direction, up, fov, outpath):
    outpath = Path(outpath)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    pipe.add_to_scene()
    try:
        vp = Viewport(type=Viewport.Type.Ortho)
        vp.camera_dir = tuple(direction)
        vp.camera_up = tuple(up)
        vp.zoom_all(size=IMAGE_SIZE)
        vp.fov = float(fov)
        vp.render_image(
            filename=str(outpath),
            size=IMAGE_SIZE,
            background=(1.0,1.0,1.0),
            renderer=make_renderer()
        )
    finally:
        pipe.remove_from_scene()

    try:
        from PIL import Image
        with Image.open(outpath) as im:
            im.save(outpath, dpi=(DPI,DPI))
    except Exception:
        pass

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows=[]

    print("="*92)
    print("PANEL E — FINAL WHOLE-VIEW BUFFER / CROP SCREEN")
    print("="*92)
    print("Frozen family: P1_U2_up_b_to_a")
    print("  E_i  view a, up b")
    print("  E_ii view c, up a")
    print("="*92)

    # reference FOV from the finite control pair
    pi0, bi0 = build_pipeline(E_I, hide_h=True)
    pii0, bii0 = build_pipeline(E_II, hide_h=True)
    add_rep(pi0, (1,2,2))
    add_rep(pii0, (2,2,1))
    di0, upi0 = projected_up(bi0, VIEW_I, UP_I)
    dii0, upii0 = projected_up(bii0, VIEW_II, UP_II)
    ref_fov = max(auto_fov_up(pi0, di0, upi0), auto_fov_up(pii0, dii0, upii0))

    for label,ri,rii,factor in CASES:
        print("\nrender:",label)
        print("  E_i rep :",ri)
        print("  E_ii rep:",rii)
        print("  factor  :",factor)

        pi, bi = build_pipeline(E_I, hide_h=True)
        pii, bii = build_pipeline(E_II, hide_h=True)
        add_rep(pi, ri)
        add_rep(pii, rii)

        di, upi = projected_up(bi, VIEW_I, UP_I)
        dii, upii = projected_up(bii, VIEW_II, UP_II)

        shared = ref_fov * factor

        oi = OUT / f"{label}__E_i.png"
        oii = OUT / f"{label}__E_ii.png"

        render_up(pi, di, upi, shared, oi)
        render_up(pii, dii, upii, shared, oii)

        rows.extend([
            {"case":label,"endpoint":"i","rep":str(ri),"fov":shared,"file":str(oi)},
            {"case":label,"endpoint":"ii","rep":str(rii),"fov":shared,"file":str(oii)},
        ])

    mp = OUT / "E_periodic_crop_manifest.csv"
    with mp.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    print("\nOutput:", OUT)

if __name__=="__main__":
    main()
