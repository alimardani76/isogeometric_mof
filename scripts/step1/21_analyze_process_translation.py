#!/usr/bin/env python3
"""Estimate process translation for the frozen Project 7 primary pairs.

Scientific question
-------------------
When two matched frameworks differ in uptake, does the framework with higher
process uptake also retain higher working capacity and, for separation
processes, higher selectivity?

The analysis remains direction-free with respect to chemistry. Pair orientation
is defined only by the observed process uptake for the trade-off diagnostic;
it is not interpreted as a chemical substitution direction.

Primary endpoints
-----------------
- mmol/g_working_capacity for all five processes;
- selectivity for the four separation processes where it is observed.

Secondary derived process scores (purity, SSP, AFM) are not analyzed here.
They remain available for later SI analyses after the primary process result is
understood.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import platform
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
ANALYSIS = ROOT / "analysis"

PROCESS_INPUT = RAW / "overall_process.csv"
PAIR_INPUT = ANALYSIS / "final_primary_pairs.parquet"

PAIR_PROCESS_OUTPUT = ANALYSIS / "process_translation_pair_results_final.parquet"
GROUP_PROCESS_OUTPUT = ANALYSIS / "process_translation_group_results_final.parquet"
SUMMARY_OUTPUT = ANALYSIS / "process_translation_summary_final.csv"
ATTRITION_OUTPUT = ANALYSIS / "process_translation_attrition_final.csv"
MANIFEST_OUTPUT = ANALYSIS / "process_translation_manifest_final.json"

N_JOBS = 6
BOOTSTRAP_REPLICATES = 10_000
BASE_SEED = 1701

REQUIRED_PROCESS_COLUMNS = [
    "filename",
    "process",
    "mmol/g_uptake",
    "mmol/g_working_capacity",
    "selectivity",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_id(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"(?i)\.cif$", "", regex=True)
        .str.replace(r"(?i)_repeat$", "", regex=True)
    )


def variant_id(series: pd.Series) -> pd.Series:
    return (
        canonical_id(series)
        .str.replace(r"(?i)_structure_clean$", "", regex=True)
        .str.replace(r"(?i)_structure_freeonly$", "", regex=True)
        .str.replace(r"(?i)_clean$", "", regex=True)
        .str.replace(r"(?i)_freeonly$", "", regex=True)
    )


class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}

    def add(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != x:
            parent = self.parent[x]
            self.parent[x] = root
            x = parent
        return root

    def union(self, a, b):
        self.add(a)
        self.add(b)
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


def assign_related_groups(pairs: pd.DataFrame) -> pd.DataFrame:
    pairs = pairs.copy()
    pairs["variant_a"] = variant_id(pairs["id_a"])
    pairs["variant_b"] = variant_id(pairs["id_b"])
    pairs["related_group_id"] = pd.NA

    for intervention, index in pairs.groupby("intervention").groups.items():
        uf = UnionFind()
        subset = pairs.loc[index, ["variant_a", "variant_b"]]
        for a, b in subset.itertuples(index=False):
            uf.union(str(a), str(b))
        roots = sorted({uf.find(str(x)) for x in pd.concat([subset["variant_a"], subset["variant_b"]])})
        root_to_id = {
            root: hashlib.sha1(f"{intervention}|{root}".encode()).hexdigest()[:16]
            for root in roots
        }
        values = [
            "group_" + root_to_id[uf.find(str(a))]
            for a in subset["variant_a"]
        ]
        pairs.loc[index, "related_group_id"] = values

    if pairs["related_group_id"].isna().any():
        raise RuntimeError("Failed to assign a related group to every pair")
    return pairs


def bootstrap_task(task):
    intervention, process, metric, values, seed = task
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return {
            "intervention": intervention,
            "process": process,
            "metric": metric,
            "groups": 0,
            "statistic": (
                "equal_weight_group_mean"
                if metric.endswith("_concordant")
                else "equal_weight_group_median"
            ),
            "estimate": np.nan,
            "bootstrap_95_low": np.nan,
            "bootstrap_95_high": np.nan,
        }
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(BOOTSTRAP_REPLICATES, len(values)))

    if metric.endswith("_concordant"):
        point = float(np.mean(values))
        boot = np.mean(values[idx], axis=1)
        statistic = "equal_weight_group_mean"
    else:
        point = float(np.median(values))
        boot = np.median(values[idx], axis=1)
        statistic = "equal_weight_group_median"

    return {
        "intervention": intervention,
        "process": process,
        "metric": metric,
        "groups": int(len(values)),
        "statistic": statistic,
        "estimate": point,
        "bootstrap_95_low": float(np.quantile(boot, 0.025)),
        "bootstrap_95_high": float(np.quantile(boot, 0.975)),
    }


def main() -> None:
    for path in [PROCESS_INPUT, PAIR_INPUT]:
        if not path.exists():
            raise FileNotFoundError(path)

    pairs = pd.read_parquet(PAIR_INPUT)
    required_pair_columns = {"id_a", "id_b", "intervention"}
    missing = sorted(required_pair_columns - set(pairs.columns))
    if missing:
        raise ValueError(f"Frozen pair catalogue lacks columns: {missing}")

    pairs["id_a"] = canonical_id(pairs["id_a"])
    pairs["id_b"] = canonical_id(pairs["id_b"])
    pairs = assign_related_groups(pairs)

    expected_groups = {
        "metal_substitution": 453,
        "linker_family_change": 3494,
        "functional_motif_change": 6,
    }
    observed_groups = (
        pairs.groupby("intervention")["related_group_id"].nunique().to_dict()
    )
    if observed_groups != expected_groups:
        raise RuntimeError(
            "Related-group reconstruction does not match the frozen design. "
            f"Expected {expected_groups}; observed {observed_groups}."
        )

    needed_ids = set(pairs["id_a"]) | set(pairs["id_b"])

    process = pd.read_csv(
        PROCESS_INPUT,
        usecols=REQUIRED_PROCESS_COLUMNS,
        low_memory=False,
    )
    process["mof_id"] = canonical_id(process["filename"])
    process = process.loc[process["mof_id"].isin(needed_ids)].copy()

    for column in ["mmol/g_uptake", "mmol/g_working_capacity", "selectivity"]:
        process[column] = pd.to_numeric(process[column], errors="coerce")

    if process.duplicated(["mof_id", "process"]).any():
        raise RuntimeError("Duplicate framework-process records detected")

    process["uptake_valid"] = (
        process["mmol/g_uptake"].notna()
        & np.isfinite(process["mmol/g_uptake"])
        & process["mmol/g_uptake"].ge(0)
    )
    process["working_capacity_valid"] = (
        process["mmol/g_working_capacity"].notna()
        & np.isfinite(process["mmol/g_working_capacity"])
        & process["mmol/g_working_capacity"].ge(0)
    )
    process["selectivity_valid"] = (
        process["selectivity"].notna()
        & np.isfinite(process["selectivity"])
        & process["selectivity"].gt(0)
    )

    conditions = process[["process"]].drop_duplicates().sort_values("process")
    grid = (
        pairs.assign(_key=1)
        .merge(conditions.assign(_key=1), on="_key", how="inner")
        .drop(columns="_key")
    )

    endpoint_columns = [
        "mof_id",
        "process",
        "mmol/g_uptake",
        "mmol/g_working_capacity",
        "selectivity",
        "uptake_valid",
        "working_capacity_valid",
        "selectivity_valid",
    ]
    left = process[endpoint_columns].rename(
        columns={
            "mof_id": "id_a",
            "mmol/g_uptake": "uptake_a",
            "mmol/g_working_capacity": "working_capacity_a",
            "selectivity": "selectivity_a",
            "uptake_valid": "uptake_valid_a",
            "working_capacity_valid": "working_capacity_valid_a",
            "selectivity_valid": "selectivity_valid_a",
        }
    )
    right = process[endpoint_columns].rename(
        columns={
            "mof_id": "id_b",
            "mmol/g_uptake": "uptake_b",
            "mmol/g_working_capacity": "working_capacity_b",
            "selectivity": "selectivity_b",
            "uptake_valid": "uptake_valid_b",
            "working_capacity_valid": "working_capacity_valid_b",
            "selectivity_valid": "selectivity_valid_b",
        }
    )

    merged = grid.merge(
        left, on=["id_a", "process"], how="left", validate="many_to_one"
    )
    merged = merged.merge(
        right, on=["id_b", "process"], how="left", validate="many_to_one"
    )

    for column in [
        "uptake_valid_a", "uptake_valid_b",
        "working_capacity_valid_a", "working_capacity_valid_b",
        "selectivity_valid_a", "selectivity_valid_b",
    ]:
        merged[column] = merged[column].astype("boolean").fillna(False).astype(bool)

    merged["uptake_pair_complete"] = merged["uptake_valid_a"] & merged["uptake_valid_b"]
    merged["working_capacity_pair_complete"] = (
        merged["working_capacity_valid_a"] & merged["working_capacity_valid_b"]
    )
    merged["selectivity_pair_complete"] = (
        merged["selectivity_valid_a"] & merged["selectivity_valid_b"]
    )

    merged["absolute_uptake_difference"] = (
        merged["uptake_b"] - merged["uptake_a"]
    ).abs().where(merged["uptake_pair_complete"])
    merged["absolute_working_capacity_difference"] = (
        merged["working_capacity_b"] - merged["working_capacity_a"]
    ).abs().where(merged["working_capacity_pair_complete"])
    merged["absolute_selectivity_difference"] = (
        merged["selectivity_b"] - merged["selectivity_a"]
    ).abs().where(merged["selectivity_pair_complete"])

    uptake_sign = np.sign(merged["uptake_b"] - merged["uptake_a"])
    wc_sign = np.sign(merged["working_capacity_b"] - merged["working_capacity_a"])
    sel_sign = np.sign(merged["selectivity_b"] - merged["selectivity_a"])

    non_tied_uptake = merged["uptake_pair_complete"] & uptake_sign.ne(0)

    merged["working_capacity_change_oriented_by_uptake"] = (
        uptake_sign * (merged["working_capacity_b"] - merged["working_capacity_a"])
    ).where(non_tied_uptake & merged["working_capacity_pair_complete"])
    merged["selectivity_change_oriented_by_uptake"] = (
        uptake_sign * (merged["selectivity_b"] - merged["selectivity_a"])
    ).where(non_tied_uptake & merged["selectivity_pair_complete"])

    merged["uptake_working_capacity_concordant"] = (
        uptake_sign.eq(wc_sign)
    ).where(non_tied_uptake & merged["working_capacity_pair_complete"])
    merged["uptake_selectivity_concordant"] = (
        uptake_sign.eq(sel_sign)
    ).where(non_tied_uptake & merged["selectivity_pair_complete"])

    merged.to_parquet(PAIR_PROCESS_OUTPUT, index=False)

    aggregation = {
        "absolute_uptake_difference": "median",
        "absolute_working_capacity_difference": "median",
        "absolute_selectivity_difference": "median",
        "working_capacity_change_oriented_by_uptake": "median",
        "selectivity_change_oriented_by_uptake": "median",
        "uptake_working_capacity_concordant": "mean",
        "uptake_selectivity_concordant": "mean",
    }
    group_results = (
        merged.groupby(
            ["intervention", "related_group_id", "process"],
            as_index=False,
            dropna=False,
        )
        .agg(aggregation)
    )
    group_results.to_parquet(GROUP_PROCESS_OUTPUT, index=False)

    metric_columns = list(aggregation)
    tasks = []
    task_number = 0
    for (intervention, process_name), group in group_results.groupby(
        ["intervention", "process"], sort=True
    ):
        for metric in metric_columns:
            values = group[metric].dropna().astype(float).tolist()
            tasks.append(
                (
                    intervention,
                    process_name,
                    metric,
                    values,
                    BASE_SEED + task_number,
                )
            )
            task_number += 1

    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:
        summary_rows = list(executor.map(bootstrap_task, tasks, chunksize=1))
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(SUMMARY_OUTPUT, index=False)

    attrition_rows = []
    for (intervention, process_name), group in merged.groupby(
        ["intervention", "process"], sort=True
    ):
        attrition_rows.append(
            {
                "intervention": intervention,
                "process": process_name,
                "expected_pairs": len(group),
                "uptake_complete_pairs": int(group["uptake_pair_complete"].sum()),
                "working_capacity_complete_pairs": int(
                    group["working_capacity_pair_complete"].sum()
                ),
                "selectivity_complete_pairs": int(
                    group["selectivity_pair_complete"].sum()
                ),
                "related_groups": int(group["related_group_id"].nunique()),
            }
        )
    attrition = pd.DataFrame(attrition_rows)
    attrition.to_csv(ATTRITION_OUTPUT, index=False)

    manifest = {
        "stage": "Primary process translation",
        "process_input": str(PROCESS_INPUT),
        "process_input_sha256": sha256(PROCESS_INPUT),
        "pair_input": str(PAIR_INPUT),
        "pair_input_sha256": sha256(PAIR_INPUT),
        "n_jobs": N_JOBS,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "seed_base": BASE_SEED,
        "primary_endpoints": [
            "mmol/g_working_capacity",
            "selectivity",
        ],
        "chemistry_direction_assigned": False,
        "tradeoff_orientation": "higher observed process uptake endpoint",
        "missing_values_filled": False,
        "negative_working_capacity_used": False,
        "predictive_model_fitted": False,
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
    }
    MANIFEST_OUTPUT.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

    print(
        f"N_JOBS={N_JOBS}; bootstrap_replicates={BOOTSTRAP_REPLICATES}; "
        f"seed_base={BASE_SEED}"
    )
    print()
    print("PROCESS ATTRITION")
    print(attrition.to_string(index=False))
    print()
    print("PROCESS TRANSLATION SUMMARY")
    print(summary.to_string(index=False))
    print()
    print("Outputs:")
    for path in [
        PAIR_PROCESS_OUTPUT,
        GROUP_PROCESS_OUTPUT,
        SUMMARY_OUTPUT,
        ATTRITION_OUTPUT,
        MANIFEST_OUTPUT,
    ]:
        print(path)
    print(
        "Negative or missing working capacities were excluded only from their "
        "specific process endpoint. Chemistry changes remained unordered. "
        "No process value was filled or repaired."
    )


if __name__ == "__main__":
    main()

