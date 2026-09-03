"""Panel C connectivity and conservative local-shell preflight."""

from collections import Counter
import numpy as np

from c_config import C_I,C_II,EXPECTED
from c_common import require_ovito,build_pipeline

def pair_name(a,b):
    return "-".join(sorted((a,b)))

def audit(data,metal):
    prop=data.particles["Particle Type"]
    ids=np.asarray(prop)
    names={t.id:t.name for t in prop.types}
    els=[names[int(x)] for x in ids]
    pos=np.asarray(data.particles.positions,dtype=float)

    top=np.asarray(data.particles.bonds.topology,dtype=int)
    adj=[[] for _ in range(data.particles.count)]
    counts=Counter()

    for a,b in top:
        adj[a].append(b)
        adj[b].append(a)
        counts[pair_name(els[a],els[b])] += 1

    m_indices=[i for i,e in enumerate(els) if e==metal]
    o_indices=[i for i,e in enumerate(els) if e=="O"]

    # Minimum-image metal-to-oxygen distances from the original periodic cell.
    H4=np.asarray(data.cell,dtype=float)
    H=H4[:3,:3]
    invH=np.linalg.inv(H)
    origin=H4[:3,3] if H4.shape[1]>=4 else np.zeros(3)
    frac=(pos-origin)@invH.T

    shell_records=[]
    for m in m_indices:
        dfrac=frac[o_indices]-frac[m]
        dfrac-=np.round(dfrac)
        dcart=dfrac@H.T
        ds=np.linalg.norm(dcart,axis=1)
        s=np.sort(ds)
        shell_records.append((s[:4],s[4]))

    metal_graph_cn=[
        sum(1 for j in adj[m] if els[j]=="O")
        for m in m_indices
    ]

    return (
        counts,len(top),Counter(els),
        metal_graph_cn,shell_records
    )

def main():
    require_ovito()
    print("="*96)
    print("PANEL C — CONNECTIVITY / DISTANCE-DEFINED LOCAL-SHELL PREFLIGHT")
    print("="*96)
    print("IMPORTANT:")
    print("The M-O4 shell below is used only as a conservative rendering shell.")
    print("Panel C is method-sensitive in the project's neighbor-analysis audit.")
    print("Do not convert this rendering shell into a robust coordination claim.")
    print("="*96)

    all_ok=True

    for ep,path in (("i",C_I),("ii",C_II)):
        if not path.exists():
            raise SystemExit(f"Missing CIF:\n{path}")

        exp=EXPECTED[ep]
        metal=exp["metal"]

        pipe,_=build_pipeline(path,hide_h=False)
        data=pipe.compute()

        counts,total,elements,graph_cn,shells=audit(data,metal)

        first_all=np.concatenate([x[0] for x in shells])
        fifth=np.array([x[1] for x in shells])

        print(f"\nEndpoint {ep}: {path.name}")
        print("  atoms       =",data.particles.count)
        print("  elements    =",dict(elements))
        print("  total bonds =",total)
        for k,v in sorted(counts.items()):
            print(f"    {k:6s} {v:4d}")

        print(f"  {metal}-O graph neighbors per metal =",graph_cn)
        print(
            f"  four-nearest {metal}-O range = "
            f"{first_all.min():.3f} .. {first_all.max():.3f} A"
        )
        print(
            f"  fifth-nearest O range        = "
            f"{fifth.min():.3f} .. {fifth.max():.3f} A"
        )

        ok=True
        ok &= data.particles.count==exp["atoms"]
        ok &= dict(elements)==exp["elements"]
        ok &= total==exp["total_bonds"]
        for k,v in exp["bonds"].items():
            ok &= counts.get(k,0)==v
        ok &= counts.get("Cu-Cu",0)==0
        ok &= counts.get("Zn-Zn",0)==0
        ok &= all(x==4 for x in graph_cn)
        ok &= first_all.min()>=exp["first_shell_range"][0]
        ok &= first_all.max()<=exp["first_shell_range"][1]
        ok &= fifth.min()>=exp["next_shell_min"]

        print("  STATUS:","PASS" if ok else "FAIL")
        all_ok &= ok

    print("\n"+"="*96)
    if all_ok:
        print("FINAL: PASS")
        print("Proceed to: python 02_C_render_whole_geometry_screen.py")
        print()
        print("Interpretation boundary remains:")
        print("  boundary case / method-sensitive local comparison")
        print("NOT:")
        print("  robust coordination mechanism")
    else:
        print("FINAL: FAIL")
        print("Stop and send this terminal output back.")
    print("="*96)

if __name__=="__main__":
    main()
