"""Panel E final chemistry/connectivity preflight."""

from collections import Counter
import numpy as np

from e_config import E_I,E_II,EXPECTED,E_PAIRWISE_CUTOFFS
from e_common import require_ovito,build_pipeline

def pair_name(a,b):
    return "-".join(sorted((a,b)))

def audit(data):
    prop=data.particles["Particle Type"]
    ids=np.asarray(prop)
    names={t.id:t.name for t in prop.types}
    els=[names[int(x)] for x in ids]

    top=np.asarray(data.particles.bonds.topology,dtype=int)
    adj=[[] for _ in range(data.particles.count)]
    counts=Counter()

    for a,b in top:
        adj[a].append(b)
        adj[b].append(a)
        counts[pair_name(els[a],els[b])] += 1

    zncoord=[]
    for i,e in enumerate(els):
        if e=="Zn":
            zncoord.append(Counter(els[j] for j in adj[i]))

    # Organic components after removing Zn.
    eligible={i for i,e in enumerate(els) if e!="Zn"}
    seen=set()
    comps=[]
    for start in eligible:
        if start in seen:
            continue
        stack=[start]
        seen.add(start)
        comp=[]
        while stack:
            u=stack.pop()
            comp.append(u)
            for v in adj[u]:
                if v in eligible and v not in seen:
                    seen.add(v)
                    stack.append(v)

        anchors=set()
        for u in comp:
            for v in adj[u]:
                if els[v]=="Zn":
                    anchors.add(v)

        if anchors:
            comps.append((dict(Counter(els[u] for u in comp)),len(anchors)))

    return counts,len(top),Counter(els),zncoord,comps

def norm_components(x):
    return sorted((tuple(sorted(d.items())),a) for d,a in x)

def main():
    require_ovito()
    print("="*90)
    print("PANEL E — FINAL CHEMISTRY / CONNECTIVITY PREFLIGHT")
    print("="*90)
    print("Pairwise cutoffs:")
    for p,c in E_PAIRWISE_CUTOFFS.items():
        print(f"  {p[0]}-{p[1]} <= {c:.2f} A")
    print("  all unspecified pairs OFF")
    print()

    all_ok=True

    for ep,path in (("i",E_I),("ii",E_II)):
        if not path.exists():
            raise SystemExit(f"Missing CIF:\n{path}")

        pipe,_=build_pipeline(path,hide_h=False)
        data=pipe.compute()
        counts,total,elements,zncoord,comps=audit(data)
        exp=EXPECTED[ep]

        print(f"Endpoint {ep}: {path.name}")
        print("  atoms       =",data.particles.count)
        print("  elements    =",dict(elements))
        print("  total bonds =",total)
        for k,v in sorted(counts.items()):
            print(f"    {k:6s} {v:3d}")

        print("  Zn coordination:")
        for c in zncoord:
            print("   ",dict(c))

        print("  Zn-connected organic components:")
        for comp,anchors in comps:
            print("   ",comp,"| Zn anchors =",anchors)

        ok=True
        ok &= data.particles.count==exp["atoms"]
        ok &= dict(elements)==exp["elements"]
        ok &= total==exp["total_bonds"]
        for k,v in exp["bonds"].items():
            ok &= counts.get(k,0)==v
        ok &= len(zncoord)==2
        ok &= all(c.get("O",0)==4 and c.get("N",0)==1 for c in zncoord)
        ok &= counts.get("Zn-Zn",0)==0
        ok &= norm_components(comps)==norm_components(exp["components"])

        print("  STATUS:","PASS" if ok else "FAIL")
        print()
        all_ok &= ok

    print("="*90)
    if all_ok:
        print("FINAL: PASS")
        print("Both E endpoints have controlled O4N1 Zn connectivity.")
        print("Proceed to: python 02_E_render_basis_matched_geometry.py")
    else:
        print("FINAL: FAIL")
        print("Do not render/freeze E yet. Send this terminal output back.")
    print("="*90)

if __name__=="__main__":
    main()
