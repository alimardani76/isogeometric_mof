"""Panel F chemistry/connectivity + functional-motif preflight."""

from collections import Counter
import numpy as np

from f_config import F_I,F_II,EXPECTED
from f_common import require_ovito,build_pipeline

def pair_name(a,b):
    return "-".join(sorted((a,b)))

def norm_component_list(items):
    return sorted((tuple(sorted(sig.items())),anchors) for sig,anchors in items)

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

    vcoord=[]
    for i,e in enumerate(els):
        if e=="V":
            vcoord.append(Counter(els[j] for j in adj[i]))

    # Cyano motif = C bonded to one N and one C, where C-N is the short bond class.
    # The graph has exactly two terminal N atoms (N degree 1) attached to cyano carbon atoms.
    cyano=[]
    for n,e in enumerate(els):
        if e!="N" or len(adj[n])!=1:
            continue
        c=adj[n][0]
        if els[c]!="C":
            continue
        carbon_neighbors=[j for j in adj[c] if els[j]=="C"]
        nitrogen_neighbors=[j for j in adj[c] if els[j]=="N"]
        if len(carbon_neighbors)==1 and n in nitrogen_neighbors:
            cyano.append((c,n,carbon_neighbors[0]))

    # Components after removing V. Keep only carbon-containing organic components.
    eligible={i for i,e in enumerate(els) if e!="V"}
    seen=set()
    organic=[]

    atom_to_component={}
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

        sig=dict(Counter(els[u] for u in comp))
        anchors=set()
        for u in comp:
            for v in adj[u]:
                if els[v]=="V":
                    anchors.add(v)

        if sig.get("C",0)>0:
            idx=len(organic)
            organic.append((sig,len(anchors),comp))
            for u in comp:
                atom_to_component[u]=idx

    cyano_component_signatures=[]
    for c,n,anchor_c in cyano:
        ci=atom_to_component[c]
        cyano_component_signatures.append(organic[ci][0])

    return (
        counts,len(top),Counter(els),vcoord,
        [(sig,anchors) for sig,anchors,comp in organic],
        cyano,cyano_component_signatures
    )

def main():
    require_ovito()
    print("="*92)
    print("PANEL F — CONNECTIVITY + FUNCTIONAL-MOTIF PREFLIGHT")
    print("="*92)

    all_ok=True

    for ep,path in (("i",F_I),("ii",F_II)):
        if not path.exists():
            raise SystemExit(f"Missing CIF:\n{path}")

        pipe,_=build_pipeline(path,hide_h=False)
        data=pipe.compute()
        counts,total,elements,vcoord,organic,cyano,cyano_sigs=audit(data)
        exp=EXPECTED[ep]

        print(f"\nEndpoint {ep}: {path.name}")
        print("  atoms       =",data.particles.count)
        print("  elements    =",dict(elements))
        print("  total bonds =",total)
        for k,v in sorted(counts.items()):
            print(f"    {k:6s} {v:3d}")

        print("  V coordination:")
        for c in vcoord:
            print("   ",dict(c))

        print("  V-connected organic components:")
        for sig,anchors in organic:
            print("   ",sig,"| V anchors =",anchors)

        print("  cyano motifs =",len(cyano))
        print("  cyano-bearing component signatures:")
        for sig in cyano_sigs:
            print("   ",sig)

        ok=True
        ok &= data.particles.count==exp["atoms"]
        ok &= dict(elements)==exp["elements"]
        ok &= total==exp["total_bonds"]
        for k,v in exp["bonds"].items():
            ok &= counts.get(k,0)==v
        ok &= len(vcoord)==4
        ok &= all(c.get("O",0)==6 for c in vcoord)
        ok &= counts.get("V-V",0)==0
        ok &= len(cyano)==exp["cyano_count"]
        ok &= norm_component_list(organic)==norm_component_list(exp["organic_components"])
        ok &= sorted(tuple(sorted(x.items())) for x in cyano_sigs) == \
              sorted(tuple(sorted(x.items())) for x in exp["cyano_component_signatures"])

        print("  STATUS:","PASS" if ok else "FAIL")
        all_ok &= ok

    print("\n"+"="*92)
    if all_ok:
        print("FINAL: PASS")
        print()
        print("Descriptive motif interpretation:")
        print("  F_i : both cyano motifs occur on the N-rich C17H7N5O4 linker family.")
        print("  F_ii: one cyano motif remains on C17H7N5O4, while the other occurs on")
        print("        a C19H7N1O4 linker environment.")
        print()
        print("Use this only as an EXPLORATORY cyano-motif placement difference.")
        print("Do not claim a class-wide law or adsorption mechanism.")
        print()
        print("Proceed to: python 02_F_render_whole_geometry_screen.py")
    else:
        print("FINAL: FAIL")
        print("Stop and send this terminal output back.")
    print("="*92)

if __name__=="__main__":
    main()
