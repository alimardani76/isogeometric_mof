#!/usr/bin/env python3
"""Fixed caliper-sensitivity analysis for Project 7.

This script measures how support, sample composition, adsorption-difference
magnitude, pressure behavior, and residual-geometry association change across
four geometry definitions fixed before this run:

- very_tight: diameters 1%, density/cell volume 2%, void fractions 0.01
- tight:      diameters 2%, density/cell volume 3%, void fractions 0.02
- primary:    diameters 3%, density/cell volume 5%, void fractions 0.03
- moderate:   diameters 5%, density/cell volume 10%, void fractions 0.05

The 3% tier remains primary because it was fixed before outcome interpretation.
The other tiers are sensitivity analyses, not candidate replacements.

The script begins from the already enumerated chemistry-valid pair tables, keeps
coordination-compatible metal pairs, rebuilds related-comparison groups within
each tier, joins observed adsorption values, and estimates direction-free
magnitudes. No threshold is selected from the output. No missing value is filled.
"""
from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha1
from pathlib import Path
import gc
import re

import numpy as np
import pandas as pd
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
ANALYSIS = ROOT / "analysis"

MASTER_FILE = ANALYSIS / "framework_master.parquet"
METAL_FILE = ANALYSIS / "metal_pairs_coordination_classified.parquet"
LINKER_FILE = ANALYSIS / "full_pair_rules" / "linker_family_change.parquet"
FUNCTIONAL_FILE = ANALYSIS / "full_pair_rules" / "functional_motif_change.parquet"
SCALE_FILE = ANALYSIS / "adsorption_condition_scales.csv"

PAIR_OUTPUT = ANALYSIS / "caliper_sensitivity_pair_assignments.parquet"
SUPPORT_OUTPUT = ANALYSIS / "caliper_sensitivity_support.csv"
COMPOSITION_OUTPUT = ANALYSIS / "caliper_sensitivity_composition.csv"
EFFECT_OUTPUT = ANALYSIS / "caliper_sensitivity_effects.csv"
PRESSURE_OUTPUT = ANALYSIS / "caliper_sensitivity_pressure.csv"
GEOMETRY_OUTPUT = ANALYSIS / "caliper_sensitivity_residual_geometry.csv"
RUN_OUTPUT = ANALYSIS / "caliper_sensitivity_run_summary.csv"

N_JOBS = 6
BOOTSTRAP_REPLICATES = 10_000
BASE_SEED = 1701
CHUNK_SIZE = 250_000

ADSORPTION_FILES = {
    "landfill-CH4.csv": "landfill_CH4",
    "landfill-CO2.csv": "landfill_CO2",
    "methane.csv": "methane_storage_CH4",
    "methane_purification-CH4.csv": "methane_purification_CH4",
    "methane_purification-CO2.csv": "methane_purification_CO2",
    "post_comb_vsa-CO2.csv": "post_combustion_CO2",
    "post_comb_vsa-N2.csv": "post_combustion_N2",
    "pre_comb_4040-CO2.csv": "pre_combustion_CO2",
    "pre_comb_4040-H2.csv": "pre_combustion_H2",
}

TIERS = {
    "very_tight": {
        "order": 1,
        "Di_diff": 0.01, "Df_diff": 0.01, "Dif_diff": 0.01,
        "Density_diff": 0.02, "UC_volume_diff": 0.02,
        "AVAf_diff": 0.01, "POAVAf_diff": 0.01,
    },
    "tight": {
        "order": 2,
        "Di_diff": 0.02, "Df_diff": 0.02, "Dif_diff": 0.02,
        "Density_diff": 0.03, "UC_volume_diff": 0.03,
        "AVAf_diff": 0.02, "POAVAf_diff": 0.02,
    },
    "primary": {
        "order": 3,
        "Di_diff": 0.03, "Df_diff": 0.03, "Dif_diff": 0.03,
        "Density_diff": 0.05, "UC_volume_diff": 0.05,
        "AVAf_diff": 0.03, "POAVAf_diff": 0.03,
    },
    "moderate": {
        "order": 4,
        "Di_diff": 0.05, "Df_diff": 0.05, "Dif_diff": 0.05,
        "Density_diff": 0.10, "UC_volume_diff": 0.10,
        "AVAf_diff": 0.05, "POAVAf_diff": 0.05,
    },
}

GEOMETRY_COLUMNS = [
    "Di_diff", "Df_diff", "Dif_diff", "Density_diff",
    "UC_volume_diff", "AVAf_diff", "POAVAf_diff",
]

EFFECT_COLUMNS = [
    "absolute_uptake_difference",
    "absolute_log_difference",
    "standardized_absolute_difference",
]


def canonical_id(series):
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"(?i)\.cif$", "", regex=True)
        .str.replace(r"(?i)_repeat$", "", regex=True)
    )


def variant_family(value):
    text = str(value).strip()
    text = re.sub(r"(?i)_clean$", "", text)
    text = re.sub(r"(?i)_freeONLY$", "", text)
    return text


def stable_family_id(tier, intervention, nodes):
    raw = tier + "|" + intervention + "|" + "|".join(sorted(nodes))
    return "family_" + sha1(raw.encode("utf-8")).hexdigest()[:16]


class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}

    def add(self, item):
        if item not in self.parent:
            self.parent[item] = item
            self.rank[item] = 0

    def find(self, item):
        root = item
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[item] != item:
            parent = self.parent[item]
            self.parent[item] = root
            item = parent
        return root

    def union(self, a, b):
        self.add(a); self.add(b)
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


def load_candidate_pairs():
    for path in [METAL_FILE, LINKER_FILE, FUNCTIONAL_FILE]:
        if not path.exists():
            raise FileNotFoundError(path)

    metal = pd.read_parquet(METAL_FILE)
    metal = metal.loc[
        metal["coordination_class"].eq("coordination_compatible")
    ].copy()
    metal["intervention"] = "metal_substitution"

    linker = pd.read_parquet(LINKER_FILE)
    linker["intervention"] = "linker_family_change"

    functional = pd.read_parquet(FUNCTIONAL_FILE)
    functional["intervention"] = "functional_motif_change"

    # The broad pair tables predate creation of the plain-language unordered
    # transition label. Reconstruct that label from the stored chemistry fields
    # rather than requiring a column that does not exist in these source files.
    def unordered_label(a, b):
        values = sorted([str(a), str(b)])
        return values[0] + " <-> " + values[1]

    metal["transition"] = metal.apply(
        lambda row: unordered_label(row["metals_a"], row["metals_b"]),
        axis=1,
    )
    linker["transition"] = linker.apply(
        lambda row: unordered_label(
            int(row["linker_cluster_a"]),
            int(row["linker_cluster_b"]),
        ),
        axis=1,
    )
    functional["transition"] = functional.apply(
        lambda row: unordered_label(
            int(row["functional_cluster_a"]),
            int(row["functional_cluster_b"]),
        ),
        axis=1,
    )

    pairs = pd.concat([metal, linker, functional], ignore_index=True, sort=False)
    required = [
        "id_a", "id_b", "pair_lo", "pair_hi", "intervention", "transition",
        "topology", *GEOMETRY_COLUMNS,
    ]
    missing = [column for column in required if column not in pairs.columns]
    if missing:
        raise ValueError(f"Candidate tables are missing columns: {missing}")
    if pairs[["intervention", "pair_lo", "pair_hi"]].duplicated().any():
        raise RuntimeError("Duplicate unordered candidate pairs")
    if pairs["transition"].isna().any() or pairs["transition"].astype("string").str.strip().eq("").any():
        raise RuntimeError("Missing reconstructed chemistry-transition labels")
    pairs["variant_a"] = pairs["id_a"].map(variant_family)
    pairs["variant_b"] = pairs["id_b"].map(variant_family)
    pairs["variant_lo"] = pairs[["variant_a", "variant_b"]].min(axis=1)
    pairs["variant_hi"] = pairs[["variant_a", "variant_b"]].max(axis=1)
    return pairs


def tier_filter(pairs, tier_name):
    limits = TIERS[tier_name]
    mask = np.ones(len(pairs), dtype=bool)
    for column in GEOMETRY_COLUMNS:
        mask &= pairs[column].to_numpy(dtype=float) <= limits[column] + 1e-12
    result = pairs.loc[mask].copy()
    result["tier"] = tier_name
    result["tier_order"] = limits["order"]

    normalized = []
    for column in GEOMETRY_COLUMNS:
        output = f"fraction_{column}"
        result[output] = result[column] / limits[column]
        normalized.append(output)
    result["residual_geometry_score"] = np.sqrt(
        np.mean(np.square(result[normalized].to_numpy(dtype=float)), axis=1)
    )
    result["maximum_fraction_of_limit"] = result[normalized].max(axis=1)
    return result


def assign_related_groups(frame, tier_name):
    outputs = []
    for intervention, group in frame.groupby("intervention", sort=False):
        uf = UnionFind()
        for row in group.itertuples(index=False):
            uf.union(row.variant_lo, row.variant_hi)
        components = defaultdict(set)
        for node in uf.parent:
            components[uf.find(node)].add(node)
        family_by_root = {
            root: stable_family_id(tier_name, intervention, nodes)
            for root, nodes in components.items()
        }
        group = group.copy()
        group["related_group_id"] = group["variant_lo"].map(
            lambda node: family_by_root[uf.find(node)]
        )
        outputs.append(group)
    return pd.concat(outputs, ignore_index=True, sort=False)


def load_adsorption(wanted_ids):
    parts = []
    for filename, target in ADSORPTION_FILES.items():
        retained = 0
        for chunk in pd.read_csv(
            RAW / filename,
            usecols=["filename", "T/K", "p/bar", "mmol/g"],
            chunksize=CHUNK_SIZE,
        ):
            chunk["mof_id"] = canonical_id(chunk["filename"])
            chunk = chunk.loc[chunk["mof_id"].isin(wanted_ids)].copy()
            if chunk.empty:
                continue
            for column in ["T/K", "p/bar", "mmol/g"]:
                chunk[column] = pd.to_numeric(chunk[column], errors="coerce")
            chunk["target"] = target
            parts.append(chunk[["mof_id", "target", "T/K", "p/bar", "mmol/g"]])
            retained += len(chunk)
        print(f"loaded adsorption: {filename}; retained={retained:,}")
        gc.collect()
    adsorption = pd.concat(parts, ignore_index=True)
    if adsorption.duplicated(["mof_id", "target", "T/K", "p/bar"]).any():
        raise RuntimeError("Duplicate framework-condition adsorption rows")
    return adsorption


def spearman_no_p(x, y):
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]; y = y[valid]
    if len(x) < 3 or np.all(x == x[0]) or np.all(y == y[0]):
        return np.nan
    return float(np.corrcoef(rankdata(x), rankdata(y))[0, 1])


def bootstrap_task(task):
    task_id, statistic, x, y = task
    rng = np.random.default_rng(BASE_SEED + task_id)
    x = np.asarray(x, dtype=float)
    y = None if y is None else np.asarray(y, dtype=float)
    values = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    n = len(x)
    for index in range(BOOTSTRAP_REPLICATES):
        draw = rng.integers(0, n, size=n)
        if statistic == "median":
            values[index] = np.median(x[draw])
        elif statistic == "spearman":
            values[index] = spearman_no_p(x[draw], y[draw])
        else:
            raise ValueError(statistic)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return task_id, np.nan, np.nan
    low, high = np.quantile(values, [0.025, 0.975])
    return task_id, float(low), float(high)


def main():
    if not MASTER_FILE.exists() or not SCALE_FILE.exists():
        raise FileNotFoundError("Missing framework master or adsorption condition scales")

    candidates = load_candidate_pairs()
    tier_pairs = []
    for tier_name in TIERS:
        selected = tier_filter(candidates, tier_name)
        selected = assign_related_groups(selected, tier_name)
        tier_pairs.append(selected)
        print(f"tier={tier_name}; selected_pairs={len(selected):,}")
    all_pairs = pd.concat(tier_pairs, ignore_index=True, sort=False)
    all_pairs.to_parquet(PAIR_OUTPUT, index=False)

    widest = all_pairs.loc[all_pairs["tier"].eq("moderate")]
    wanted_ids = set(widest["id_a"].astype(str)) | set(widest["id_b"].astype(str))
    adsorption = load_adsorption(wanted_ids)
    scales = pd.read_csv(SCALE_FILE, low_memory=False)
    conditions = scales[["target", "T/K", "p/bar"]].drop_duplicates()
    if len(conditions) != 18:
        raise RuntimeError(f"Expected 18 conditions, found {len(conditions)}")

    master = pd.read_parquet(MASTER_FILE, columns=["mof_id", "DB_num"])
    db_map = master.set_index("mof_id")["DB_num"]

    support_rows = []
    composition_rows = []
    group_effect_parts = []

    left_ads = adsorption.rename(columns={"mof_id": "id_a", "mmol/g": "uptake_a"})
    right_ads = adsorption.rename(columns={"mof_id": "id_b", "mmol/g": "uptake_b"})

    for tier_name, pairs in all_pairs.groupby("tier", sort=False):
        for intervention, group in pairs.groupby("intervention", sort=False):
            endpoints = set(group["id_a"]) | set(group["id_b"])
            endpoint_db = db_map.reindex(list(endpoints)).dropna()
            support_rows.append({
                "tier": tier_name,
                "tier_order": TIERS[tier_name]["order"],
                "intervention": intervention,
                "raw_pairs": len(group),
                "related_groups": group["related_group_id"].nunique(),
                "frameworks": len(endpoints),
                "exact_changes": group["transition"].nunique(),
                "topologies": group["topology"].nunique(dropna=True),
                "database_origins": endpoint_db.nunique(),
                "median_residual_geometry_score": group["residual_geometry_score"].median(),
                "maximum_residual_geometry_score": group["residual_geometry_score"].max(),
            })
            for database, count in endpoint_db.value_counts().items():
                composition_rows.append({
                    "tier": tier_name,
                    "intervention": intervention,
                    "composition_type": "database",
                    "label": database,
                    "frameworks": int(count),
                })
            for topology, count in group["topology"].value_counts().items():
                composition_rows.append({
                    "tier": tier_name,
                    "intervention": intervention,
                    "composition_type": "topology_pair_rows",
                    "label": topology,
                    "frameworks": int(count),
                })

        grid = (pairs.assign(_key=1)
                .merge(conditions.assign(_key=1), on="_key", how="inner")
                .drop(columns="_key"))
        merged = (grid
                  .merge(left_ads, on=["id_a", "target", "T/K", "p/bar"], how="left", validate="many_to_one")
                  .merge(right_ads, on=["id_b", "target", "T/K", "p/bar"], how="left", validate="many_to_one")
                  .merge(scales, on=["target", "T/K", "p/bar"], how="left", validate="many_to_one"))
        merged["complete"] = merged["uptake_a"].notna() & merged["uptake_b"].notna()
        complete = merged.loc[merged["complete"]].copy()
        complete["absolute_uptake_difference"] = (complete["uptake_b"] - complete["uptake_a"]).abs()
        complete["absolute_log_difference"] = (
            np.log(complete["uptake_b"] + complete["epsilon_primary"])
            - np.log(complete["uptake_a"] + complete["epsilon_primary"])
        ).abs()
        complete["standardized_absolute_difference"] = (
            complete["absolute_uptake_difference"]
            / complete["robust_scale_iqr_over_1_349"]
        )

        group_effect = (
            complete.groupby(
                ["tier", "tier_order", "intervention", "related_group_id", "target", "T/K", "p/bar"],
                as_index=False,
            )
            .agg(
                residual_geometry_score=("residual_geometry_score", "median"),
                pair_rows=("pair_lo", "size"),
                absolute_uptake_difference=("absolute_uptake_difference", "median"),
                absolute_log_difference=("absolute_log_difference", "median"),
                standardized_absolute_difference=("standardized_absolute_difference", "median"),
            )
        )
        group_effect_parts.append(group_effect)
        del grid, merged, complete, group_effect
        gc.collect()

    group_effects = pd.concat(group_effect_parts, ignore_index=True)

    effect_rows = []
    geometry_rows = []
    bootstrap_tasks = []
    task_refs = {}
    task_id = 0

    for keys, group in group_effects.groupby(
        ["tier", "tier_order", "intervention", "target", "T/K", "p/bar"], sort=False
    ):
        tier_name, tier_order, intervention, target, temperature, pressure = keys
        for effect in EFFECT_COLUMNS:
            values = group[effect].dropna().to_numpy(dtype=float)
            row_index = len(effect_rows)
            effect_rows.append({
                "tier": tier_name,
                "tier_order": tier_order,
                "intervention": intervention,
                "target": target,
                "T/K": temperature,
                "p/bar": pressure,
                "effect_measure": effect,
                "groups": len(values),
                "median_effect_magnitude": float(np.median(values)),
            })
            bootstrap_tasks.append((task_id, "median", values, None))
            task_refs[task_id] = ("effect", row_index)
            task_id += 1

            x = group["residual_geometry_score"].to_numpy(dtype=float)
            y = group[effect].to_numpy(dtype=float)
            geometry_index = len(geometry_rows)
            geometry_rows.append({
                "tier": tier_name,
                "tier_order": tier_order,
                "intervention": intervention,
                "target": target,
                "T/K": temperature,
                "p/bar": pressure,
                "effect_measure": effect,
                "groups": len(group),
                "spearman_rho": spearman_no_p(x, y),
            })
            bootstrap_tasks.append((task_id, "spearman", x, y))
            task_refs[task_id] = ("geometry", geometry_index)
            task_id += 1

    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:
        bootstrap_results = list(executor.map(bootstrap_task, bootstrap_tasks))

    for returned_id, low, high in bootstrap_results:
        table, index = task_refs[returned_id]
        if table == "effect":
            effect_rows[index]["bootstrap_95_low"] = low
            effect_rows[index]["bootstrap_95_high"] = high
        else:
            geometry_rows[index]["bootstrap_95_low_rho"] = low
            geometry_rows[index]["bootstrap_95_high_rho"] = high

    effects = pd.DataFrame(effect_rows)
    geometry = pd.DataFrame(geometry_rows)
    effects.to_csv(EFFECT_OUTPUT, index=False)
    geometry.to_csv(GEOMETRY_OUTPUT, index=False)

    pressure_rows = []
    for keys, group in effects.groupby(
        ["tier", "tier_order", "intervention", "target", "T/K", "effect_measure"], sort=False
    ):
        group = group.sort_values("p/bar")
        if len(group) != 2:
            raise RuntimeError(f"Expected two pressures for {keys}")
        low, high = group.iloc[0], group.iloc[1]
        pressure_rows.append({
            "tier": keys[0],
            "tier_order": keys[1],
            "intervention": keys[2],
            "target": keys[3],
            "T/K": keys[4],
            "effect_measure": keys[5],
            "p/bar_low": low["p/bar"],
            "p/bar_high": high["p/bar"],
            "groups_low": low["groups"],
            "groups_high": high["groups"],
            "median_low": low["median_effect_magnitude"],
            "median_high": high["median_effect_magnitude"],
            "high_minus_low": high["median_effect_magnitude"] - low["median_effect_magnitude"],
        })
    pressure = pd.DataFrame(pressure_rows)
    pressure.to_csv(PRESSURE_OUTPUT, index=False)

    support = pd.DataFrame(support_rows).sort_values(["tier_order", "intervention"])
    composition = pd.DataFrame(composition_rows)
    support.to_csv(SUPPORT_OUTPUT, index=False)
    composition.to_csv(COMPOSITION_OUTPUT, index=False)

    run_summary = (
        pressure.groupby(["tier", "tier_order", "intervention", "effect_measure"], as_index=False)
        .agg(
            pressure_comparisons=("target", "size"),
            magnitude_increased=("high_minus_low", lambda v: int((v > 0).sum())),
            magnitude_decreased=("high_minus_low", lambda v: int((v < 0).sum())),
        )
        .merge(
            geometry.groupby(["tier", "tier_order", "intervention", "effect_measure"], as_index=False)
            .agg(
                median_absolute_rho=("spearman_rho", lambda v: float(np.median(np.abs(v)))),
                maximum_absolute_rho=("spearman_rho", lambda v: float(np.max(np.abs(v)))),
                positive_rho_intervals=("bootstrap_95_low_rho", lambda v: int((v > 0).sum())),
            ),
            on=["tier", "tier_order", "intervention", "effect_measure"],
            validate="one_to_one",
        )
        .sort_values(["tier_order", "intervention", "effect_measure"])
    )
    run_summary.to_csv(RUN_OUTPUT, index=False)

    print(
        f"N_JOBS={N_JOBS}; bootstrap_replicates={BOOTSTRAP_REPLICATES}; "
        f"seed_base={BASE_SEED}; bootstrap_tasks={len(bootstrap_tasks)}"
    )
    print("\nSUPPORT ACROSS FIXED CALIPERS")
    print(support.to_string(index=False))
    print("\nROBUSTNESS SUMMARY")
    print(run_summary.to_string(index=False))
    print("\nOutputs:")
    for path in [PAIR_OUTPUT, SUPPORT_OUTPUT, COMPOSITION_OUTPUT, EFFECT_OUTPUT,
                 PRESSURE_OUTPUT, GEOMETRY_OUTPUT, RUN_OUTPUT]:
        print(path)
    print(
        "The primary 3% tier was not replaced. No threshold was selected from "
        "the outcomes. Metal changes remained unordered. No p-value, predictive "
        "model, or missing-value filling was used."
    )


if __name__ == "__main__":
    main()

