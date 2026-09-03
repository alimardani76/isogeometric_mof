"""Verify the corrected Panel B pairwise bond topology before rendering."""

from collections import Counter
from p7b_ovito_config import cif_paths, B_PAIRWISE_CUTOFFS, B_EXPECTED_BOND_COUNTS
from p7b_ovito_common import build_pipeline
import numpy as np

def pair_counts(data):
    if data.particles is None or data.particles.bonds is None:
        return Counter(), 0

    ptype = data.particles["Particle Type"]
    ids = np.asarray(ptype)
    names = {t.id: t.name for t in ptype.types}
    topology = np.asarray(data.particles.bonds.topology)

    counts = Counter()
    for a,b in topology:
        x = names.get(int(ids[a]), str(int(ids[a])))
        y = names.get(int(ids[b]), str(int(ids[b])))
        counts["-".join(sorted((x,y)))] += 1
    return counts, len(topology)

def recipe():
    return dict(
        h_mode="show",
        h_radius=0.12,
        particle_scale=1.00,
        bond_width=0.13,
        bond_color=(0.58,0.58,0.58),
        bond_coloring="uniform",
        palette="base",
        show_cell=False,
        ao=False,
        bond_mode="pairwise",
        pair_cutoffs=B_PAIRWISE_CUTOFFS,
    )

def main():
    paths = cif_paths("B")
    all_ok = True

    print("="*78)
    print("PANEL B — PAIRWISE BOND TOPOLOGY VERIFICATION")
    print("="*78)
    print("Cutoffs:")
    for pair, cutoff in B_PAIRWISE_CUTOFFS.items():
        print(f"  {pair[0]}-{pair[1]} <= {cutoff:.2f} A")
    print("  all unspecified pairs: OFF")

    for endpoint in ("i","ii"):
        pipe,_ = build_pipeline(paths[endpoint], rep=(1,1,1), recipe=recipe())
        data = pipe.compute()
        counts,total = pair_counts(data)

        print(f"\nEndpoint {endpoint}: total bonds = {total}")
        for pair,count in sorted(counts.items()):
            print(f"  {pair:8s} {count:4d}")

        expected = B_EXPECTED_BOND_COUNTS[endpoint]
        endpoint_ok = (total == expected["TOTAL"])
        for pair, exp in expected.items():
            if pair == "TOTAL":
                continue
            got = counts.get(pair,0)
            endpoint_ok &= (got == exp)
            if got != exp:
                print(f"  !! mismatch {pair}: got {got}, expected {exp}")

        # Explicitly guard against visually misleading metal-metal bonds.
        mm = counts.get("Cu-Cu",0) + counts.get("Zn-Zn",0)
        if mm:
            endpoint_ok = False
            print(f"  !! ERROR: found {mm} metal-metal rendering bonds")

        print("  STATUS:", "PASS" if endpoint_ok else "FAIL")
        all_ok &= endpoint_ok

    print("\n" + "="*78)
    print("FINAL:", "PASS — corrected B topology is ready for shortlist rendering."
          if all_ok else
          "FAIL — do not render yet; send this terminal output back.")
    print("="*78)

if __name__ == "__main__":
    main()
