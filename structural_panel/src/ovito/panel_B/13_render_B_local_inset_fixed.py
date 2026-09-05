"""Panel B — corrected local Zn/Cu inset screening.

Fixes two issues in the previous local-inset round:
1. PBC-wrapped graph neighbors appearing as detached atoms in oblique views.
2. Local object rendered tiny because viewport fitting included the large simulation cell.

Method:
- Build a 3x3x3 periodic buffer.
- Choose a central Zn/Cu site.
- Keep graph depth 1/2/3 around that site.
- Fit the orthographic camera to the retained particle cluster itself.
"""

from pathlib import Path
import numpy as np

from p7b_ovito_config import (
    OUT_ROOT, VIEW_COEFFS_FULL, cif_paths, B_PAIRWISE_CUTOFFS, DPI
)
from p7b_ovito_common import (
    build_pipeline, direction_from_coeffs, make_renderer
)

from ovito.modifiers import DeleteSelectedModifier
from ovito.vis import Viewport

BUFFER_REP = (3,3,3)
IMAGE_SIZE = (3200,2400)

PAL_INSET = {
    "H":  (0.92,0.92,0.92),
    "C":  (0.30,0.30,0.30),
    "N":  (0.20,0.38,0.78),
    "O":  (0.84,0.20,0.20),
    "Zn": (0.25,0.48,0.72),
    "Cu": (0.82,0.42,0.16),
    "V":  (0.40,0.55,0.70),
    "I":  (0.42,0.18,0.52),
}

BASE_RECIPE = dict(
    h_mode="hide",
    h_radius=0.10,
    particle_scale=1.0,
    radii={"C":0.34, "O":0.46, "Zn":0.82, "Cu":0.82, "I":0.38},
    bond_width=0.16,
    bond_color=(0.42,0.42,0.42),
    bond_coloring="uniform",
    palette=PAL_INSET,
    show_cell=False,
    ao=False,
    bond_mode="pairwise",
    pair_cutoffs=B_PAIRWISE_CUTOFFS,
)

CASES = [
    ("D2_ab_plus",      2, "ab_plus",  False),
]

def type_info(data):
    prop = data.particles["Particle Type"]
    ids = np.asarray(prop)
    names = {t.id:t.name for t in prop.types}
    return ids, names

def cell_center(data):
    H4 = np.asarray(data.cell, dtype=float)
    H = H4[:3,:3]
    origin = H4[:3,3] if H4.shape[1] >= 4 else np.zeros(3)
    return origin + H @ np.array([0.5,0.5,0.5])

def choose_central_metal(data, metal_name):
    pos = np.asarray(data.particles.positions)
    ids, names = type_info(data)
    ctr = cell_center(data)

    candidates = [
        (float(np.dot(pos[i]-ctr, pos[i]-ctr)), i)
        for i, tid in enumerate(ids)
        if names.get(int(tid)) == metal_name
    ]
    if not candidates:
        raise RuntimeError(f"No {metal_name} site found.")
    candidates.sort()
    return candidates[0][1]

def graph_keep(data, metal_name, depth):
    if data.particles.bonds is None:
        raise RuntimeError("No pairwise bonds present.")

    topology = np.asarray(data.particles.bonds.topology, dtype=int)
    n = data.particles.count
    adj = [[] for _ in range(n)]
    for a,b in topology:
        adj[a].append(b)
        adj[b].append(a)

    start = choose_central_metal(data, metal_name)
    keep = {start}
    frontier = {start}
    for _ in range(depth):
        nxt = set()
        for i in frontier:
            nxt.update(adj[i])
        nxt -= keep
        keep.update(nxt)
        frontier = nxt

    return start, sorted(keep)

def local_pipeline(cif_path, metal_name, depth, ao=False):
    recipe = dict(BASE_RECIPE)
    recipe["ao"] = ao

    pipe, base = build_pipeline(cif_path, rep=BUFFER_REP, recipe=recipe)
    data = pipe.compute()
    start, keep = graph_keep(data, metal_name, depth)
    keep_set = set(keep)

    def select_nonlocal(frame, data):
        sel = np.ones(data.particles.count, dtype=np.int32)
        for i in keep_set:
            sel[i] = 0
        data.particles_.create_property("Selection", data=sel)

    pipe.modifiers.append(select_nonlocal)
    pipe.modifiers.append(DeleteSelectedModifier())
    return pipe, base, start, keep

def cluster_geometry(pipeline):
    data = pipeline.compute()
    pos = np.asarray(data.particles.positions, dtype=float)
    if len(pos) == 0:
        raise RuntimeError("Local cluster is empty.")
    center = pos.mean(axis=0)
    r = float(np.max(np.linalg.norm(pos-center, axis=1)))
    return center, max(r, 1.0), data

def render_local(pipeline, direction, fov, center, outpath, ao=False):
    outpath = Path(outpath)
    outpath.parent.mkdir(parents=True, exist_ok=True)

    direction = np.asarray(direction, dtype=float)
    direction /= np.linalg.norm(direction)

    pipeline.add_to_scene()
    try:
        vp = Viewport(type=Viewport.Type.Ortho, camera_dir=tuple(direction))
        # Point the orthographic camera through the local-cluster center.
        vp.camera_pos = tuple(center - direction * max(30.0, fov*6.0))
        vp.fov = float(fov)
        vp.render_image(
            filename=str(outpath),
            size=IMAGE_SIZE,
            background=(1.0,1.0,1.0),
            renderer=make_renderer(ao=ao)
        )
    finally:
        pipeline.remove_from_scene()

    try:
        from PIL import Image
        with Image.open(outpath) as im:
            im.save(outpath, dpi=(DPI,DPI))
    except Exception:
        pass

def make_contact(rows, outbase):
    from PIL import Image, ImageDraw, ImageFont

    def font(size,bold=False):
        choices=[
            Path(r"C:\Windows\Fonts\arialbd.ttf") if bold else Path(r"C:\Windows\Fonts\arial.ttf"),
            Path(r"C:\Windows\Fonts\arial.ttf")
        ]
        for p in choices:
            if p.exists():
                try:
                    return ImageFont.truetype(str(p),size=size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def fit(path,w,h):
        im=Image.open(path).convert("RGB")
        im.thumbnail((w,h),Image.Resampling.LANCZOS)
        c=Image.new("RGB",(w,h),"white")
        c.paste(im,((w-im.width)//2,(h-im.height)//2))
        return c

    chunks=[rows[i:i+4] for i in range(0,len(rows),4)]
    for page,chunk in enumerate(chunks,1):
        tile_w,tile_h=760,620
        margin,gap,label_h=45,30,50
        W=2*tile_w+gap+2*margin
        H=105+len(chunk)*(tile_h+label_h+gap)+margin
        canvas=Image.new("RGB",(W,H),"white")
        d=ImageDraw.Draw(canvas)
        d.text((margin,22),
               "Panel B — corrected local Zn/Cu inset screening",
               fill="black",font=font(34,True))
        y=95
        for label,pi,pii in chunk:
            d.text((margin,y),f"{label} — Zn",fill="black",font=font(22,True))
            d.text((margin+tile_w+gap,y),f"{label} — Cu",fill="black",font=font(22,True))
            y+=label_h
            canvas.paste(fit(pi,tile_w,tile_h),(margin,y))
            canvas.paste(fit(pii,tile_w,tile_h),(margin+tile_w+gap,y))
            d.rectangle((margin,y,margin+tile_w,y+tile_h),outline="black",width=2)
            d.rectangle((margin+tile_w+gap,y,margin+2*tile_w+gap,y+tile_h),outline="black",width=2)
            y+=tile_h+gap
        op=outbase.with_name(outbase.stem+f"__page_{page:02d}.png")
        canvas.save(op,dpi=(DPI,DPI))
        print("Contact:",op)

def main():
    paths = cif_paths("B")
    outdir = OUT_ROOT / "70_B_final_inset_tight"
    outdir.mkdir(parents=True, exist_ok=True)
    rows=[]

    for label,depth,view,ao in CASES:
        print("\nrender:",label)

        pi,base_i,start_i,keep_i = local_pipeline(paths["i"],"Zn",depth,ao=ao)
        pii,base_ii,start_ii,keep_ii = local_pipeline(paths["ii"],"Cu",depth,ao=ao)

        ci,ri,_ = cluster_geometry(pi)
        cii,rii,_ = cluster_geometry(pii)

        # Matched pair scale. 1.55 leaves breathing room around atom spheres/bonds.
        shared_fov = 2.0 * max(ri,rii) * 1.55 * 0.58

        di = direction_from_coeffs(base_i,VIEW_COEFFS_FULL[view])
        dii = direction_from_coeffs(base_ii,VIEW_COEFFS_FULL[view])

        out_i = outdir / f"{label}__B_i_Zn.png"
        out_ii = outdir / f"{label}__B_ii_Cu.png"

        render_local(pi,di,shared_fov,ci,out_i,ao=ao)
        render_local(pii,dii,shared_fov,cii,out_ii,ao=ao)

        print(f"  depth={depth} | Zn atoms={len(keep_i)} | Cu atoms={len(keep_ii)} | FOV={shared_fov:.3f}")
        rows.append((label,out_i,out_ii))

    make_contact(rows,outdir/"B_local_inset_fixed_contact")
    print("\nOutput:",outdir)

if __name__ == "__main__":
    main()
