"""Panel D chemistry/connectivity preflight.

This script deliberately validates chemistry BEFORE any serious rendering.
"""

from collections import Counter, defaultdict
import numpy as np

from d_config import D_I,D_II,EXPECTED,D_PAIRWISE_CUTOFFS
from d_common import require_ovito, build_pipeline

def pair_name(a,b):
    # Keep metal pair readable as Cu-O, otherwise alphabetical.
    if set((a,b)) == set(("Cu","O")):
        return "Cu-O"
    return "-".join(sorted((a,b)))

def graph_info(data):
    prop=data.particles["Particle Type"]
    type_ids=np.asarray(prop)
    names={t.id:t.name for t in prop.types}
    els=[names[int(t)] for t in type_ids]

    topology=np.asarray(data.particles.bonds.topology,dtype=int)
    adj=[[] for _ in range(data.particles.count)]
    counts=Counter()
    for a,b in topology:
        adj[a].append(b); adj[b].append(a)
        counts[pair_name(els[a],els[b])] += 1

    # Detect local substituent motifs using graph chemistry.
    ethyl=[]
    methyl_on_CH=[]
    for i,e in enumerate(els):
        if e!="C":
            continue
        neigh=[els[j] for j in adj[i]]
        # terminal CH3 attached to one carbon
        if neigh.count("H")==3 and neigh.count("C")==1 and len(neigh)==4:
            cnb=[j for j in adj[i] if els[j]=="C"][0]
            n2=[els[j] for j in adj[cnb]]
            # CH3-CH2-backbone = ethyl
            if n2.count("H")==2 and n2.count("C")==2 and len(n2)==4:
                ethyl.append((i,cnb))
            # CH3 directly attached to CH backbone
            elif n2.count("H")==1 and n2.count("C")==3 and len(n2)==4:
                methyl_on_CH.append((i,cnb))

    element_counts=Counter(els)
    return counts,len(topology),element_counts,ethyl,methyl_on_CH

def main():
    require_ovito()
    print("="*82)
    print("PANEL D — CHEMISTRY / CONNECTIVITY PREFLIGHT")
    print("="*82)
    print("Pairwise cutoffs:")
    for pair,cut in D_PAIRWISE_CUTOFFS.items():
        print(f"  {pair[0]}-{pair[1]} <= {cut:.2f} A")
    print("  all unspecified pairs OFF")
    print()

    all_ok=True
    for endpoint,path in (("i",D_I),("ii",D_II)):
        if not path.exists():
            raise SystemExit(f"Missing CIF:\n{path}")

        pipe,_=build_pipeline(path,hide_h=False)
        data=pipe.compute()
        counts,total,elements,ethyl,methyl=graph_info(data)
        exp=EXPECTED[endpoint]

        print(f"Endpoint {endpoint}: {path.name}")
        print(f"  atoms       = {data.particles.count}")
        print(f"  elements    = {dict(elements)}")
        print(f"  total bonds = {total}")
        for pair,count in sorted(counts.items()):
            print(f"    {pair:6s} {count:4d}")
        print(f"  ethyl motifs       = {len(ethyl)}")
        print(f"  methyl-on-CH motifs= {len(methyl)}")

        ok=True
        ok &= data.particles.count == exp["atoms"]
        ok &= dict(elements) == exp["elements"]
        ok &= total == exp["total_bonds"]
        for pair,n in exp["bonds"].items():
            ok &= counts.get(pair,0) == n
        ok &= len(ethyl) == exp["ethyl"]
        ok &= len(methyl) == exp["methyl_on_CH"]
        ok &= counts.get("Cu-Cu",0) == 0

        print("  STATUS:", "PASS" if ok else "FAIL")
        print()
        all_ok &= ok

    print("="*82)
    if all_ok:
        print("FINAL: PASS")
        print("Chemistry interpretation:")
        print("  D_i  contains 4 x ethyl branches  (-CH2-CH3)")
        print("  D_ii contains 4 x methyl branches (-CH3)")
        print("  normalized difference = +CH2 in D_i")
        print("Proceed to: python 02_D_render_geometry_111.py")
    else:
        print("FINAL: FAIL")
        print("Do not render yet. Send this terminal output back.")
    print("="*82)

if __name__=="__main__":
    main()
