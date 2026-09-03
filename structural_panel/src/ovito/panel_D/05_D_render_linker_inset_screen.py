"""Panel D — ethyl vs methyl linker-inset screening.

Scientific target:
    D_i  : backbone-CH2-CH3 (ethyl)
    D_ii : backbone-CH3     (methyl)

The script detects these motifs from the validated bond graph, not by hard-coded atom indices.

Rendering strategy learned from Panel B:
- 3x3x3 periodic buffer
- choose a motif near the center of the replicated box
- retain a local heavy-atom neighborhood
- fit the orthographic camera to the retained cluster itself
"""

from pathlib import Path
import numpy as np

from d_config import D_I, D_II, OUT_ROOT, VIEW_COEFFS, DPI
from d_common import build_pipeline, direction_from_coeffs, make_renderer
from ovito.modifiers import ReplicateModifier, DeleteSelectedModifier
from ovito.vis import Viewport

OUT = OUT_ROOT / "70_D_final_inset_tight"
BUFFER_REP = (3,3,3)
IMAGE_SIZE = (3200,2400)

# Local inset style: larger linker atoms/bonds than the whole-view screen.
LOCAL_RADII = {
    "C": 0.42,
    "N": 0.40,
    "O": 0.42,
}
LOCAL_COLORS = {
    "C": (0.29,0.29,0.29),
    "N": (0.20,0.38,0.78),
    "O": (0.84,0.20,0.20),
}
LOCAL_BOND_WIDTH = 0.17
LOCAL_BOND_COLOR = (0.42,0.42,0.42)

CASES = [
    ("CTX2_ac_mixed",  2, "ac_mixed"),
]

def type_arrays(data):
    prop=data.particles["Particle Type"]
    ids=np.asarray(prop)
    names={t.id:t.name for t in prop.types}
    elements=[names[int(x)] for x in ids]
    return ids,names,elements

def graph(data):
    topology=np.asarray(data.particles.bonds.topology,dtype=int)
    adj=[[] for _ in range(data.particles.count)]
    for a,b in topology:
        adj[a].append(b)
        adj[b].append(a)
    return adj

def cell_center(data):
    H4=np.asarray(data.cell,dtype=float)
    H=H4[:3,:3]
    origin=H4[:3,3] if H4.shape[1] >= 4 else np.zeros(3)
    return origin + H@np.array([0.5,0.5,0.5])

def find_motifs(data, endpoint):
    """Return motif dicts with terminal, optional extra, and anchor indices."""
    _,_,els=type_arrays(data)
    adj=graph(data)
    motifs=[]

    for terminal,e in enumerate(els):
        if e!="C":
            continue
        neigh=adj[terminal]
        nels=[els[j] for j in neigh]

        # terminal CH3 attached to exactly one carbon
        if not (nels.count("H")==3 and nels.count("C")==1 and len(neigh)==4):
            continue
        carbon_nb=[j for j in neigh if els[j]=="C"][0]
        n2=adj[carbon_nb]
        e2=[els[j] for j in n2]

        if endpoint=="i":
            # ethyl: terminal CH3 - CH2 - backbone
            if e2.count("H")==2 and e2.count("C")==2 and len(n2)==4:
                other_c=[j for j in n2 if els[j]=="C" and j!=terminal]
                if len(other_c)==1:
                    motifs.append({
                        "terminal":terminal,
                        "extra":carbon_nb,
                        "anchor":other_c[0],
                    })
        else:
            # methyl directly attached to CH backbone
            if e2.count("H")==1 and e2.count("C")==3 and len(n2)==4:
                motifs.append({
                    "terminal":terminal,
                    "extra":None,
                    "anchor":carbon_nb,
                })
    return motifs

def choose_central_motif(data, endpoint):
    motifs=find_motifs(data,endpoint)
    if not motifs:
        raise RuntimeError(f"No expected D_{endpoint} substituent motif found.")

    pos=np.asarray(data.particles.positions,dtype=float)
    ctr=cell_center(data)
    motifs.sort(key=lambda m: float(np.dot(pos[m["anchor"]]-ctr,pos[m["anchor"]]-ctr)))
    return motifs[0],len(motifs)

def local_keep(data, endpoint, context_depth):
    _,_,els=type_arrays(data)
    adj=graph(data)
    motif,nmotifs=choose_central_motif(data,endpoint)

    # Always include the defining substituent and its anchor.
    keep={motif["terminal"],motif["anchor"]}
    if motif["extra"] is not None:
        keep.add(motif["extra"])

    # Expand only through heavy linker atoms (C/N/O), never H or Cu.
    frontier={motif["anchor"]}
    for _ in range(context_depth):
        nxt=set()
        for i in frontier:
            for j in adj[i]:
                if els[j] in {"C","N","O"} and j not in keep:
                    nxt.add(j)
        keep.update(nxt)
        frontier=nxt

    return motif,sorted(keep),nmotifs

def build_local(path,endpoint,context_depth):
    # Keep H for motif classification, then simply omit H from the retained set.
    pipe,base=build_pipeline(path,hide_h=False)
    pipe.modifiers.append(
        ReplicateModifier(num_x=3,num_y=3,num_z=3,adjust_box=True)
    )

    data=pipe.compute()
    motif,keep,nmotifs=local_keep(data,endpoint,context_depth)
    keep_set=set(keep)

    def select_nonlocal(frame,data):
        sel=np.ones(data.particles.count,dtype=np.int32)
        for i in keep_set:
            sel[i]=0
        data.particles_.create_property("Selection",data=sel)

    def style_local(frame,data):
        prop=data.particles_.particle_types_
        for t in prop.types_:
            if t.name in LOCAL_RADII:
                t.radius=float(LOCAL_RADII[t.name])
            if t.name in LOCAL_COLORS:
                t.color=tuple(LOCAL_COLORS[t.name])
        if data.particles_.bonds is not None:
            data.particles_.bonds.vis.width=LOCAL_BOND_WIDTH
            data.particles_.bonds.vis.color=LOCAL_BOND_COLOR

    pipe.modifiers.append(select_nonlocal)
    pipe.modifiers.append(DeleteSelectedModifier())
    pipe.modifiers.append(style_local)
    return pipe,base,motif,keep,nmotifs

def cluster_geometry(pipe):
    data=pipe.compute()
    pos=np.asarray(data.particles.positions,dtype=float)
    center=pos.mean(axis=0)
    radius=float(np.max(np.linalg.norm(pos-center,axis=1)))
    return center,max(radius,1.0),data

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
            background=(1.0,1.0,1.0),
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
        tw,th=760,620
        margin,gap,lh=45,30,50
        W=2*tw+gap+2*margin
        H=105+len(chunk)*(th+lh+gap)+margin
        canvas=Image.new("RGB",(W,H),"white")
        d=ImageDraw.Draw(canvas)
        d.text(
            (margin,22),
            "Panel D — ethyl vs methyl local linker inset screening",
            fill="black",font=font(33,True)
        )
        y=95
        for label,pi,pii in chunk:
            d.text((margin,y),f"{label} — D_i ethyl",fill="black",font=font(21,True))
            d.text((margin+tw+gap,y),f"{label} — D_ii methyl",fill="black",font=font(21,True))
            y+=lh
            canvas.paste(fit(pi,tw,th),(margin,y))
            canvas.paste(fit(pii,tw,th),(margin+tw+gap,y))
            d.rectangle((margin,y,margin+tw,y+th),outline="black",width=2)
            d.rectangle((margin+tw+gap,y,margin+2*tw+gap,y+th),outline="black",width=2)
            y+=th+gap

        op=cdir/f"D_linker_inset_contact__page_{page:02d}.png"
        canvas.save(op,dpi=(DPI,DPI))
        print("Created:",op)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]

    for label,depth,view in CASES:
        print("\nrender:",label)

        pi,base_i,motif_i,keep_i,nmi=build_local(D_I,"i",depth)
        pii,base_ii,motif_ii,keep_ii,nmii=build_local(D_II,"ii",depth)

        ci,ri,_=cluster_geometry(pi)
        cii,rii,_=cluster_geometry(pii)
        shared_fov=2.0*max(ri,rii)*1.55*0.49

        di=direction_from_coeffs(base_i,VIEW_COEFFS[view])
        dii=direction_from_coeffs(base_ii,VIEW_COEFFS[view])

        oi=OUT/f"{label}__D_i_ethyl.png"
        oii=OUT/f"{label}__D_ii_methyl.png"
        render_local(pi,di,shared_fov,ci,oi)
        render_local(pii,dii,shared_fov,cii,oii)

        print(f"  detected replicated motifs: D_i={nmi}, D_ii={nmii}")
        print(f"  kept heavy atoms: D_i={len(keep_i)}, D_ii={len(keep_ii)}")
        print(f"  pair FOV={shared_fov:.3f}")
        rows.append((label,oi,oii))

    make_contact(rows)
    print("\nOutput:",OUT)

if __name__=="__main__":
    main()
