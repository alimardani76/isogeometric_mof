"""Panel A final chemistry/connectivity preflight including Zn-N."""

from collections import Counter
import numpy as np

from a_config import A_I, A_II, A_PAIRWISE_CUTOFFS
from a_common import require_ovito, build_pipeline

EXPECTED = {
    "i": {
        "total":65,
        "pairs":{"C-C":27,"C-H":13,"C-N":3,"C-O":8,"H-N":2,"N-O":2,"N-Zn":2,"O-Zn":8},
        "components":[
            ({"C":18,"O":4},2),
            ({"C":6,"N":1,"O":6},2),
            ({"C":2,"N":2},2),
        ],
    },
    "ii": {
        "total":49,
        "pairs":{"C-C":13,"C-H":2,"C-N":6,"C-O":8,"H-N":2,"N-O":8,"N-Zn":2,"O-Zn":8},
        "components":[
            ({"C":8,"O":4},2),
            ({"C":6,"N":4,"O":12},2),
            ({"C":2,"N":2},2),
        ],
    },
}

def pair_name(a,b):
    return "-".join(sorted((a,b)))

def info(data):
    prop=data.particles["Particle Type"]
    ids=np.asarray(prop)
    names={t.id:t.name for t in prop.types}
    els=[names[int(x)] for x in ids]

    topology=np.asarray(data.particles.bonds.topology,dtype=int)
    adj=[[] for _ in range(data.particles.count)]
    counts=Counter()
    for a,b in topology:
        adj[a].append(b); adj[b].append(a)
        counts[pair_name(els[a],els[b])] += 1

    zn_coord=[]
    for i,e in enumerate(els):
        if e=="Zn":
            zn_coord.append(Counter(els[j] for j in adj[i]))

    # Organic components after removing Zn.
    eligible={i for i,e in enumerate(els) if e!="Zn"}
    seen=set()
    comps=[]
    for start in eligible:
        if start in seen: continue
        stack=[start]; seen.add(start); comp=[]
        while stack:
            u=stack.pop(); comp.append(u)
            for v in adj[u]:
                if v in eligible and v not in seen:
                    seen.add(v); stack.append(v)

        anchors=set()
        for u in comp:
            for v in adj[u]:
                if els[v]=="Zn":
                    anchors.add(v)

        if anchors:
            heavy=Counter(els[u] for u in comp if els[u]!="H")
            comps.append((dict(heavy),len(anchors)))

    comps.sort(key=lambda x:(-x[0].get("C",0),-x[0].get("N",0),-x[0].get("O",0)))
    return counts,len(topology),zn_coord,comps

def norm_comp_list(x):
    return sorted([(tuple(sorted(d.items())),a) for d,a in x])

def main():
    require_ovito()
    print("="*88)
    print("PANEL A — FINAL CONNECTIVITY PREFLIGHT")
    print("="*88)
    print("Pairwise cutoffs:")
    for p,c in A_PAIRWISE_CUTOFFS.items():
        print(f"  {p[0]}-{p[1]} <= {c:.2f} A")
    print("  all unspecified pairs OFF")
    print()

    all_ok=True
    for ep,path in (("i",A_I),("ii",A_II)):
        pipe,_=build_pipeline(path,hide_h=False)
        data=pipe.compute()
        counts,total,zn_coord,comps=info(data)
        exp=EXPECTED[ep]

        print(f"Endpoint {ep}: {path.name}")
        print("  total bonds =",total)
        for k,v in sorted(counts.items()):
            print(f"    {k:6s} {v:3d}")
        print("  Zn coordination:")
        for c in zn_coord:
            print("   ",dict(c))
        print("  Zn-coordinated organic components:")
        for comp,anchors in comps:
            print("   ",comp,"| Zn anchors =",anchors)

        ok=True
        ok &= total==exp["total"]
        for k,v in exp["pairs"].items():
            ok &= counts.get(k,0)==v
        ok &= len(zn_coord)==2
        ok &= all(c.get("O",0)==4 and c.get("N",0)==1 for c in zn_coord)
        ok &= counts.get("Zn-Zn",0)==0
        ok &= norm_comp_list(comps)==norm_comp_list(exp["components"])

        print("  STATUS:", "PASS" if ok else "FAIL")
        print()
        all_ok &= ok

    print("="*88)
    if all_ok:
        print("FINAL: PASS")
        print("The A pcu graph now has the intended O4N1 Zn connectivity.")
        print("Proceed to corrected whole + inset rendering.")
    else:
        print("FINAL: FAIL")
        print("Stop and send this output back.")
    print("="*88)

if __name__=="__main__":
    main()
