#!/usr/bin/env python3
"""Compare adsorption magnitudes between the full-support and reciprocal matches.

The reciprocal pair set was created without adsorption outcomes. This script now
joins those selected pairs to the already corrected direction-free effect table
and compares pressure patterns with the full-support analysis.

No pair is reselected. Metal changes remain unordered. No p-values, predictive
models, or missing-value filling are used.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"

MATCH_FILE = ANALYSIS / "reciprocal_covariance_matched_pairs.parquet"
EFFECT_FILE = ANALYSIS / "final_primary_pair_effect_magnitudes.parquet"
FULL_METAL_FILE = ANALYSIS / "unordered_metal_change_pressure_summary.csv"
FULL_CLASS_FILE = ANALYSIS / "corrected_pressure_magnitude_summary.csv"

PAIR_OUTPUT = ANALYSIS / "reciprocal_pair_effect_magnitudes.parquet"
METAL_OUTPUT = ANALYSIS / "reciprocal_unordered_metal_magnitudes.csv"
METAL_PRESSURE_OUTPUT = ANALYSIS / "reciprocal_unordered_metal_pressure_summary.csv"
CLASS_OUTPUT = ANALYSIS / "reciprocal_class_magnitude_summary.csv"
CLASS_PRESSURE_OUTPUT = ANALYSIS / "reciprocal_class_pressure_summary.csv"
COMPARISON_OUTPUT = ANALYSIS / "matching_design_comparison.csv"
RUN_SUMMARY_OUTPUT = ANALYSIS / "matching_robustness_run_summary.csv"

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


def summarize_conditions(frame, group_columns, rng):
    rows = []
    for keys, group in frame.groupby(group_columns, sort=False, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_columns, keys))
        row["groups_of_related_comparisons"] = group[
            "dependence_family_id"
        ].nunique()
        row["selected_pairs"] = group["pair_lo"].nunique()
        for measure in MEASURES:
            values = group[measure].dropna().to_numpy(dtype=float)
            low, high = bootstrap_median(values, rng)
            row[f"median_{measure}"] = float(np.median(values))
            row[f"bootstrap_95_low_{measure}"] = low
            row[f"bootstrap_95_high_{measure}"] = high
        rows.append(row)
    return pd.DataFrame(rows)


def pressure_table(summary, identity_columns):
    rows = []
    grouping = [*identity_columns, "target", "T/K"]
    for keys, group in summary.groupby(grouping, sort=False, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        group = group.sort_values("p/bar")
        if len(group) != 2:
            raise RuntimeError(
                f"Expected two pressure rows for {dict(zip(grouping, keys))}"
            )
        low, high = group.iloc[0], group.iloc[1]
        row = dict(zip(grouping, keys))
        row.update({
            "p/bar_low": low["p/bar"],
            "p/bar_high": high["p/bar"],
            "groups_low": low["groups_of_related_comparisons"],
            "groups_high": high["groups_of_related_comparisons"],
            "selected_pairs_low": low["selected_pairs"],
            "selected_pairs_high": high["selected_pairs"],
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
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    for path in [MATCH_FILE, EFFECT_FILE, FULL_METAL_FILE, FULL_CLASS_FILE]:
        if not path.exists():
            raise FileNotFoundError(path)

    matches = pd.read_parquet(MATCH_FILE)
    effects = pd.read_parquet(EFFECT_FILE)

    key = ["intervention", "pair_lo", "pair_hi"]
    if matches[key].duplicated().any():
        raise RuntimeError("Duplicate selected pair keys")

    effect_columns = [
        *key,
        "target",
        "T/K",
        "p/bar",
        "outcome_complete",
        "dependence_family_id",
        "transition",
        *MEASURES,
    ]
    effect_subset = effects[effect_columns].copy()

    selected = matches.merge(
        effect_subset,
        on=key,
        how="left",
        validate="one_to_many",
        suffixes=("", "_effect"),
    )

    # The selected-pair metadata and effect table must agree.
    if not selected["transition"].eq(selected["transition_effect"]).all():
        raise RuntimeError("Transition mismatch after effect merge")
    if not selected["dependence_family_id"].eq(
        selected["dependence_family_id_effect"]
    ).all():
        raise RuntimeError("Related-comparison group mismatch after merge")

    selected = selected.drop(
        columns=["transition_effect", "dependence_family_id_effect"]
    )

    expected_rows = len(matches) * 18
    if len(selected) != expected_rows:
        raise RuntimeError(
            f"Expected {expected_rows} selected pair-condition rows, found {len(selected)}"
        )

    selected.to_parquet(PAIR_OUTPUT, index=False)
    complete = selected.loc[selected["outcome_complete"]].copy()

    rng = np.random.default_rng(RANDOM_SEED)

    # Exact unordered metal changes. Reciprocal matching is non-overlapping within
    # each exact change, but related-comparison groups are still retained for a
    # conservative uncertainty summary.
    metal = complete.loc[
        complete["intervention"].eq("metal_substitution")
    ].copy()
    metal_support = metal.groupby("transition")[
        "dependence_family_id"
    ].nunique()
    retained_metal = set(metal_support[metal_support >= MIN_GROUPS].index)
    metal = metal.loc[metal["transition"].isin(retained_metal)].copy()

    metal_group = (
        metal.groupby(
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
            pair_lo=("pair_lo", "first"),
            pair_count=("pair_lo", "nunique"),
            **{measure: (measure, "median") for measure in MEASURES},
        )
    )

    metal_summary = summarize_conditions(
        metal_group,
        ["transition", "target", "T/K", "p/bar"],
        rng,
    )
    metal_summary.to_csv(METAL_OUTPUT, index=False)
    metal_pressure = pressure_table(metal_summary, ["transition"])
    metal_pressure.to_csv(METAL_PRESSURE_OUTPUT, index=False)

    # Class summaries. Connected groups are still collapsed first because the
    # reciprocal rule was applied within exact chemistry changes, not globally
    # across all different changes in one intervention class.
    class_group = (
        complete.groupby(
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
            pair_lo=("pair_lo", "first"),
            pair_count=("pair_lo", "nunique"),
            **{measure: (measure, "median") for measure in MEASURES},
        )
    )

    class_summary = summarize_conditions(
        class_group,
        ["intervention", "target", "T/K", "p/bar"],
        rng,
    )
    class_summary.to_csv(CLASS_OUTPUT, index=False)
    class_pressure = pressure_table(class_summary, ["intervention"])
    class_pressure.to_csv(CLASS_PRESSURE_OUTPUT, index=False)

    # Compare pressure-direction conclusions with the full-support outputs.
    full_metal = pd.read_csv(FULL_METAL_FILE, low_memory=False)
    full_class = pd.read_csv(FULL_CLASS_FILE, low_memory=False)

    metal_compare = full_metal.merge(
        metal_pressure,
        on=["transition", "target", "T/K"],
        how="inner",
        suffixes=("_full", "_reciprocal"),
        validate="one_to_one",
    )
    metal_compare["analysis_level"] = "exact_unordered_metal_change"
    metal_compare["same_log_pressure_direction"] = (
        np.sign(metal_compare["change_in_absolute_log_difference_full"])
        == np.sign(metal_compare["change_in_absolute_log_difference_reciprocal"])
    )
    metal_compare["same_standardized_pressure_direction"] = (
        np.sign(metal_compare["change_in_standardized_absolute_difference_full"])
        == np.sign(metal_compare["change_in_standardized_absolute_difference_reciprocal"])
    )

    class_compare = full_class.merge(
        class_pressure,
        on=["intervention", "target", "T/K"],
        how="inner",
        suffixes=("_full", "_reciprocal"),
        validate="one_to_one",
    )
    class_compare["analysis_level"] = "intervention_class"
    class_compare["same_log_pressure_direction"] = (
        np.sign(class_compare["change_in_absolute_log_difference_full"])
        == np.sign(class_compare["change_in_absolute_log_difference_reciprocal"])
    )
    class_compare["same_standardized_pressure_direction"] = (
        np.sign(class_compare["change_in_standardized_absolute_difference_full"])
        == np.sign(class_compare["change_in_standardized_absolute_difference_reciprocal"])
    )

    comparison = pd.concat(
        [metal_compare, class_compare],
        ignore_index=True,
        sort=False,
    )
    comparison.to_csv(COMPARISON_OUTPUT, index=False)

    run_rows = []
    for level, group in comparison.groupby("analysis_level", sort=False):
        run_rows.append({
            "analysis_level": level,
            "comparisons": len(group),
            "same_log_pressure_direction": int(
                group["same_log_pressure_direction"].sum()
            ),
            "same_standardized_pressure_direction": int(
                group["same_standardized_pressure_direction"].sum()
            ),
            "maximum_absolute_change_in_log_pressure_contrast": float(
                (
                    group["change_in_absolute_log_difference_reciprocal"]
                    - group["change_in_absolute_log_difference_full"]
                ).abs().max()
            ),
            "maximum_absolute_change_in_standardized_pressure_contrast": float(
                (
                    group["change_in_standardized_absolute_difference_reciprocal"]
                    - group["change_in_standardized_absolute_difference_full"]
                ).abs().max()
            ),
        })
    run_summary = pd.DataFrame(run_rows)
    run_summary.to_csv(RUN_SUMMARY_OUTPUT, index=False)

    print(
        f"N_JOBS={N_JOBS}; bootstrap_replicates={BOOTSTRAP_REPLICATES}; "
        f"seed={RANDOM_SEED}; selected_pairs={len(matches):,}; "
        f"pair_condition_rows={len(selected):,}"
    )
    print("\nMATCHING ROBUSTNESS SUMMARY")
    print(run_summary.to_string(index=False))

    print("\nEXACT METAL-CHANGE PRESSURE COUNTS")
    metal_counts = (
        metal_pressure.groupby("transition", as_index=False)
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
        )
    )
    print(metal_counts.to_string(index=False))

    print("\nCLASS-LEVEL PRESSURE COUNTS")
    class_counts = (
        class_pressure.groupby("intervention", as_index=False)
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
        )
    )
    print(class_counts.to_string(index=False))

    incomplete = selected.loc[~selected["outcome_complete"]]
    print(f"\nIncomplete selected pair-condition rows: {len(incomplete):,}")
    print("\nOutputs:")
    for path in [
        PAIR_OUTPUT,
        METAL_OUTPUT,
        METAL_PRESSURE_OUTPUT,
        CLASS_OUTPUT,
        CLASS_PRESSURE_OUTPUT,
        COMPARISON_OUTPUT,
        RUN_SUMMARY_OUTPUT,
    ]:
        print(path)
    print(
        "The reciprocal set was selected without adsorption outcomes. Metal changes "
        "remained unordered. No p-value, predictive model, pair reselection, or "
        "missing-value filling was used."
    )


if __name__ == "__main__":
    main()

