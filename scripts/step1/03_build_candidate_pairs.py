#!/usr/bin/env python3
"""Build full-cohort chemistry comparison pairs with six worker processes.

Scientific scope:
- Uses the full chemistry-supported ARC-MOF cohort.
- Holds topology, dimensionality, and the non-changing chemistry dimensions fixed.
- Applies the audited measured-geometry tiers.
- Does not use adsorption outcomes.
- Does not run CrystalNN. Metal pairs remain coordination-pending.
- Does not fill missing scientific values.

Engineering:
- Six worker processes.
- Context groups are processed independently.
- Pair rows are written to one temporary Parquet file per completed group.
- The parent process stores only aggregated counters, never one dictionary per tested pair.
- A manifest records every completed context group and supports restart.
"""
from __future__ import annotations

from collections import Counter
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from hashlib import sha1
from itertools import combinations
from pathlib import Path
import json
import os
import shutil

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
MASTER_FILE = ANALYSIS / "framework_master.parquet"
CHEMISTRY_FILE = ANALYSIS / "cif_chemistry.parquet"
WORK_DIR = ANALYSIS / "full_pair_rules_work"
OUTPUT_DIR = ANALYSIS / "full_pair_rules"
MANIFEST = WORK_DIR / "completed_groups.jsonl"
SUMMARY_FILE = ANALYSIS / "full_pair_rule_summary.csv"
GROUP_PROFILE_FILE = ANALYSIS / "full_pair_context_profile.csv"

N_JOBS = 6
MAX_PENDING = 12
SITE_RATIO_LIMIT = 1.05
NUMERICAL_TOLERANCE = 1e-12


GEOMETRY = ["Di", "Df", "Dif", "Density", "UC_volume", "AVAf", "POAVAf"]
TIERS = {
    "stringent": {"Di": .03, "Df": .03, "Dif": .03, "Density": .05,
                  "UC_volume": .05, "AVAf": .03, "POAVAf": .03},
    "moderate": {"Di": .05, "Df": .05, "Dif": .05, "Density": .10,
                 "UC_volume": .10, "AVAf": .05, "POAVAf": .05},
    "exploratory": {"Di": .10, "Df": .10, "Dif": .10, "Density": .15,
                    "UC_volume": .20, "AVAf": .10, "POAVAf": .10},
}


def rel_diff(a, b):
    denominator = (abs(a) + abs(b)) / 2.0
    return abs(a - b) / denominator if denominator > 0 else 0.0


def geometry_differences(a, b):
    return {
        "Di_diff": rel_diff(a["Di"], b["Di"]),
        "Df_diff": rel_diff(a["Df"], b["Df"]),
        "Dif_diff": rel_diff(a["Dif"], b["Dif"]),
        "Density_diff": rel_diff(a["Density"], b["Density"]),
        "UC_volume_diff": rel_diff(a["UC_volume"], b["UC_volume"]),
        "AVAf_diff": abs(a["AVAf"] - b["AVAf"]),
        "POAVAf_diff": abs(a["POAVAf"] - b["POAVAf"]),
    }


def passes(differences, tier):
    return all(
        differences[f"{name}_diff"]
        <= limit + NUMERICAL_TOLERANCE
        for name, limit in TIERS[tier].items()
    )


def best_tier(d):
    for tier in ("stringent", "moderate", "exploratory"):
        if passes(d, tier):
            return tier
    return "rejected"


def site_ratio(a, b):
    low = min(a, b)
    return max(a, b) / low if low > 0 else np.inf


def group_id(intervention, keys):
    raw = intervention + "|" + "|".join("<NA>" if pd.isna(x) else str(x) for x in keys)
    return sha1(raw.encode("utf-8")).hexdigest()[:20]


def base_pair(a, b, intervention, chemical_class):
    d = geometry_differences(a, b)
    lo, hi = sorted([a["mof_id"], b["mof_id"]])
    return {
        "id_a": a["mof_id"], "id_b": b["mof_id"],
        "pair_lo": lo, "pair_hi": hi,
        "intervention": intervention,
        "chemical_class": chemical_class,
        "geometry_tier": best_tier(d),
        "topology": a["topology"],
        "Dimensionality": a["Dimensionality"],
        "metals_a": a["metals"], "metals_b": b["metals"],
        "metal_site_count_a": a["metal_site_count"],
        "metal_site_count_b": b["metal_site_count"],
        "metal_site_count_ratio": site_ratio(a["metal_site_count"], b["metal_site_count"]),
        **d,
    }


def process_group(payload):
    intervention, gid, frame, linker_racs, output_path = payload
    counts = Counter()
    accepted = []
    rows = frame.to_dict("records")

    for a, b in combinations(rows, 2):
        if intervention == "metal_substitution":
            if a["metal_cluster"] == b["metal_cluster"]:
                continue
            if a["metals"] == b["metals"]:
                counts[("same_actual_metal", "not_applicable")] += 1; continue
            if not bool(a["single_metal"]) or not bool(b["single_metal"]):
                counts[("mixed_metal", "not_applicable")] += 1; continue
            if site_ratio(a["metal_site_count"], b["metal_site_count"]) > SITE_RATIO_LIMIT:
                counts[("metal_multiplicity_changed", "not_applicable")] += 1; continue
            result = base_pair(a, b, intervention, "composition_clean_coordination_pending")

        elif intervention == "linker_family_change":
            if a["linker_cluster"] == b["linker_cluster"]:
                continue
            if a["metals"] != b["metals"]:
                counts[("actual_metal_changed", "not_applicable")] += 1; continue
            if site_ratio(a["metal_site_count"], b["metal_site_count"]) > SITE_RATIO_LIMIT:
                counts[("metal_multiplicity_changed", "not_applicable")] += 1; continue
            result = base_pair(a, b, intervention, "composition_clean")
            result["linker_cluster_a"] = a["linker_cluster"]
            result["linker_cluster_b"] = b["linker_cluster"]

        else:
            if a["functional_cluster"] == b["functional_cluster"]:
                continue
            if a["metals"] != b["metals"]:
                counts[("actual_metal_changed", "not_applicable")] += 1; continue
            if site_ratio(a["metal_site_count"], b["metal_site_count"]) > SITE_RATIO_LIMIT:
                counts[("metal_multiplicity_changed", "not_applicable")] += 1; continue
            linker_a = np.asarray([a[c] for c in linker_racs], dtype=float)
            linker_b = np.asarray([b[c] for c in linker_racs], dtype=float)
            if not np.array_equal(linker_a, linker_b):
                counts[("linker_also_changed", "not_applicable")] += 1; continue
            result = base_pair(a, b, intervention, "composition_clean")
            result["functional_cluster_a"] = a["functional_cluster"]
            result["functional_cluster_b"] = b["functional_cluster"]

        tier = result["geometry_tier"]
        counts[(result["chemical_class"], tier)] += 1
        if tier != "rejected":
            accepted.append(result)

    if accepted:
        table = pa.Table.from_pandas(pd.DataFrame(accepted), preserve_index=False)
        pq.write_table(table, output_path, compression="snappy")

    return {
        "group_id": gid,
        "intervention": intervention,
        "group_size": len(frame),
        "pairs_checked": len(rows) * (len(rows) - 1) // 2,
        "accepted_rows": len(accepted),
        "counts": [[status, tier, count] for (status, tier), count in counts.items()],
        "output_file": str(output_path) if accepted else None,
    }


def load_completed():
    completed, aggregate = set(), Counter()
    if not MANIFEST.exists():
        return completed, aggregate
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        completed.add(item["group_id"])
        for status, tier, count in item["counts"]:
            aggregate[(item["intervention"], status, tier)] += count
    return completed, aggregate


def append_manifest(item):
    with MANIFEST.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item) + "\n")


def collect_one(pending, aggregate, progress):
    done, pending = wait(pending, return_when=FIRST_COMPLETED)
    for future in done:
        item = future.result()
        append_manifest(item)
        for status, tier, count in item["counts"]:
            aggregate[(item["intervention"], status, tier)] += count
        progress["groups"] += 1
        progress["pairs"] += item["pairs_checked"]
        progress["accepted"] += item["accepted_rows"]
        if progress["groups"] % 500 == 0:
            print(f"completed_groups={progress['groups']:,}; checked_pairs={progress['pairs']:,}; accepted={progress['accepted']:,}")
    return pending


def finalize_outputs():
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    for intervention in ("metal_substitution", "linker_family_change", "functional_motif_change"):
        source = WORK_DIR / intervention
        files = sorted(source.glob("*.parquet")) if source.exists() else []
        if not files:
            continue
        dataset = ds.dataset(files, format="parquet")
        table = dataset.to_table()
        pq.write_table(table, OUTPUT_DIR / f"{intervention}.parquet", compression="snappy")


def main():
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)

    WORK_DIR.mkdir(parents=True, exist_ok=True)

    for intervention in (
        "metal_substitution",
        "linker_family_change",
        "functional_motif_change",
    ):
        (WORK_DIR / intervention).mkdir(exist_ok=True)

    master = pd.read_parquet(MASTER_FILE)
    master = master.loc[master["chemistry_verification_eligible"]].copy()
    chemistry = pd.read_parquet(CHEMISTRY_FILE)
    frame = master.merge(
        chemistry[["mof_id", "parse_ok", "metals", "single_metal", "metal_site_count"]],
        on="mof_id", how="left", validate="one_to_one"
    )
    frame = frame.loc[frame["parse_ok"].fillna(False)].copy()

    linker_racs = [c for c in frame.columns if c.startswith(("f-lig-", "lc-", "D_lc-"))]
    if len(linker_racs) != 58:
        raise RuntimeError(f"Expected 58 variable linker RACs, found {len(linker_racs)}")

    specs = {
        "metal_substitution": ["topology", "Dimensionality", "linker_cluster", "functional_cluster"],
        "linker_family_change": ["topology", "Dimensionality", "metal_cluster", "functional_cluster"],
        "functional_motif_change": ["topology", "Dimensionality", "metal_cluster", "linker_cluster"],
    }

    profile = []
    tasks = []
    completed, aggregate = load_completed()

    for intervention, fixed in specs.items():
        for keys, group in frame.groupby(fixed, sort=False, dropna=False):
            if len(group) < 2:
                continue
            if not isinstance(keys, tuple):
                keys = (keys,)
            gid = group_id(intervention, keys)
            possible = len(group) * (len(group) - 1) // 2
            profile.append({"intervention": intervention, "group_id": gid,
                            "group_size": len(group), "possible_pairs": possible})
            if gid in completed:
                continue
            columns = list(dict.fromkeys([
                "mof_id", "topology", "Dimensionality", "metals", "single_metal",
                "metal_site_count", "metal_cluster", "linker_cluster", "functional_cluster",
                *GEOMETRY, *(linker_racs if intervention == "functional_motif_change" else [])
            ]))
            tasks.append((intervention, gid, group[columns].copy(), linker_racs,
                          WORK_DIR / intervention / f"{gid}.parquet"))

    pd.DataFrame(profile).to_csv(GROUP_PROFILE_FILE, index=False)
    print(f"N_JOBS={N_JOBS}; frameworks={len(frame):,}; context_groups={len(profile):,}; pending_groups={len(tasks):,}")
    prof = pd.DataFrame(profile)
    print(prof.groupby("intervention").agg(groups=("group_id", "size"),
          frameworks_in_groups=("group_size", "sum"), max_group=("group_size", "max"),
          possible_pairs=("possible_pairs", "sum")).to_string())

    progress = {"groups": 0, "pairs": 0, "accepted": 0}
    pending = set()
    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:
        for task in tasks:
            pending.add(executor.submit(process_group, task))
            if len(pending) >= MAX_PENDING:
                pending = collect_one(pending, aggregate, progress)
        while pending:
            pending = collect_one(pending, aggregate, progress)

    summary = pd.DataFrame([
        {"intervention": intervention, "status": status,
         "geometry_tier": tier, "pairs": count}
        for (intervention, status, tier), count in aggregate.items()
    ]).sort_values(["intervention", "status", "geometry_tier"])
    summary.to_csv(SUMMARY_FILE, index=False)
    finalize_outputs()
    print(summary.to_string(index=False))
    print(f"\nSaved summary: {SUMMARY_FILE}")
    print(f"Saved final pair tables: {OUTPUT_DIR}")
    print("CrystalNN and adsorption outcomes were not used. No missing values were filled.")


if __name__ == "__main__":
    main()

