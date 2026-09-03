"""Panel A — final robust local-linker inset screen.

This script avoids the PBC bond-visualization artifacts of the previous round.

Workflow:
1. Use the final A pairwise connectivity on the ORIGINAL 1x1x1 CIF.
2. Identify the exact target linker by its heavy-atom signature.
3. Unwrap the linker graph through periodic boundaries using bond PBC vectors.
4. Optionally include the two coordinating Zn anchors.
5. Write a standalone non-periodic XYZ fragment.
6. Re-import it into OVITO and regenerate local bonds with zero PBC.
7. Render face-on and mild-oblique candidates at matched scale.

Target linker families:
N-family:
    A_i  = C6 N1 O6
    A_ii = C6 N4 O12
C-family:
    A_i  = C18 O4
    A_ii = C8 O4
"""

from pathlib import Path
from collections import Counter
import numpy as np

from a_config import A_I, A_II, OUT_ROOT, DPI, A_PAIRWISE_CUTOFFS
from a_common import build_pipeline, make_renderer
from ovito.io import import_file
from ovito.modifiers import CreateBondsModifier
from ovito.vis import Viewport, BondsVis

OUT = OUT_ROOT / "70_A_final_inset_tight"
FRAGDIR = OUT / "xyz_fragments"
IMAGE_SIZE = (3200,2400)

TARGETS = {
    ("i","nitro"):  {"C":6,"N":1,"O":6},
    ("ii","nitro"): {"C":6,"N":4,"O":12},
    ("i","carbon"): {"C":18,"O":4},
    ("ii","carbon"):{"C":8,"O":4},
}

CASES = [
    ("NITRO_plusZn_face",   "nitro",  True,  "face"),
]

LOCAL_RADII = {
    "C":0.40,
    "N":0.45,
    "O":0.44,
    "Zn":0.70,
}
LOCAL_COLORS = {
    "C": (0.29,0.29,0.29),
    "N": (0.12,0.34,0.78),
    "O": (0.84,0.20,0.20),
    "Zn":(0.24,0.55,0.66),
}
BOND_WIDTH = 0.15
BOND_COLOR = (0.43,0.43,0.43)

def arrays(data):
    prop = data.particles["Particle Type"]
    ids = np.asarray(prop)
    names = {t.id:t.name for t in prop.types}
    els = [names[int(x)] for x in ids]
    return ids,names,els

def graph_with_pbc(data):
    top = np.asarray(data.particles.bonds.topology,dtype=int)
    pbc = np.asarray(data.particles.bonds.pbc_vectors,dtype=int)
    H = np.asarray(data.cell)[:3,:3]

    adj=[[] for _ in range(data.particles.count)]
    for (a,b),s in zip(top,pbc):
        shift = H @ np.asarray(s,dtype=float)
        adj[a].append((b,shift))
        adj[b].append((a,-shift))
    return adj

def component_signature(comp,els):
    return dict(Counter(els[i] for i in comp if els[i]!="H"))

def find_target_component(data,endpoint,family):
    _,_,els = arrays(data)
    adj = graph_with_pbc(data)

    eligible={i for i,e in enumerate(els) if e!="Zn"}
    seen=set()
    candidates=[]

    for start in eligible:
        if start in seen:
            continue
        stack=[start]
        seen.add(start)
        comp=[]
        while stack:
            u=stack.pop()
            comp.append(u)
            for v,_ in adj[u]:
                if v in eligible and v not in seen:
                    seen.add(v)
                    stack.append(v)

        sig=component_signature(comp,els)
        if sig == TARGETS[(endpoint,family)]:
            anchors=set()
            for u in comp:
                for v,_ in adj[u]:
                    if els[v]=="Zn":
                        anchors.add(v)
            candidates.append((comp,sorted(anchors),adj,els))

    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected exactly one {endpoint}/{family} component with "
            f"signature {TARGETS[(endpoint,family)]}, found {len(candidates)}."
        )
    return candidates[0]

def unwrap_indices(data, indices, adj):
    pos=np.asarray(data.particles.positions,dtype=float)
    indices=set(indices)
    root=next(iter(indices))

    uw={root:pos[root].copy()}
    stack=[root]
    while stack:
        u=stack.pop()
        for v,shift in adj[u]:
            if v not in indices or v in uw:
                continue
            uw[v] = uw[u] + (pos[v]-pos[u] + shift)
            stack.append(v)

    if len(uw) != len(indices):
        missing=indices-set(uw)
        raise RuntimeError(f"Unwrap graph disconnected: {len(missing)} missing atoms.")
    return uw

def add_anchor_coordinates(data, comp, anchors, adj, uw):
    pos=np.asarray(data.particles.positions,dtype=float)
    comp_set=set(comp)
    for z in anchors:
        found=False
        for u in comp:
            for v,shift in adj[u]:
                if v == z:
                    uw[z] = uw[u] + (pos[z]-pos[u] + shift)
                    found=True
                    break
            if found:
                break
        if not found:
            raise RuntimeError("Could not unwrap Zn anchor from linker.")
    return uw

def write_fragment_xyz(path,data,endpoint,family,include_zn):
    comp,anchors,adj,els = find_target_component(data,endpoint,family)

    keep=set(comp)
    uw=unwrap_indices(data,keep,adj)
    if include_zn:
        keep.update(anchors)
        uw=add_anchor_coordinates(data,comp,anchors,adj,uw)

    # Recenter fragment near the origin for numerical cleanliness.
    coords=np.array([uw[i] for i in keep],dtype=float)
    center=coords.mean(axis=0)

    ordered=sorted(keep)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8") as f:
        f.write(f"{len(ordered)}\n")
        f.write(f"Panel A {endpoint} {family} includeZn={include_zn}\n")
        for i in ordered:
            x,y,z = uw[i]-center
            f.write(f"{els[i]} {x:.8f} {y:.8f} {z:.8f}\n")

    return {
        "signature":component_signature(comp,els),
        "anchors":len(anchors),
        "natoms":len(ordered),
    }

def fragment_pipeline(xyz):
    pipe=import_file(str(xyz))
    data0=pipe.compute()

    def style_types(frame,data):
        prop=data.particles_.particle_types_
        for t in prop.types_:
            if t.name in LOCAL_RADII:
                t.radius=float(LOCAL_RADII[t.name])
            if t.name in LOCAL_COLORS:
                t.color=tuple(LOCAL_COLORS[t.name])
    pipe.modifiers.append(style_types)

    bonds=CreateBondsModifier()
    bonds.mode=CreateBondsModifier.Mode.Pairwise
    if hasattr(bonds,"discard_existing_bonds"):
        bonds.discard_existing_bonds=True

    present={t.name for t in data0.particles["Particle Type"].types}
    for (a,b),cut in A_PAIRWISE_CUTOFFS.items():
        if a in present and b in present:
            bonds.set_pairwise_cutoff(a,b,float(cut))

    bonds.vis.width=float(BOND_WIDTH)
    try:
        bonds.vis.coloring_mode=BondsVis.ColoringMode.Uniform
    except Exception:
        pass
    bonds.vis.color=tuple(BOND_COLOR)
    pipe.modifiers.append(bonds)

    if pipe.source.data.cell is not None:
        pipe.source.data.cell.vis.render_cell=False

    return pipe

def pca_camera(pipe,mode):
    data=pipe.compute()
    pos=np.asarray(data.particles.positions,dtype=float)
    _,_,els=arrays(data)

    mask=np.array([e!="Zn" for e in els],dtype=bool)
    pts=pos[mask] if mask.any() else pos
    center=pos.mean(axis=0)

    X=pts-pts.mean(axis=0)
    vals,vecs=np.linalg.eigh(X.T@X/max(len(X)-1,1))
    order=np.argsort(vals)[::-1]
    major=vecs[:,order[0]]
    second=vecs[:,order[1]]
    normal=vecs[:,order[2]]

    if mode=="face":
        d=normal
    elif mode=="oblique":
        d=normal + 0.38*second
    else:
        raise ValueError(mode)
    d=d/np.linalg.norm(d)

    # Projected extent is more useful than 3D radius for orthographic fitting.
    # Build an in-plane basis.
    e1=major/np.linalg.norm(major)
    e2=np.cross(d,e1)
    if np.linalg.norm(e2) < 1e-8:
        e2=second/np.linalg.norm(second)
    else:
        e2=e2/np.linalg.norm(e2)

    rel=pos-center
    ext1=np.ptp(rel@e1) if len(pos)>1 else 1.0
    ext2=np.ptp(rel@e2) if len(pos)>1 else 1.0
    # OVITO ortho fov is vertical field; use conservative physical size.
    fov=max(ext1,ext2,1.0)*1.38
    return center,d,fov

def render_local(pipe,direction,fov,center,outpath):
    outpath=Path(outpath)
    outpath.parent.mkdir(parents=True,exist_ok=True)

    direction=np.asarray(direction,dtype=float)
    direction/=np.linalg.norm(direction)

    pipe.add_to_scene()
    try:
        vp=Viewport(type=Viewport.Type.Ortho,camera_dir=tuple(direction))
        vp.camera_pos=tuple(center-direction*max(30.0,fov*6.0))
        vp.fov=float(fov)
        vp.render_image(
            filename=str(outpath),
            size=IMAGE_SIZE,
            background=(1,1,1),
            renderer=make_renderer()
        )
    finally:
        pipe.remove_from_scene()

    try:
        from PIL import Image
        with Image.open(outpath) as im:
            im.save(outpath,dpi=(DPI,DPI))
    except Exception:
        pass

def make_contact(rows):
    from PIL import Image,ImageDraw,ImageFont
    cdir=OUT/"contact_sheets"
    cdir.mkdir(parents=True,exist_ok=True)

    def font(size,bold=False):
        choices=[
            Path(r"C:\Windows\Fonts\arialbd.ttf") if bold else Path(r"C:\Windows\Fonts\arial.ttf"),
            Path(r"C:\Windows\Fonts\arial.ttf")
        ]
        for p in choices:
            if p.exists():
                try:return ImageFont.truetype(str(p),size=size)
                except Exception:pass
        return ImageFont.load_default()

    def fit(path,w,h):
        im=Image.open(path).convert("RGB")
        im.thumbnail((w,h),Image.Resampling.LANCZOS)
        c=Image.new("RGB",(w,h),"white")
        c.paste(im,((w-im.width)//2,(h-im.height)//2))
        return c

    chunks=[rows[i:i+4] for i in range(0,len(rows),4)]
    for page,chunk in enumerate(chunks,1):
        tw,th=780,620
        margin,gap,lh=45,30,52
        W=2*tw+gap+2*margin
        H=110+len(chunk)*(th+lh+gap)+margin
        canvas=Image.new("RGB",(W,H),"white")
        dr=ImageDraw.Draw(canvas)
        dr.text((margin,22),"Panel A — FINAL standalone linker inset screen",
                fill="black",font=font(33,True))
        y=100
        for label,pi,pii in chunk:
            dr.text((margin,y),f"{label} — A_i",fill="black",font=font(21,True))
            dr.text((margin+tw+gap,y),f"{label} — A_ii",fill="black",font=font(21,True))
            y+=lh
            canvas.paste(fit(pi,tw,th),(margin,y))
            canvas.paste(fit(pii,tw,th),(margin+tw+gap,y))
            dr.rectangle((margin,y,margin+tw,y+th),outline="black",width=2)
            dr.rectangle((margin+tw+gap,y,margin+2*tw+gap,y+th),outline="black",width=2)
            y+=th+gap
        op=cdir/f"A_final_linker_inset_contact__page_{page:02d}.png"
        canvas.save(op,dpi=(DPI,DPI))
        print("Created:",op)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    FRAGDIR.mkdir(parents=True,exist_ok=True)

    # Final corrected CIF data with heavy atoms only.
    pi,_=build_pipeline(A_I,hide_h=True)
    pii,_=build_pipeline(A_II,hide_h=True)
    data_i=pi.compute()
    data_ii=pii.compute()

    rows=[]
    for label,family,include_zn,mode in CASES:
        print("\nrender:",label)

        xyz_i=FRAGDIR/f"{label}__A_i.xyz"
        xyz_ii=FRAGDIR/f"{label}__A_ii.xyz"

        info_i=write_fragment_xyz(xyz_i,data_i,"i",family,include_zn)
        info_ii=write_fragment_xyz(xyz_ii,data_ii,"ii",family,include_zn)

        fi=fragment_pipeline(xyz_i)
        fii=fragment_pipeline(xyz_ii)

        cen_i,d_i,fov_i=pca_camera(fi,mode)
        cen_ii,d_ii,fov_ii=pca_camera(fii,mode)
        shared=max(fov_i,fov_ii)*0.50

        oi=OUT/f"{label}__A_i.png"
        oii=OUT/f"{label}__A_ii.png"
        render_local(fi,d_i,shared,cen_i,oi)
        render_local(fii,d_ii,shared,cen_ii,oii)

        print("  A_i :",info_i)
        print("  A_ii:",info_ii)
        print("  matched FOV =",f"{shared:.3f}")

        rows.append((label,oi,oii))

    make_contact(rows)
    print("\nOutput:",OUT)

if __name__=="__main__":
    main()
