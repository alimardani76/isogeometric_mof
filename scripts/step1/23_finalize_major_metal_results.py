#!/usr/bin/env python3
"""Finalize raw chemistry results for the five well-supported metal changes.

This is the last class-level numerical analysis before case selection and figure
production. It combines the existing pressure and process outputs for Co-Cu,
Cu-Zn, Fe-Zn, Co-Fe, and Cu-Fe without assigning a chemical direction.

No pair selection, adsorption recalculation, model fitting, imputation, or
threshold change is performed.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import hashlib
import json
import platform

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"

PAIR_PROCESS = ANALYSIS / "process_translation_pair_results_final.parquet"
PRESSURE = ANALYSIS / "unordered_metal_change_pressure_summary.csv"
PRIMARY_PAIRS = ANALYSIS / "final_primary_pairs.parquet"

PROCESS_PAIR_OUTPUT = ANALYSIS / "final_major_metal_process_pair_results.parquet"
PROCESS_GROUP_OUTPUT = ANALYSIS / "final_major_metal_process_group_results.parquet"
PROCESS_SUMMARY_OUTPUT = ANALYSIS / "final_major_metal_process_summary.csv"
PRESSURE_OUTPUT = ANALYSIS / "final_major_metal_pressure_summary.csv"
SUPPORT_OUTPUT = ANALYSIS / "final_major_metal_support.csv"
RUN_SUMMARY_OUTPUT = ANALYSIS / "final_major_metal_run_summary.csv"
MANIFEST_OUTPUT = ANALYSIS / "final_major_metal_manifest.json"

N_JOBS = 6
BOOTSTRAP_REPLICATES = 10_000
BASE_SEED = 1701

MAJOR_TRANSITIONS = [
    "Co <-> Cu",
    "Cu <-> Zn",
    "Fe <-> Zn",
    "Co <-> Fe",
    "Cu <-> Fe",
]

CONTINUOUS_METRICS = [
    "absolute_uptake_difference",
    "absolute_working_capacity_difference",
    "absolute_selectivity_difference",
    "working_capacity_change_oriented_by_uptake",
    "selectivity_change_oriented_by_uptake",
]

CONCORDANCE_METRICS = [
    "uptake_working_capacity_concordant",
    "uptake_selectivity_concordant",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def normalize_transition(value: str) -> str:
    text = (
        str(value)
        .replace("â†”", "<->")
        .replace("&lt;-&gt;", "<->")
        .replace("↔", "<->")
    )

    parts = [part.strip() for part in text.split("<->")]

    if len(parts) != 2:
        return text.strip()

    return " <-> ".join(sorted(parts))


def choose_column(columns, candidates, purpose):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    raise ValueError(
        f"Could not identify {purpose}. Available columns:\n"
        + "\n".join(map(str, columns))
    )


def bootstrap_task(task):
    transition, process, metric, values, seed = task
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    statistic = (
        "equal_weight_group_mean"
        if metric in CONCORDANCE_METRICS
        else "equal_weight_group_median"
    )
    if len(values) == 0:
        estimate = low = high = np.nan
    else:
        rng = np.random.default_rng(seed)
        index = rng.integers(
            0, len(values), size=(BOOTSTRAP_REPLICATES, len(values))
        )
        if metric in CONCORDANCE_METRICS:
            estimate = float(np.mean(values))
            boot = np.mean(values[index], axis=1)
        else:
            estimate = float(np.median(values))
            boot = np.median(values[index], axis=1)
        low = float(np.quantile(boot, 0.025))
        high = float(np.quantile(boot, 0.975))
    return {
        "transition": transition,
        "process": process,
        "metric": metric,
        "groups": int(len(values)),
        "statistic": statistic,
        "estimate": estimate,
        "bootstrap_95_low": low,
        "bootstrap_95_high": high,
    }


def main() -> None:
    for path in [PAIR_PROCESS, PRESSURE, PRIMARY_PAIRS]:
        if not path.exists():
            raise FileNotFoundError(path)

    pairs = pd.read_parquet(PRIMARY_PAIRS)
    transition_column = choose_column(
        pairs.columns,
        ["transition", "exact_change", "unordered_transition"],
        "metal transition in the frozen primary catalogue",
    )
    pairs["transition"] = pairs[transition_column].map(normalize_transition)
    metal_pairs = pairs.loc[
        pairs["intervention"].eq("metal_substitution")
        & pairs["transition"].isin(MAJOR_TRANSITIONS)
    ].copy()

    support = (
        metal_pairs.groupby("transition", as_index=False)
        .agg(
            raw_pairs=("pair_key", "nunique"),
            unique_frameworks_a=("id_a", "nunique"),
            unique_frameworks_b=("id_b", "nunique"),
        )
    )

    process = pd.read_parquet(PAIR_PROCESS)
    if "transition" not in process.columns:
        pair_transition = metal_pairs[["pair_key", "transition"]].drop_duplicates()
        process = process.merge(
            pair_transition,
            on="pair_key",
            how="left",
            validate="many_to_one",
        )
    else:
        process["transition"] = process["transition"].map(normalize_transition)

    process = process.loc[
        process["intervention"].eq("metal_substitution")
        & process["transition"].isin(MAJOR_TRANSITIONS)
    ].copy()

    required = {
        "transition",
        "process",
        "related_group_id",
        *CONTINUOUS_METRICS,
        *CONCORDANCE_METRICS,
    }
    missing = sorted(required - set(process.columns))
    if missing:
        raise ValueError(f"Process pair results lack columns: {missing}")

    aggregation = {metric: "median" for metric in CONTINUOUS_METRICS}
    aggregation.update({metric: "mean" for metric in CONCORDANCE_METRICS})
    group_results = (
        process.groupby(
            ["transition", "process", "related_group_id"],
            as_index=False,
            dropna=False,
        )
        .agg(aggregation)
    )

    process.to_parquet(PROCESS_PAIR_OUTPUT, index=False)
    group_results.to_parquet(PROCESS_GROUP_OUTPUT, index=False)

    tasks = []
    task_number = 0
    for (transition, process_name), group in group_results.groupby(
        ["transition", "process"], sort=True
    ):
        for metric in CONTINUOUS_METRICS + CONCORDANCE_METRICS:
            tasks.append(
                (
                    transition,
                    process_name,
                    metric,
                    group[metric].dropna().astype(float).tolist(),
                    BASE_SEED + task_number,
                )
            )
            task_number += 1

    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:
        process_summary = pd.DataFrame(
            executor.map(bootstrap_task, tasks, chunksize=1)
        )
    process_summary.to_csv(PROCESS_SUMMARY_OUTPUT, index=False)

    pressure = pd.read_csv(PRESSURE, low_memory=False)
    pressure["transition"] = pressure["transition"].map(normalize_transition)
    pressure = pressure.loc[pressure["transition"].isin(MAJOR_TRANSITIONS)].copy()
    pressure.to_csv(PRESSURE_OUTPUT, index=False)

    pressure_support = (
        pressure.groupby("transition", as_index=False)
        .agg(
            pressure_comparisons=("target", "size"),
            maximum_group_support=("groups_low", "max"),
            log_magnitude_decreased=(
                "change_in_absolute_log_difference",
                lambda x: int((x < 0).sum()),
            ),
            log_magnitude_increased=(
                "change_in_absolute_log_difference",
                lambda x: int((x > 0).sum()),
            ),
            standardized_magnitude_decreased=(
                "change_in_standardized_absolute_difference",
                lambda x: int((x < 0).sum()),
            ),
            standardized_magnitude_increased=(
                "change_in_standardized_absolute_difference",
                lambda x: int((x > 0).sum()),
            ),
        )
    )

    process_support = (
        group_results.groupby("transition", as_index=False)
        .agg(
            process_groups=("related_group_id", "nunique"),
            process_conditions=("process", "nunique"),
        )
    )

    final_support = (
        support.merge(pressure_support, on="transition", how="left")
        .merge(process_support, on="transition", how="left")
        .sort_values("raw_pairs", ascending=False)
    )
    final_support.to_csv(SUPPORT_OUTPUT, index=False)

    run_summary = []
    for transition in MAJOR_TRANSITIONS:
        row = final_support.loc[final_support["transition"].eq(transition)]
        if row.empty:
            raise RuntimeError(f"Major transition missing from final support: {transition}")
        wc = process_summary.loc[
            process_summary["transition"].eq(transition)
            & process_summary["metric"].eq(
                "working_capacity_change_oriented_by_uptake"
            )
        ]
        sel = process_summary.loc[
            process_summary["transition"].eq(transition)
            & process_summary["metric"].eq(
                "selectivity_change_oriented_by_uptake"
            )
        ]
        run_summary.append(
            {
                "transition": transition,
                "raw_pairs": int(row.iloc[0]["raw_pairs"]),
                "maximum_group_support": int(row.iloc[0]["maximum_group_support"]),
                "log_pressure_decreases": int(row.iloc[0]["log_magnitude_decreased"]),
                "log_pressure_increases": int(row.iloc[0]["log_magnitude_increased"]),
                "standardized_pressure_decreases": int(row.iloc[0]["standardized_magnitude_decreased"]),
                "standardized_pressure_increases": int(row.iloc[0]["standardized_magnitude_increased"]),
                "working_capacity_processes_positive": int((wc["estimate"] > 0).sum()),
                "working_capacity_processes_interval_above_zero": int((wc["bootstrap_95_low"] > 0).sum()),
                "selectivity_processes_positive": int((sel["estimate"] > 0).sum()),
                "selectivity_processes_interval_above_zero": int((sel["bootstrap_95_low"] > 0).sum()),
            }
        )
    run_summary = pd.DataFrame(run_summary)
    run_summary.to_csv(RUN_SUMMARY_OUTPUT, index=False)

    manifest = {
        "stage": "Final raw results for five major unordered metal changes",
        "pair_process_input": str(PAIR_PROCESS),
        "pair_process_sha256": sha256(PAIR_PROCESS),
        "pressure_input": str(PRESSURE),
        "pressure_sha256": sha256(PRESSURE),
        "primary_pairs_input": str(PRIMARY_PAIRS),
        "primary_pairs_sha256": sha256(PRIMARY_PAIRS),
        "major_transitions": MAJOR_TRANSITIONS,
        "n_jobs": N_JOBS,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "seed_base": BASE_SEED,
        "chemistry_direction_assigned": False,
        "pair_selection_changed": False,
        "missing_values_filled": False,
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
    print("FINAL MAJOR-METAL SUPPORT")
    print(final_support.to_string(index=False))
    print()
    print("FINAL MAJOR-METAL RESULT")
    print(run_summary.to_string(index=False))
    print()
    print("Outputs:")
    for path in [
        PROCESS_PAIR_OUTPUT,
        PROCESS_GROUP_OUTPUT,
        PROCESS_SUMMARY_OUTPUT,
        PRESSURE_OUTPUT,
        SUPPORT_OUTPUT,
        RUN_SUMMARY_OUTPUT,
        MANIFEST_OUTPUT,
    ]:
        print(path)
    print(
        "Metal changes remained unordered. Existing adsorption, pressure, and "
        "process results were summarized without pair reselection, imputation, "
        "or predictive modeling."
    )


if __name__ == "__main__":
    main()

