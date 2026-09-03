"""Panel C — final cautious Zn/Cu boundary-case local inset screen.

This is a rendering-context comparison, NOT a robust coordination/mechanism claim.

Target site:
- corresponding first Zn/Cu site near fractional (0, ~0.54, 0)
- selected geometrically, not by hard-coded particle index

Three nested contexts:
CORE:
    M + 4 nearest graph-bonded O

CARBOXY:
    CORE
    + carboxylate C attached to each selected O
    + the companion O attached to each carboxylate C

LINKER1:
    CARBOXY
    + first carbon beyond each carboxylate carbon

Workflow:
- use validated rendering graph on original periodic CIF;
- identify corresponding local site;
- unwrap selected graph through PBC;
- export standalone non-periodic XYZ;
- rebuild only Euclidean local bonds;
- render matched-scale face-on / mild-oblique candidates.
"""

from pathlib import Path
import numpy as np

from c_config import (
    C_I,C_II,OUT_ROOT,DPI,C_PAIRWISE_CUTOFFS
)
from c_common import build_pipeline,make_renderer
from ovito.io import import_file
from ovito.modifiers import CreateBondsModifier
from ovito.vis import Viewport,BondsVis

OUT = OUT_ROOT / "70_C_final_inset_tight"
FRAGDIR = OUT / "xyz_fragments"
IMAGE_SIZE = (3200,2400)

CASES = [
    ("CARBOXY_face",   "carboxy",  "face"),
]

LOCAL_RADII = {
    "C":0.40,
    "O":0.46,
    "Zn":0.72,
    "Cu":0.72,
}
LOCAL_COLORS = {
    "C": (0.29,0.29,0.29),
    "O": (0.84,0.20,0.20),
    "Zn":(0.25,0.48,0.72),
    "Cu":(0.82,0.42,0.16),
}
BOND_WIDTH = 0.16
BOND_COLOR = (0.42,0.42,0.42)

TARGET_FRAC = np.array([0.0,0.545,0.0],dtype=float)

def arrays(data):
    prop=data.particles["Particle Type"]
    ids=np.asarray(prop)
    names={t.id:t.name for t in prop.types}
    els=[names[int(x)] for x in ids]
    return ids,names,els

def graph_with_pbc(data):
    top=np.asarray(data.particles.bonds.topology,dtype=int)
    pbc=np.asarray(data.particles.bonds.pbc_vectors,dtype=int)
    H=np.asarray(data.cell)[:3,:3]

    adj=[[] for _ in range(data.particles.count)]
    for (a,b),s in zip(top,pbc):
        shift=H@np.asarray(s,dtype=float)
        adj[a].append((b,shift))
        adj[b].append((a,-shift))
    return adj

def fractional_positions(data):
    H4=np.asarray(data.cell,dtype=float)
    H=H4[:3,:3]
    origin=H4[:3,3] if H4.shape[1]>=4 else np.zeros(3)
    invH=np.linalg.inv(H)
    pos=np.asarray(data.particles.positions,dtype=float)
    frac=(pos-origin)@invH.T
    return frac,H

def choose_corresponding_metal(data):
    _,_,els=arrays(data)
    frac,H=fractional_positions(data)

    metals=[i for i,e in enumerate(els) if e in {"Zn","Cu"}]
    if not metals:
        raise RuntimeError("No Zn/Cu metal atoms found.")

    def score(i):
        df=frac[i]-TARGET_FRAC
        df-=np.round(df)
        # physical-distance score in the real cell
        return float(np.linalg.norm(H@df))

    metals.sort(key=score)
    return metals[0]

def select_context(data,level):
    _,_,els=arrays(data)
    adj=graph_with_pbc(data)

    m=choose_corresponding_metal(data)
    metal=els[m]

    O_neighbors=[v for v,_ in adj[m] if els[v]=="O"]
    if len(O_neighbors)!=4:
        raise RuntimeError(
            f"Expected 4 distance-defined O neighbors for selected {metal}; "
            f"found {len(O_neighbors)}."
        )

    keep={m,*O_neighbors}

    if level in {"carboxy","linker1"}:
        carboxy_C=[]
        companion_O=[]

        for o in O_neighbors:
            Cs=[v for v,_ in adj[o] if els[v]=="C"]
            if len(Cs)!=1:
                raise RuntimeError(
                    f"Expected one carboxylate C attached to selected O; found {len(Cs)}."
                )
            c=Cs[0]
            carboxy_C.append(c)
            keep.add(c)

            # Companion oxygen on the same carboxylate carbon.
            other_O=[v for v,_ in adj[c] if els[v]=="O" and v!=o]
            if len(other_O)!=1:
                raise RuntimeError(
                    f"Expected one companion O on carboxylate C; found {len(other_O)}."
                )
            companion_O.append(other_O[0])
            keep.add(other_O[0])

        if level=="linker1":
            for c in carboxy_C:
                beyond=[v for v,_ in adj[c] if els[v]=="C"]
                if len(beyond)!=1:
                    raise RuntimeError(
                        f"Expected one first carbon beyond carboxylate C; found {len(beyond)}."
                    )
                keep.add(beyond[0])

    return m,keep,adj,els

def unwrap_selected(data,root,keep,adj):
    pos=np.asarray(data.particles.positions,dtype=float)
    keep=set(keep)

    uw={root:pos[root].copy()}
    stack=[root]

    while stack:
        u=stack.pop()
        for v,shift in adj[u]:
            if v not in keep or v in uw:
                continue
            uw[v]=uw[u]+(pos[v]-pos[u]+shift)
            stack.append(v)

    if len(uw)!=len(keep):
        missing=keep-set(uw)
        raise RuntimeError(
            f"Selected local graph disconnected during unwrap; "
            f"{len(missing)} atoms missing."
        )
    return uw

def write_xyz(path,data,level):
    m,keep,adj,els=select_context(data,level)
    uw=unwrap_selected(data,m,keep,adj)

    ordered=sorted(keep)
    coords=np.array([uw[i] for i in ordered],dtype=float)
    center=coords.mean(axis=0)

    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8") as f:
        f.write(f"{len(ordered)}\n")
        f.write(
            f"Panel C boundary inset level={level}; "
            f"distance-defined local rendering context\n"
        )
        for i in ordered:
            x,y,z=uw[i]-center
            f.write(f"{els[i]} {x:.8f} {y:.8f} {z:.8f}\n")

    return {
        "metal":els[m],
        "level":level,
        "atoms_written":len(ordered),
    }

def fragment_pipeline(xyz):
    pipe=import_file(str(xyz))
    data0=pipe.compute()

    def style(frame,data):
        prop=data.particles_.particle_types_
        for t in prop.types_:
            if t.name in LOCAL_RADII:
                t.radius=float(LOCAL_RADII[t.name])
            if t.name in LOCAL_COLORS:
                t.color=tuple(LOCAL_COLORS[t.name])
    pipe.modifiers.append(style)

    bonds=CreateBondsModifier()
    bonds.mode=CreateBondsModifier.Mode.Pairwise
    if hasattr(bonds,"discard_existing_bonds"):
        bonds.discard_existing_bonds=True

    present={t.name for t in data0.particles["Particle Type"].types}
    for (a,b),cut in C_PAIRWISE_CUTOFFS.items():
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

    center=pos.mean(axis=0)

    # Orient using O/C context rather than the metal sphere alone.
    mask=np.array([e not in {"Zn","Cu"} for e in els],dtype=bool)
    pts=pos[mask] if mask.any() else pos

    X=pts-pts.mean(axis=0)
    vals,vecs=np.linalg.eigh(X.T@X/max(len(X)-1,1))
    order=np.argsort(vals)[::-1]
    major=vecs[:,order[0]]
    second=vecs[:,order[1]]
    normal=vecs[:,order[2]]

    if mode=="face":
        d=normal
    elif mode=="oblique":
        d=normal+0.38*second
    else:
        raise ValueError(mode)
    d=d/np.linalg.norm(d)

    radius=float(np.max(np.linalg.norm(pos-center,axis=1)))
    return center,d,max(radius,1.0)

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

    chunks=[rows[i:i+3] for i in range(0,len(rows),3)]
    for page,chunk in enumerate(chunks,1):
        tw,th=780,620
        margin,gap,lh=45,30,52
        W=2*tw+gap+2*margin
        H=110+len(chunk)*(th+lh+gap)+margin

        canvas=Image.new("RGB",(W,H),"white")
        dr=ImageDraw.Draw(canvas)
        dr.text(
            (margin,22),
            "Panel C — method-sensitive boundary-case local inset",
            fill="black",font=font(32,True)
        )

        y=100
        for label,pi,pii in chunk:
            dr.text((margin,y),f"{label} — C_i (Zn)",fill="black",font=font(21,True))
            dr.text((margin+tw+gap,y),f"{label} — C_ii (Cu)",fill="black",font=font(21,True))
            y+=lh

            canvas.paste(fit(pi,tw,th),(margin,y))
            canvas.paste(fit(pii,tw,th),(margin+tw+gap,y))

            dr.rectangle((margin,y,margin+tw,y+th),outline="black",width=2)
            dr.rectangle(
                (margin+tw+gap,y,margin+2*tw+gap,y+th),
                outline="black",width=2
            )
            y+=th+gap

        op=cdir/f"C_boundary_inset_contact__page_{page:02d}.png"
        canvas.save(op,dpi=(DPI,DPI))
        print("Created:",op)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    FRAGDIR.mkdir(parents=True,exist_ok=True)

    # Heavy-atom graph is sufficient and keeps the inset quiet.
    pi,_=build_pipeline(C_I,hide_h=True)
    pii,_=build_pipeline(C_II,hide_h=True)
    data_i=pi.compute()
    data_ii=pii.compute()

    rows=[]

    for label,level,viewmode in CASES:
        print("\nrender:",label)

        xyz_i=FRAGDIR/f"{label}__C_i_Zn.xyz"
        xyz_ii=FRAGDIR/f"{label}__C_ii_Cu.xyz"

        info_i=write_xyz(xyz_i,data_i,level)
        info_ii=write_xyz(xyz_ii,data_ii,level)

        fi=fragment_pipeline(xyz_i)
        fii=fragment_pipeline(xyz_ii)

        cen_i,d_i,r_i=pca_camera(fi,viewmode)
        cen_ii,d_ii,r_ii=pca_camera(fii,viewmode)

        # matched physical scale
        fov=2.0*max(r_i,r_ii)*1.48*0.65

        oi=OUT/f"{label}__C_i_Zn.png"
        oii=OUT/f"{label}__C_ii_Cu.png"

        render_local(fi,d_i,fov,cen_i,oi)
        render_local(fii,d_ii,fov,cen_ii,oii)

        print("  C_i :",info_i)
        print("  C_ii:",info_ii)
        print("  matched FOV =",f"{fov:.3f}")

        rows.append((label,oi,oii))

    make_contact(rows)
    print("\nOutput:",OUT)

if __name__=="__main__":
    main()
