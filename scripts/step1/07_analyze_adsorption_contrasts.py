#!/usr/bin/env python3
"""Correct Project 7 adsorption-effect scales without redefining any pair.

Why this exists
---------------
Earlier signed metal summaries used alphabetical element ordering. That sign was
reproducible bookkeeping but not a chemically justified substitution direction.
This script replaces that interpretation with unordered magnitudes.

Primary quantities
------------------
1. Absolute uptake difference, |q_B - q_A|, in mmol g^-1.
2. Absolute log-uptake difference,
   |log(q_B + epsilon) - log(q_A + epsilon)|.
3. Standardized absolute uptake difference within each adsorption condition,
   |q_B - q_A| divided by the robust scale of all ARC-MOF uptakes observed at
   that condition. The robust scale is IQR / 1.349.

Epsilon is frozen separately for each adsorption condition as one hundredth of
the smallest positive uptake observed in the full source file at that condition.
A sensitivity value using one thousandth of the same minimum is also reported.

Scientific boundaries
---------------------
- Uses the already frozen stringent pair table and corrected complete condition grid.
- Does not alter pair selection, chemistry classification, or geometry matching.
- Metal transitions remain unordered.
- Related comparisons are summarized together before overall summaries.
- No p-values, predictive models, or missing-value filling.
"""
from __future__ import annotations

from pathlib import Path
import gc
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
ANALYSIS = ROOT / "analysis"
INPUT = ANALYSIS / "stringent_pairs_with_adsorption.parquet"

CONDITION_SCALE_OUTPUT = ANALYSIS / "adsorption_condition_scales.csv"
PAIR_OUTPUT = ANALYSIS / "final_primary_pair_effect_magnitudes.parquet"
GROUP_OUTPUT = ANALYSIS / "corrected_group_effect_magnitudes.parquet"
SUMMARY_OUTPUT = ANALYSIS / "corrected_effect_magnitude_summary.csv"
PRESSURE_OUTPUT = ANALYSIS / "corrected_pressure_magnitude_summary.csv"
RUN_SUMMARY_OUTPUT = ANALYSIS / "corrected_effect_run_summary.csv"

N_JOBS = 1
CHUNK_SIZE = 250_000
BOOTSTRAP_REPLICATES = 10_000
RANDOM_SEED = 1701

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


def bootstrap_median(values, rng):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return np.nan, np.nan
    if len(values) == 1:
        return float(values[0]), float(values[0])
    estimates = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    for index in range(BOOTSTRAP_REPLICATES):
        sample = rng.choice(values, size=len(values), replace=True)
        estimates[index] = np.median(sample)
    low, high = np.quantile(estimates, [0.025, 0.975])
    return float(low), float(high)


def read_condition_scales():
    rows = []
    for filename, target in ADSORPTION_FILES.items():
        values_by_condition = {}
        for chunk in pd.read_csv(
            RAW / filename,
            usecols=["T/K", "p/bar", "mmol/g"],
            chunksize=CHUNK_SIZE,
        ):
            for column in ["T/K", "p/bar", "mmol/g"]:
                chunk[column] = pd.to_numeric(chunk[column], errors="coerce")
            chunk = chunk.dropna(subset=["T/K", "p/bar", "mmol/g"])
            for (temperature, pressure), part in chunk.groupby(["T/K", "p/bar"]):
                key = (float(temperature), float(pressure))
                values_by_condition.setdefault(key, []).append(
                    part["mmol/g"].to_numpy(dtype=float)
                )
        for (temperature, pressure), arrays in values_by_condition.items():
            values = np.concatenate(arrays)
            finite = values[np.isfinite(values)]
            positive = finite[finite > 0]
            if len(positive) == 0:
                raise RuntimeError(
                    f"No positive uptake for {target}, {temperature} K, {pressure} bar"
                )
            q1, q3 = np.quantile(finite, [0.25, 0.75])
            robust_scale = float((q3 - q1) / 1.349)
            if not np.isfinite(robust_scale) or robust_scale <= 0:
                raise RuntimeError(
                    f"Nonpositive robust scale for {target}, {temperature} K, {pressure} bar"
                )
            minimum_positive = float(positive.min())
            rows.append({
                "target": target,
                "T/K": temperature,
                "p/bar": pressure,
                "source_rows": len(finite),
                "minimum_positive_uptake": minimum_positive,
                "epsilon_primary": minimum_positive / 100.0,
                "epsilon_sensitivity": minimum_positive / 1000.0,
                "uptake_q1": float(q1),
                "uptake_q3": float(q3),
                "robust_scale_iqr_over_1_349": robust_scale,
            })
        print(f"condition scales calculated: {filename}")
        gc.collect()
    scales = pd.DataFrame(rows)
    if scales.duplicated(["target", "T/K", "p/bar"]).any():
        raise RuntimeError("Duplicate condition scales")
    expected = 2 * len(ADSORPTION_FILES)
    if len(scales) != expected:
        raise RuntimeError(f"Expected {expected} condition scales, found {len(scales)}")
    return scales


def main():
    if not INPUT.exists():
        raise FileNotFoundError(INPUT)

    data = pd.read_parquet(INPUT)
    scales = read_condition_scales()
    scales.to_csv(CONDITION_SCALE_OUTPUT, index=False)

    data = data.merge(
        scales,
        on=["target", "T/K", "p/bar"],
        how="left",
        validate="many_to_one",
    )
    if data["robust_scale_iqr_over_1_349"].isna().any():
        raise RuntimeError("Missing condition scale after merge")

    complete = data["outcome_complete"].copy()
    data["absolute_uptake_difference"] = (
        data["uptake_b"] - data["uptake_a"]
    ).abs().where(complete)

    data["absolute_log_difference"] = (
        np.log(data["uptake_b"] + data["epsilon_primary"])
        - np.log(data["uptake_a"] + data["epsilon_primary"])
    ).abs().where(complete)

    data["absolute_log_difference_sensitivity"] = (
        np.log(data["uptake_b"] + data["epsilon_sensitivity"])
        - np.log(data["uptake_a"] + data["epsilon_sensitivity"])
    ).abs().where(complete)

    data["standardized_absolute_difference"] = (
        data["absolute_uptake_difference"]
        / data["robust_scale_iqr_over_1_349"]
    ).where(complete)

    # Numerical safety. Uptakes must be nonnegative for the log transform.
    negative_uptakes = (
        data.loc[complete, "uptake_a"].lt(0).sum()
        + data.loc[complete, "uptake_b"].lt(0).sum()
    )
    if negative_uptakes:
        raise RuntimeError(f"Negative uptake values detected: {negative_uptakes}")

    data.to_parquet(PAIR_OUTPUT, index=False)

    # One value per connected group and condition. All chemistry transitions inside
    # a connected group are summarized before the group contributes to the main result.
    group_level = (
        data.loc[complete]
        .groupby(
            [
                "intervention",
                "dependence_family_id",
                "target",
                "T/K",
                "p/bar",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(
            raw_pair_rows=("pair_lo", "size"),
            distinct_comparisons=("evidence_unit_id", "nunique"),
            distinct_unordered_changes=("transition", "nunique"),
            absolute_uptake_difference=("absolute_uptake_difference", "median"),
            absolute_log_difference=("absolute_log_difference", "median"),
            absolute_log_difference_sensitivity=(
                "absolute_log_difference_sensitivity",
                "median",
            ),
            standardized_absolute_difference=(
                "standardized_absolute_difference",
                "median",
            ),
        )
    )
    group_level.to_parquet(GROUP_OUTPUT, index=False)

    rng = np.random.default_rng(RANDOM_SEED)
    summary_rows = []
    for keys, group in group_level.groupby(
        ["intervention", "target", "T/K", "p/bar"],
        sort=False,
    ):
        intervention, target, temperature, pressure = keys
        row = {
            "intervention": intervention,
            "target": target,
            "T/K": temperature,
            "p/bar": pressure,
            "groups_of_related_comparisons": group["dependence_family_id"].nunique(),
        }
        for column in [
            "absolute_uptake_difference",
            "absolute_log_difference",
            "absolute_log_difference_sensitivity",
            "standardized_absolute_difference",
        ]:
            values = group[column].to_numpy(dtype=float)
            low, high = bootstrap_median(values, rng)
            row[f"median_{column}"] = float(np.median(values))
            row[f"bootstrap_95_low_{column}"] = low
            row[f"bootstrap_95_high_{column}"] = high
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(SUMMARY_OUTPUT, index=False)

    # Low/high pressure comparison for the two scale-adjusted magnitudes.
    pressure_rows = []
    for keys, group in summary.groupby(["intervention", "target", "T/K"], sort=False):
        intervention, target, temperature = keys
        group = group.sort_values("p/bar")
        if len(group) != 2:
            raise RuntimeError(
                f"Expected two pressures for {intervention}, {target}, {temperature}"
            )
        low = group.iloc[0]
        high = group.iloc[1]
        pressure_rows.append({
            "intervention": intervention,
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

    run_summary = (
        pressure.groupby("intervention", as_index=False)
        .agg(
            pressure_comparisons=("target", "size"),
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
            maximum_epsilon_sensitivity_change_low=(
                "epsilon_sensitivity_change_low",
                "max",
            ),
            maximum_epsilon_sensitivity_change_high=(
                "epsilon_sensitivity_change_high",
                "max",
            ),
        )
    )
    run_summary.to_csv(RUN_SUMMARY_OUTPUT, index=False)

    print(
        f"N_JOBS={N_JOBS}; bootstrap_replicates={BOOTSTRAP_REPLICATES}; "
        f"seed={RANDOM_SEED}"
    )
    print("\nCORRECTED EFFECT SUMMARY")
    print(run_summary.to_string(index=False))
    print("\nPRESSURE RESULTS")
    print(
        pressure[
            [
                "intervention",
                "target",
                "T/K",
                "p/bar_low",
                "p/bar_high",
                "groups_low",
                "groups_high",
                "median_absolute_log_difference_low",
                "median_absolute_log_difference_high",
                "change_in_absolute_log_difference",
                "median_standardized_absolute_difference_low",
                "median_standardized_absolute_difference_high",
                "change_in_standardized_absolute_difference",
            ]
        ].to_string(index=False)
    )
    print("\nOutputs:")
    print(CONDITION_SCALE_OUTPUT)
    print(PAIR_OUTPUT)
    print(GROUP_OUTPUT)
    print(SUMMARY_OUTPUT)
    print(PRESSURE_OUTPUT)
    print(RUN_SUMMARY_OUTPUT)
    print("Metal changes remained unordered. No p-value or model was used. No missing value was filled.")


if __name__ == "__main__":
    main()

