#!/usr/bin/env python3
"""Estimate unordered exact-metal-change magnitudes for Project 7.

This stage answers which repeated metal changes remain associated with adsorption
differences after the frozen chemistry, coordination, topology, dimensionality,
and measured-geometry controls. Metal changes remain unordered. No synthesis
direction is inferred.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
INPUT = ANALYSIS / "final_primary_pair_effect_magnitudes.parquet"
OUTPUT = ANALYSIS / "unordered_metal_change_magnitudes.csv"
PRESSURE_OUTPUT = ANALYSIS / "unordered_metal_change_pressure_summary.csv"
RUN_SUMMARY = ANALYSIS / "unordered_metal_change_run_summary.csv"

N_JOBS = 1
BOOTSTRAP_REPLICATES = 10_000
RANDOM_SEED = 1701
MIN_GROUPS = 5

MEASURES = [
    "absolute_uptake_difference",
    "absolute_log_difference",
    "absolute_log_difference_sensitivity",
    "standardized_absolute_difference",
]


def bootstrap_median(values, rng):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return np.nan, np.nan
    if len(values) == 1:
        return float(values[0]), float(values[0])
    draws = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    for index in range(BOOTSTRAP_REPLICATES):
        draws[index] = np.median(
            rng.choice(values, size=len(values), replace=True)
        )
    low, high = np.quantile(draws, [0.025, 0.975])
    return float(low), float(high)


def main():
    if not INPUT.exists():
        raise FileNotFoundError(INPUT)

    data = pd.read_parquet(INPUT)
    data = data.loc[
        data["intervention"].eq("metal_substitution")
        & data["outcome_complete"]
    ].copy()

    required = [
        "transition", "dependence_family_id", "target", "T/K", "p/bar",
        "evidence_unit_id", *MEASURES,
    ]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # One value per related-comparison group, exact unordered metal change,
    # and adsorption condition.
    group_level = (
        data.groupby(
            [
                "transition",
                "dependence_family_id",
                "target",
                "T/K",
                "p/bar",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(
            raw_pair_rows=("evidence_unit_id", "size"),
            distinct_comparisons=("evidence_unit_id", "nunique"),
            absolute_uptake_difference=(
                "absolute_uptake_difference", "median"
            ),
            absolute_log_difference=("absolute_log_difference", "median"),
            absolute_log_difference_sensitivity=(
                "absolute_log_difference_sensitivity", "median"
            ),
            standardized_absolute_difference=(
                "standardized_absolute_difference", "median"
            ),
        )
    )

    support = (
        group_level.groupby("transition")["dependence_family_id"]
        .nunique()
    )
    retained = set(support[support >= MIN_GROUPS].index)
    group_level = group_level.loc[
        group_level["transition"].isin(retained)
    ].copy()

    rng = np.random.default_rng(RANDOM_SEED)
    rows = []
    for keys, group in group_level.groupby(
        ["transition", "target", "T/K", "p/bar"], sort=False
    ):
        transition, target, temperature, pressure = keys
        row = {
            "transition": transition,
            "target": target,
            "T/K": temperature,
            "p/bar": pressure,
            "groups_of_related_comparisons": group[
                "dependence_family_id"
            ].nunique(),
        }
        for measure in MEASURES:
            values = group[measure].dropna().to_numpy(dtype=float)
            low, high = bootstrap_median(values, rng)
            row[f"median_{measure}"] = float(np.median(values))
            row[f"bootstrap_95_low_{measure}"] = low
            row[f"bootstrap_95_high_{measure}"] = high
        rows.append(row)

    result = pd.DataFrame(rows).sort_values(
        ["transition", "target", "T/K", "p/bar"]
    )
    result.to_csv(OUTPUT, index=False)

    pressure_rows = []
    for keys, group in result.groupby(
        ["transition", "target", "T/K"], sort=False
    ):
        transition, target, temperature = keys
        group = group.sort_values("p/bar")
        if len(group) != 2:
            raise RuntimeError(
                f"Expected two pressures for {transition}, {target}, {temperature}"
            )
        low, high = group.iloc[0], group.iloc[1]
        pressure_rows.append({
            "transition": transition,
            "target": target,
            "T/K": temperature,
            "p/bar_low": low["p/bar"],
            "p/bar_high": high["p/bar"],
            "groups_low": low["groups_of_related_comparisons"],
            "groups_high": high["groups_of_related_comparisons"],
            "median_absolute_uptake_difference_low": low[
                "median_absolute_uptake_difference"
            ],
            "median_absolute_uptake_difference_high": high[
                "median_absolute_uptake_difference"
            ],
            "median_absolute_log_difference_low": low[
                "median_absolute_log_difference"
            ],
            "median_absolute_log_difference_high": high[
                "median_absolute_log_difference"
            ],
            "change_in_absolute_log_difference": (
                high["median_absolute_log_difference"]
                - low["median_absolute_log_difference"]
            ),
            "median_standardized_absolute_difference_low": low[
                "median_standardized_absolute_difference"
            ],
            "median_standardized_absolute_difference_high": high[
                "median_standardized_absolute_difference"
            ],
            "change_in_standardized_absolute_difference": (
                high["median_standardized_absolute_difference"]
                - low["median_standardized_absolute_difference"]
            ),
            "epsilon_sensitivity_change_low": abs(
                low["median_absolute_log_difference_sensitivity"]
                - low["median_absolute_log_difference"]
            ),
            "epsilon_sensitivity_change_high": abs(
                high["median_absolute_log_difference_sensitivity"]
                - high["median_absolute_log_difference"]
            ),
        })

    pressure = pd.DataFrame(pressure_rows)
    pressure.to_csv(PRESSURE_OUTPUT, index=False)

    summary = (
        pressure.groupby("transition", as_index=False)
        .agg(
            pressure_comparisons=("target", "size"),
            maximum_group_support=("groups_low", "max"),
            log_magnitude_increased=(
                "change_in_absolute_log_difference",
                lambda values: int((values > 0).sum()),
            ),
            log_magnitude_decreased=(
                "change_in_absolute_log_difference",
                lambda values: int((values < 0).sum()),
            ),
            standardized_magnitude_increased=(
                "change_in_standardized_absolute_difference",
                lambda values: int((values > 0).sum()),
            ),
            standardized_magnitude_decreased=(
                "change_in_standardized_absolute_difference",
                lambda values: int((values < 0).sum()),
            ),
            maximum_epsilon_sensitivity_change=(
                "epsilon_sensitivity_change_low", "max"
            ),
        )
    )
    summary.to_csv(RUN_SUMMARY, index=False)

    print(
        f"N_JOBS={N_JOBS}; bootstrap_replicates={BOOTSTRAP_REPLICATES}; "
        f"seed={RANDOM_SEED}; minimum_groups={MIN_GROUPS}"
    )
    print("\nUNORDERED METAL-CHANGE SUMMARY")
    print(summary.to_string(index=False))
    print("\nPRESSURE RESULTS")
    print(
        pressure[
            [
                "transition", "target", "T/K", "p/bar_low", "p/bar_high",
                "groups_low", "groups_high",
                "median_absolute_uptake_difference_low",
                "median_absolute_uptake_difference_high",
                "median_absolute_log_difference_low",
                "median_absolute_log_difference_high",
                "change_in_absolute_log_difference",
                "median_standardized_absolute_difference_low",
                "median_standardized_absolute_difference_high",
                "change_in_standardized_absolute_difference",
            ]
        ].to_string(index=False)
    )
    print(f"\nSaved estimates: {OUTPUT}")
    print(f"Saved pressure summary: {PRESSURE_OUTPUT}")
    print(f"Saved run summary: {RUN_SUMMARY}")
    print(
        "Metal changes remained unordered. No synthesis direction, p-value, "
        "model, pair reselection, or missing-value filling was used."
    )


if __name__ == "__main__":
    main()

