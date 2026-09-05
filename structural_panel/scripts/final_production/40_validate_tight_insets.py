from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
import os, csv, math

def detect_root():
    env = os.environ.get("P7B_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if not p.exists():
            raise SystemExit(f"P7B_ROOT is set but does not exist: {p}")
        return p
    return Path(__file__).resolve().parents[2]


def foreground_bbox(path,threshold=248):
    im=Image.open(path).convert("RGB")
    arr=np.asarray(im)
    mask=(arr < threshold).any(axis=2)
    ys,xs=np.where(mask)
    if len(xs)==0:
        return None
    x0,x1=int(xs.min()),int(xs.max())
    y0,y1=int(ys.min()),int(ys.max())
    W,H=im.size
    return x0,y0,x1,y1,(x1-x0+1)/W,(y1-y0+1)/H

def make_contacts(images,outdir):
    outdir.mkdir(parents=True,exist_ok=True)
    tiles=[]
    for p in images:
        im=Image.open(p).convert("RGB")
        im.thumbnail((700,525))
        tile=Image.new("RGB",(740,600),"white")
        tile.paste(im,((740-im.width)//2,20))
        dr=ImageDraw.Draw(tile)
        dr.text((20,560),p.parent.name+" / "+p.name,fill="black")
        tiles.append(tile)

    per_page=6; cols=2; rows=3
    for page in range(math.ceil(len(tiles)/per_page)):
        batch=tiles[page*per_page:(page+1)*per_page]
        sheet=Image.new("RGB",(cols*740+40,rows*600+40),"white")
        for i,t in enumerate(batch):
            r=i//cols; c=i%cols
            sheet.paste(t,(20+c*740,20+r*600))
        op=outdir/f"tight_inset_contact__page_{page+1:02d}.png"
        sheet.save(op,dpi=(200,200))
        print("contact:",op)

def main():
    root=detect_root()
    folder=root/"OVITO_final_insets_tight"
    images=sorted([p for p in folder.rglob("*.png") if "contact" not in p.name.lower()])
    if len(images)!=12:
        print(f"WARNING: expected 12 PNGs, found {len(images)}")

    rows=[]
    for p in images:
        im=Image.open(p)
        W,H=im.size
        dpi=im.info.get("dpi",(0,0))
        box=foreground_bbox(p)
        if box is None:
            rows.append({"file":p.name,"panel":p.parent.name,"status":"FAIL_EMPTY"})
            continue
        x0,y0,x1,y1,occ_w,occ_h=box
        major=max(occ_w,occ_h)
        minor=min(occ_w,occ_h)
        edge=min(x0,y0,W-1-x1,H-1-y1)

        res_ok=(W,H)==(3200,2400)
        dpi_ok=(dpi[0]>=590 and dpi[1]>=590)
        framing_ok=(0.54 <= major <= 0.67)
        edge_ok=(edge >= 100)
        status="PASS" if all((res_ok,dpi_ok,framing_ok,edge_ok)) else "CHECK"

        rows.append({
            "panel":p.parent.name,
            "file":p.name,
            "width_px":W,
            "height_px":H,
            "dpi_x":round(float(dpi[0]),2),
            "dpi_y":round(float(dpi[1]),2),
            "occupancy_width_pct":round(100*occ_w,1),
            "occupancy_height_pct":round(100*occ_h,1),
            "major_occupancy_pct":round(100*major,1),
            "minor_occupancy_pct":round(100*minor,1),
            "min_edge_margin_px":edge,
            "status":status,
        })

    csvp=folder/"tight_inset_QA.csv"
    with csvp.open("w",newline="",encoding="utf-8-sig") as f:
        fields=["panel","file","width_px","height_px","dpi_x","dpi_y","occupancy_width_pct","occupancy_height_pct","major_occupancy_pct","minor_occupancy_pct","min_edge_margin_px","status"]
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader(); w.writerows(rows)

    md=["# Tight Inset Automatic QA","","Target: 3200×2400, ~600 dpi, major object dimension ~54–67%, no edge clipping.",""]
    md.append("| Panel | File | Occupancy W | Occupancy H | Major | Edge margin | Status |")
    md.append("|---|---|---:|---:|---:|---:|---|")
    for r in rows:
        md.append(f"| {r['panel']} | `{r['file']}` | {r['occupancy_width_pct']}% | {r['occupancy_height_pct']}% | {r['major_occupancy_pct']}% | {r['min_edge_margin_px']} px | **{r['status']}** |")
    (folder/"tight_inset_QA.md").write_text("\n".join(md)+"\n",encoding="utf-8")

    make_contacts(images,folder/"contact_sheets")
    print("QA CSV:",csvp)
    print("QA MD :",folder/"tight_inset_QA.md")

if __name__=="__main__":
    main()
