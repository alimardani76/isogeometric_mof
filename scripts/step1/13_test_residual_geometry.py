#!/usr/bin/env python3
"""Step 2 of 5: test residual geometry imbalance in Project 7.

The stringent pairs already satisfy all physical geometry limits. This script
checks whether the small geometry differences that remain are associated with
the observed direction-free adsorption magnitudes.

No pair is removed or reweighted. No p-value or predictive model is used. No
missing value is filled.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
INPUT = ANALYSIS / "final_primary_pair_effect_magnitudes.parquet"

GROUP_OUTPUT = ANALYSIS / "step2_residual_geometry_group_data.parquet"
RESULT_OUTPUT = ANALYSIS / "step2_residual_geometry_results.csv"
SUMMARY_OUTPUT = ANALYSIS / "step2_residual_geometry_summary.csv"

N_JOBS = 6
BOOTSTRAP_REPLICATES = 10_000
BASE_SEED = 1701

LIMITS = {
    "Di_diff": 0.03,
    "Df_diff": 0.03,
    "Dif_diff": 0.03,
    "Density_diff": 0.05,
    "UC_volume_diff": 0.05,
    "AVAf_diff": 0.03,
    "POAVAf_diff": 0.03,
}

EFFECTS = [
    "absolute_uptake_difference",
    "absolute_log_difference",
    "standardized_absolute_difference",
]


def spearman_no_p(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]
    if len(x) < 3 or np.all(x == x[0]) or np.all(y == y[0]):
        return np.nan
    return float(np.corrcoef(rankdata(x), rankdata(y))[0, 1])


def quartile_contrast(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]
    if len(x) < 8:
        return np.nan, 0, 0
    q1, q3 = np.quantile(x, [0.25, 0.75])
    low = y[x <= q1]
    high = y[x >= q3]
    if len(low) == 0 or len(high) == 0:
        return np.nan, len(low), len(high)
    return float(np.median(high) - np.median(low)), len(low), len(high)


def analyze_task(task):
    task_index, intervention, target, temperature, pressure, effect, part = task
    x = part["residual_geometry_score"].to_numpy(dtype=float)
    y = part[effect].to_numpy(dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]

    rho = spearman_no_p(x, y)
    contrast, low_n, high_n = quartile_contrast(x, y)

    rng = np.random.default_rng(BASE_SEED + task_index)
    rho_boot = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    contrast_boot = np.empty(BOOTSTRAP_REPLICATES, dtype=float)

    for index in range(BOOTSTRAP_REPLICATES):
        sample_index = rng.integers(0, len(x), size=len(x))
        sx = x[sample_index]
        sy = y[sample_index]
        rho_boot[index] = spearman_no_p(sx, sy)
        contrast_boot[index] = quartile_contrast(sx, sy)[0]

    rho_valid = rho_boot[np.isfinite(rho_boot)]
    contrast_valid = contrast_boot[np.isfinite(contrast_boot)]

    # The functional-motif class has only six independent groups. The
    # predeclared quartile contrast requires at least eight groups, so that
    # contrast is scientifically unavailable for this class. Preserve it as
    # missing rather than forcing a number or failing the complete audit.
    if len(rho_valid):
        rho_low = float(np.quantile(rho_valid, 0.025))
        rho_high = float(np.quantile(rho_valid, 0.975))
    else:
        rho_low = np.nan
        rho_high = np.nan

    if len(contrast_valid):
        contrast_low = float(np.quantile(contrast_valid, 0.025))
        contrast_high = float(np.quantile(contrast_valid, 0.975))
    else:
        contrast_low = np.nan
        contrast_high = np.nan

    return {
        "intervention": intervention,
        "target": target,
        "T/K": temperature,
        "p/bar": pressure,
        "effect_measure": effect,
        "groups": len(x),
        "spearman_rho": rho,
        "bootstrap_95_low_rho": rho_low,
        "bootstrap_95_high_rho": rho_high,
        "high_minus_low_geometry_quartile_median": contrast,
        "bootstrap_95_low_quartile_contrast": contrast_low,
        "bootstrap_95_high_quartile_contrast": contrast_high,
        "low_geometry_quartile_groups": low_n,
        "high_geometry_quartile_groups": high_n,
        "quartile_contrast_available": bool(len(x) >= 8),
    }


def main():
    if not INPUT.exists():
        raise FileNotFoundError(INPUT)

    data = pd.read_parquet(INPUT)
    data = data.loc[data["outcome_complete"]].copy()

    required = [
        "intervention",
        "dependence_family_id",
        "target",
        "T/K",
        "p/bar",
        "geometry_tier",
        "pair_lo",
        "evidence_unit_id",
        *LIMITS.keys(),
        *EFFECTS,
    ]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if not data["geometry_tier"].eq("stringent").all():
        raise RuntimeError("Input contains non-stringent pairs")

    normalized_columns = []
    for column, limit in LIMITS.items():
        output = f"fraction_of_limit_{column}"
        data[output] = data[column] / limit
        normalized_columns.append(output)

    if (data[normalized_columns] > 1 + 1e-12).any().any():
        raise RuntimeError("A stringent pair exceeds a declared geometry limit")

    data["residual_geometry_score"] = np.sqrt(
        np.mean(
            np.square(data[normalized_columns].to_numpy(dtype=float)),
            axis=1,
        )
    )
    data["maximum_fraction_of_geometry_limit"] = data[
        normalized_columns
    ].max(axis=1)

    aggregations = {
        "pair_rows": ("pair_lo", "size"),
        "distinct_comparisons": ("evidence_unit_id", "nunique"),
        "residual_geometry_score": ("residual_geometry_score", "median"),
        "maximum_fraction_of_geometry_limit": (
            "maximum_fraction_of_geometry_limit",
            "median",
        ),
    }
    for effect in EFFECTS:
        aggregations[effect] = (effect, "median")

    group_level = (
        data.groupby(
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
        .agg(**aggregations)
    )
    group_level.to_parquet(GROUP_OUTPUT, index=False)

    tasks = []
    task_index = 0
    for keys, part in group_level.groupby(
        ["intervention", "target", "T/K", "p/bar"],
        sort=False,
    ):
        intervention, target, temperature, pressure = keys
        for effect in EFFECTS:
            tasks.append(
                (
                    task_index,
                    intervention,
                    target,
                    temperature,
                    pressure,
                    effect,
                    part,
                )
            )
            task_index += 1

    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:
        results = list(executor.map(analyze_task, tasks))

    result = pd.DataFrame(results).sort_values(
        ["intervention", "effect_measure", "target", "T/K", "p/bar"]
    )

    result["rho_interval_excludes_zero"] = (
        (result["bootstrap_95_low_rho"] > 0)
        | (result["bootstrap_95_high_rho"] < 0)
    )
    result["quartile_interval_excludes_zero"] = (
        (result["bootstrap_95_low_quartile_contrast"] > 0)
        | (result["bootstrap_95_high_quartile_contrast"] < 0)
    )
    result.to_csv(RESULT_OUTPUT, index=False)

    summary = (
        result.groupby(["intervention", "effect_measure"], as_index=False)
        .agg(
            conditions=("target", "size"),
            median_absolute_rho=(
                "spearman_rho",
                lambda values: float(np.median(np.abs(values))),
            ),
            maximum_absolute_rho=(
                "spearman_rho",
                lambda values: float(np.max(np.abs(values))),
            ),
            positive_rho_intervals_excluding_zero=(
                "bootstrap_95_low_rho",
                lambda values: int((values > 0).sum()),
            ),
            negative_rho_intervals_excluding_zero=(
                "bootstrap_95_high_rho",
                lambda values: int((values < 0).sum()),
            ),
            quartile_intervals_excluding_zero=(
                "quartile_interval_excludes_zero",
                "sum",
            ),
        )
    )
    summary.to_csv(SUMMARY_OUTPUT, index=False)

    print(
        f"N_JOBS={N_JOBS}; bootstrap_replicates={BOOTSTRAP_REPLICATES}; "
        f"seed_base={BASE_SEED}; tasks={len(tasks)}"
    )
    print("\nRESIDUAL GEOMETRY SUMMARY")
    print(summary.to_string(index=False))

    unavailable = result.loc[~result["quartile_contrast_available"]]
    print("\nQUARTILE CONTRAST AVAILABILITY")
    if unavailable.empty:
        print("Available for all tasks")
    else:
        print(
            unavailable.groupby("intervention")
            .size()
            .rename("tasks_without_quartile_contrast")
            .to_string()
        )
        print(
            "Quartile contrasts require at least eight independent groups; "
            "unavailable values remain missing."
        )

    print("\nLARGEST ABSOLUTE CORRELATIONS")
    display = result.assign(abs_rho=result["spearman_rho"].abs()).sort_values(
        "abs_rho",
        ascending=False,
    ).head(20)
    print(
        display[
            [
                "intervention",
                "target",
                "T/K",
                "p/bar",
                "effect_measure",
                "groups",
                "spearman_rho",
                "bootstrap_95_low_rho",
                "bootstrap_95_high_rho",
                "high_minus_low_geometry_quartile_median",
            ]
        ].to_string(index=False)
    )

    print("\nOutputs:")
    print(GROUP_OUTPUT)
    print(RESULT_OUTPUT)
    print(SUMMARY_OUTPUT)
    print(
        "No pair was removed or reweighted. No p-value or predictive model "
        "was used. No missing value was filled."
    )


if __name__ == "__main__":
    main()

