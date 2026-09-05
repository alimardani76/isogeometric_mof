"""Panel F — final cyano-motif inset screening.

Scientific target:
    F_i  : cyano motif on N-rich C17H7N5O4 linker
    F_ii : distinctive cyano motif on C19H7N1O4 linker

A shared-environment control (C17H7N5O4 vs C17H7N5O4) is also rendered once.

The local motif is defined from the validated graph, not from hard-coded atom numbers.
"""

from pathlib import Path
from collections import Counter
import numpy as np

from f_config import F_I,F_II,OUT_ROOT,DPI,F_PAIRWISE_CUTOFFS
from f_common import build_pipeline,make_renderer
from ovito.io import import_file
from ovito.modifiers import CreateBondsModifier
from ovito.vis import Viewport,BondsVis

OUT = OUT_ROOT / "70_F_final_inset_tight"
FRAGDIR = OUT / "xyz_fragments"
IMAGE_SIZE = (3200,2400)

# Full organic-component signatures including H, used only for exact selection.
DISTINCTIVE_TARGET = {
    "i":  {"C":17,"H":7,"N":5,"O":4},
    "ii": {"C":19,"H":7,"N":1,"O":4},
}
SHARED_TARGET = {
    "i":  {"C":17,"H":7,"N":5,"O":4},
    "ii": {"C":17,"H":7,"N":5,"O":4},
}

CASES = [
    ("DIST_D3_face",      "distinctive", 3, "face"),
]

LOCAL_RADII = {
    "C":0.40,
    "N":0.47,
    "O":0.43,
}
LOCAL_COLORS = {
    "C":(0.29,0.29,0.29),
    "N":(0.12,0.34,0.80),
    "O":(0.84,0.20,0.20),
}
BOND_WIDTH = 0.16
BOND_COLOR = (0.42,0.42,0.42)

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

def find_organic_components(data):
    _,_,els=arrays(data)
    adj=graph_with_pbc(data)

    # Remove V to isolate organic linker components.
    eligible={i for i,e in enumerate(els) if e!="V"}
    seen=set()
    comps=[]
    atom_to_comp={}

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

        sig=dict(Counter(els[i] for i in comp))
        if sig.get("C",0) == 0:
            continue

        idx=len(comps)
        comps.append({"atoms":comp,"signature":sig})
        for i in comp:
            atom_to_comp[i]=idx

    return comps,atom_to_comp,adj,els

def find_cyano_motifs(data):
    comps,atom_to_comp,adj,els=find_organic_components(data)
    motifs=[]

    for n,e in enumerate(els):
        if e!="N":
            continue

        # terminal nitrile N has one graph neighbor
        heavy_neighbors=[v for v,_ in adj[n] if els[v]!="H"]
        if len(heavy_neighbors)!=1:
            continue

        c=heavy_neighbors[0]
        if els[c]!="C":
            continue

        c_heavy=[v for v,_ in adj[c] if els[v]!="H"]
        c_C=[v for v in c_heavy if els[v]=="C"]
        c_N=[v for v in c_heavy if els[v]=="N"]

        if len(c_C)==1 and n in c_N:
            comp_idx=atom_to_comp.get(c)
            if comp_idx is None:
                continue
            motifs.append({
                "cyano_N":n,
                "cyano_C":c,
                "attach_C":c_C[0],
                "component_index":comp_idx,
                "component_signature":comps[comp_idx]["signature"],
            })

    return motifs,comps,adj,els

def choose_motif(data,endpoint,mode):
    motifs,comps,adj,els=find_cyano_motifs(data)
    target=(DISTINCTIVE_TARGET if mode=="distinctive" else SHARED_TARGET)[endpoint]

    candidates=[m for m in motifs if m["component_signature"]==target]
    if not candidates:
        raise RuntimeError(
            f"No {endpoint}/{mode} cyano motif found on component {target}. "
            f"Available cyano signatures: {[m['component_signature'] for m in motifs]}"
        )

    # F_i has two equivalent N-rich cyano motifs; select deterministically.
    candidates.sort(key=lambda m:(m["cyano_N"],m["cyano_C"]))
    m=candidates[0]
    return m,comps,adj,els

def local_keep(data,endpoint,mode,depth):
    motif,comps,adj,els=choose_motif(data,endpoint,mode)
    comp=set(comps[motif["component_index"]]["atoms"])

    if depth is None:
        # Full linker, heavy atoms only.
        keep={i for i in comp if els[i]!="H"}
    else:
        # Always keep cyano group + attachment carbon.
        keep={motif["cyano_N"],motif["cyano_C"],motif["attach_C"]}
        frontier={motif["attach_C"]}

        for _ in range(depth):
            nxt=set()
            for u in frontier:
                for v,_ in adj[u]:
                    if v in comp and els[v] in {"C","N","O"} and v not in keep:
                        nxt.add(v)
            keep.update(nxt)
            frontier=nxt

    return motif,keep,adj,els

def unwrap_selected(data,keep,adj):
    pos=np.asarray(data.particles.positions,dtype=float)
    keep=set(keep)

    # Start at attachment carbon when possible for stable local geometry.
    root=next(iter(keep))
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
            f"Selected local graph is disconnected after PBC unwrap; "
            f"{len(missing)} atoms missing."
        )

    return uw

def write_xyz(path,data,endpoint,mode,depth):
    motif,keep,adj,els=local_keep(data,endpoint,mode,depth)
    uw=unwrap_selected(data,keep,adj)

    ordered=sorted(keep)
    coords=np.array([uw[i] for i in ordered],dtype=float)
    center=coords.mean(axis=0)

    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8") as f:
        f.write(f"{len(ordered)}\n")
        f.write(
            f"Panel F {endpoint} {mode} depth={depth} "
            f"component={motif['component_signature']}\n"
        )
        for i in ordered:
            x,y,z=uw[i]-center
            f.write(f"{els[i]} {x:.8f} {y:.8f} {z:.8f}\n")

    return {
        "component_signature":motif["component_signature"],
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
    for (a,b),cut in F_PAIRWISE_CUTOFFS.items():
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
    center=pos.mean(axis=0)

    X=pos-center
    vals,vecs=np.linalg.eigh(X.T@X/max(len(X)-1,1))
    order=np.argsort(vals)[::-1]
    major=vecs[:,order[0]]
    second=vecs[:,order[1]]
    normal=vecs[:,order[2]]

    if mode=="face":
        d=normal
    elif mode=="oblique":
        d=normal+0.36*second
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

    chunks=[rows[i:i+4] for i in range(0,len(rows),4)]
    for page,chunk in enumerate(chunks,1):
        tw,th=780,620
        margin,gap,lh=45,30,52
        W=2*tw+gap+2*margin
        H=110+len(chunk)*(th+lh+gap)+margin

        canvas=Image.new("RGB",(W,H),"white")
        dr=ImageDraw.Draw(canvas)
        dr.text(
            (margin,22),
            "Panel F — exploratory cyano-motif inset screen",
            fill="black",font=font(33,True)
        )

        y=100
        for label,pi,pii in chunk:
            dr.text((margin,y),f"{label} — F_i",fill="black",font=font(21,True))
            dr.text((margin+tw+gap,y),f"{label} — F_ii",fill="black",font=font(21,True))
            y+=lh
            canvas.paste(fit(pi,tw,th),(margin,y))
            canvas.paste(fit(pii,tw,th),(margin+tw+gap,y))
            dr.rectangle((margin,y,margin+tw,y+th),outline="black",width=2)
            dr.rectangle((margin+tw+gap,y,margin+2*tw+gap,y+th),outline="black",width=2)
            y+=th+gap

        op=cdir/f"F_cyano_inset_contact__page_{page:02d}.png"
        canvas.save(op,dpi=(DPI,DPI))
        print("Created:",op)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    FRAGDIR.mkdir(parents=True,exist_ok=True)

    # H retained here because full component signature is used for exact target selection.
    pi,_=build_pipeline(F_I,hide_h=False)
    pii,_=build_pipeline(F_II,hide_h=False)
    data_i=pi.compute()
    data_ii=pii.compute()

    rows=[]

    for label,target_mode,depth,viewmode in CASES:
        print("\nrender:",label)

        xyz_i=FRAGDIR/f"{label}__F_i.xyz"
        xyz_ii=FRAGDIR/f"{label}__F_ii.xyz"

        info_i=write_xyz(xyz_i,data_i,"i",target_mode,depth)
        info_ii=write_xyz(xyz_ii,data_ii,"ii",target_mode,depth)

        fi=fragment_pipeline(xyz_i)
        fii=fragment_pipeline(xyz_ii)

        cen_i,d_i,r_i=pca_camera(fi,viewmode)
        cen_ii,d_ii,r_ii=pca_camera(fii,viewmode)

        # Same physical scale for the paired inset.
        fov=2.0*max(r_i,r_ii)*1.42*0.55

        oi=OUT/f"{label}__F_i.png"
        oii=OUT/f"{label}__F_ii.png"

        render_local(fi,d_i,fov,cen_i,oi)
        render_local(fii,d_ii,fov,cen_ii,oii)

        print("  F_i :",info_i)
        print("  F_ii:",info_ii)
        print("  matched FOV =",f"{fov:.3f}")

        rows.append((label,oi,oii))

    make_contact(rows)
    print("\nOutput:",OUT)

if __name__=="__main__":
    main()
