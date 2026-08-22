#!/usr/bin/env python3
"""Build one non-overlapping covariance-aware matched set for Project 7.

Purpose
-------
This is a robustness check for the existing full-support stringent analysis. It
keeps the same chemistry rules and the same stringent physical geometry limits,
but selects reciprocal nearest neighbours using a shrinkage-Mahalanobis distance.
No adsorption outcome is read or used.

Design
------
1. Start from the already accepted stringent pair table.
2. Fit robust geometry scaling on the full 177,869-framework chemistry-supported
   cohort, without using adsorption outcomes.
3. Estimate a Ledoit-Wolf shrinkage covariance matrix in that scaled geometry space.
4. Calculate a covariance-aware distance for every accepted pair.
5. Within each exact unordered chemistry change, retain only reciprocal nearest
   neighbours. An explicit clean/freeONLY framework variant can be used at most
   once within that exact chemistry change.

This does not replace the full-support analysis. It creates an independent
robustness set whose conclusions will be compared with the existing result.
"""
from __future__ import annotations

from pathlib import Path
import json
import platform
import sys

import numpy as np
import pandas as pd
import sklearn
from sklearn.covariance import LedoitWolf


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"

MASTER_FILE = ANALYSIS / "framework_master.parquet"
PAIR_FILE = ANALYSIS / "stringent_pair_dependence_ledger.parquet"

OUTPUT_FILE = ANALYSIS / "reciprocal_covariance_matched_pairs.parquet"
SUMMARY_FILE = ANALYSIS / "reciprocal_covariance_matching_summary.csv"
TRANSITION_FILE = ANALYSIS / "reciprocal_covariance_transition_support.csv"
SCALE_FILE = ANALYSIS / "reciprocal_covariance_geometry_scaling.csv"
PRECISION_FILE = ANALYSIS / "reciprocal_covariance_precision_matrix.csv"
RUN_FILE = ANALYSIS / "reciprocal_covariance_run_manifest.json"

N_JOBS = 1

GEOMETRY_COLUMNS = [
    "Di",
    "Df",
    "Dif",
    "Density",
    "UC_volume",
    "AVAf",
    "POAVAf",
]

# Unit-cell volume is log-transformed only for covariance-distance estimation.
# The original stringent physical limits remain unchanged and were already
# applied before this script.
TRANSFORMED_COLUMNS = [
    "Di",
    "Df",
    "Dif",
    "Density",
    "log_UC_volume",
    "AVAf",
    "POAVAf",
]


def robust_geometry_table(master: pd.DataFrame):
    geometry = master[["mof_id", *GEOMETRY_COLUMNS]].copy()

    if geometry[GEOMETRY_COLUMNS].isna().any().any():
        missing = geometry[GEOMETRY_COLUMNS].isna().sum()
        raise RuntimeError(
            "Missing geometry in chemistry-supported cohort:\n"
            + missing[missing > 0].to_string()
        )

    if (geometry["UC_volume"] <= 0).any():
        raise RuntimeError("Nonpositive unit-cell volume prevents log transform")

    transformed = geometry[["mof_id"]].copy()
    transformed["Di"] = geometry["Di"]
    transformed["Df"] = geometry["Df"]
    transformed["Dif"] = geometry["Dif"]
    transformed["Density"] = geometry["Density"]
    transformed["log_UC_volume"] = np.log(geometry["UC_volume"])
    transformed["AVAf"] = geometry["AVAf"]
    transformed["POAVAf"] = geometry["POAVAf"]

    medians = transformed[TRANSFORMED_COLUMNS].median()
    q1 = transformed[TRANSFORMED_COLUMNS].quantile(0.25)
    q3 = transformed[TRANSFORMED_COLUMNS].quantile(0.75)
    iqr = q3 - q1

    zero_iqr = iqr[iqr <= 0]
    if not zero_iqr.empty:
        raise RuntimeError(
            "Zero or negative IQR in geometry variables:\n"
            + zero_iqr.to_string()
        )

    scaled = (
        transformed[TRANSFORMED_COLUMNS] - medians
    ) / iqr

    scale_table = pd.DataFrame(
        {
            "variable": TRANSFORMED_COLUMNS,
            "median": medians.values,
            "q1": q1.values,
            "q3": q3.values,
            "iqr": iqr.values,
        }
    )

    return transformed[["mof_id"]].join(scaled), scale_table


def calculate_pair_distances(
    pairs: pd.DataFrame,
    scaled_geometry: pd.DataFrame,
    precision: np.ndarray,
):
    geometry_index = scaled_geometry.set_index("mof_id")

    missing_a = set(pairs["id_a"]) - set(geometry_index.index)
    missing_b = set(pairs["id_b"]) - set(geometry_index.index)
    if missing_a or missing_b:
        raise RuntimeError(
            f"Pair endpoints missing scaled geometry: "
            f"A={len(missing_a)}, B={len(missing_b)}"
        )

    a = geometry_index.loc[
        pairs["id_a"], TRANSFORMED_COLUMNS
    ].to_numpy(dtype=float)
    b = geometry_index.loc[
        pairs["id_b"], TRANSFORMED_COLUMNS
    ].to_numpy(dtype=float)

    difference = a - b
    squared = np.einsum(
        "ij,jk,ik->i",
        difference,
        precision,
        difference,
    )

    if (squared < -1e-10).any():
        raise RuntimeError("Negative squared Mahalanobis distance")

    pairs = pairs.copy()
    pairs["covariance_distance"] = np.sqrt(
        np.maximum(squared, 0.0)
    )
    return pairs


def select_reciprocal_pairs(group: pd.DataFrame):
    """Select mutual nearest edges on normalized framework-variant nodes."""
    # Multiple raw records may represent the same normalized variant pair.
    # Keep the shortest edge, with pair IDs as deterministic tie-breakers.
    edges = (
        group.sort_values(
            [
                "covariance_distance",
                "pair_lo",
                "pair_hi",
            ]
        )
        .drop_duplicates(
            ["variant_lo", "variant_hi"],
            keep="first",
        )
        .copy()
    )

    nearest = {}

    for row in edges.itertuples(index=False):
        candidates = [
            (
                row.variant_lo,
                row.variant_hi,
                row.covariance_distance,
                row.pair_lo,
                row.pair_hi,
            ),
            (
                row.variant_hi,
                row.variant_lo,
                row.covariance_distance,
                row.pair_lo,
                row.pair_hi,
            ),
        ]

        for node, partner, distance, pair_lo, pair_hi in candidates:
            key = (
                float(distance),
                str(partner),
                str(pair_lo),
                str(pair_hi),
            )
            previous = nearest.get(node)
            if previous is None or key < previous[0]:
                nearest[node] = (key, partner)

    accepted_indices = []

    for index, row in edges.iterrows():
        nearest_a = nearest.get(row["variant_lo"])
        nearest_b = nearest.get(row["variant_hi"])

        if nearest_a is None or nearest_b is None:
            continue

        if (
            nearest_a[1] == row["variant_hi"]
            and nearest_b[1] == row["variant_lo"]
        ):
            accepted_indices.append(index)

    selected = edges.loc[accepted_indices].copy()

    # Mutual-nearest matching must be non-overlapping within this exact change.
    endpoints = pd.concat(
        [selected["variant_lo"], selected["variant_hi"]],
        ignore_index=True,
    )
    if endpoints.duplicated().any():
        raise RuntimeError(
            "Reciprocal matching produced repeated framework variants "
            "within one exact chemistry change"
        )

    return selected


def main():
    if not MASTER_FILE.exists():
        raise FileNotFoundError(MASTER_FILE)
    if not PAIR_FILE.exists():
        raise FileNotFoundError(PAIR_FILE)

    master = pd.read_parquet(MASTER_FILE)
    master = master.loc[
        master["chemistry_verification_eligible"]
    ].copy()

    pairs = pd.read_parquet(PAIR_FILE)

    if not pairs["geometry_tier"].eq("stringent").all():
        raise RuntimeError("Input pair table contains non-stringent rows")

    required_pair_columns = [
        "id_a",
        "id_b",
        "pair_lo",
        "pair_hi",
        "variant_lo",
        "variant_hi",
        "intervention",
        "transition",
    ]
    missing = [
        column
        for column in required_pair_columns
        if column not in pairs.columns
    ]
    if missing:
        raise ValueError(f"Missing pair columns: {missing}")

    scaled_geometry, scale_table = robust_geometry_table(master)
    scale_table.to_csv(SCALE_FILE, index=False)

    model = LedoitWolf(
        assume_centered=False,
        store_precision=True,
    )
    model.fit(
        scaled_geometry[TRANSFORMED_COLUMNS].to_numpy(dtype=float)
    )

    precision = model.precision_
    precision_table = pd.DataFrame(
        precision,
        index=TRANSFORMED_COLUMNS,
        columns=TRANSFORMED_COLUMNS,
    )
    precision_table.to_csv(PRECISION_FILE)

    pairs = calculate_pair_distances(
        pairs,
        scaled_geometry,
        precision,
    )

    selected_parts = []

    for _, group in pairs.groupby(
        ["intervention", "transition"],
        sort=False,
        dropna=False,
    ):
        selected = select_reciprocal_pairs(group)
        if not selected.empty:
            selected_parts.append(selected)

    if not selected_parts:
        raise RuntimeError("No reciprocal pairs were selected")

    selected = pd.concat(
        selected_parts,
        ignore_index=True,
        sort=False,
    )
    selected["robustness_design"] = (
        "reciprocal_nearest_shrinkage_mahalanobis"
    )

    if selected[
        ["intervention", "transition", "variant_lo", "variant_hi"]
    ].duplicated().any():
        raise RuntimeError("Duplicate selected normalized pairs")

    selected.to_parquet(OUTPUT_FILE, index=False)

    summary = (
        pairs.groupby("intervention", as_index=False)
        .agg(
            eligible_stringent_pairs=("pair_lo", "size"),
            eligible_exact_changes=("transition", "nunique"),
            eligible_framework_variants=(
                "variant_lo",
                lambda values: len(set(values)),
            ),
        )
    )

    selected_summary = (
        selected.groupby("intervention", as_index=False)
        .agg(
            selected_pairs=("pair_lo", "size"),
            selected_exact_changes=("transition", "nunique"),
            median_covariance_distance=(
                "covariance_distance",
                "median",
            ),
            maximum_covariance_distance=(
                "covariance_distance",
                "max",
            ),
        )
    )

    summary = summary.merge(
        selected_summary,
        on="intervention",
        how="left",
        validate="one_to_one",
    )
    summary["selected_fraction"] = (
        summary["selected_pairs"]
        / summary["eligible_stringent_pairs"]
    )
    summary.to_csv(SUMMARY_FILE, index=False)

    transition_support = (
        selected.groupby(
            ["intervention", "transition"],
            as_index=False,
        )
        .agg(
            selected_pairs=("pair_lo", "size"),
            unique_variant_endpoints=(
                "variant_lo",
                lambda values: len(set(values)),
            ),
            median_covariance_distance=(
                "covariance_distance",
                "median",
            ),
            maximum_covariance_distance=(
                "covariance_distance",
                "max",
            ),
        )
        .sort_values(
            ["intervention", "selected_pairs"],
            ascending=[True, False],
        )
    )

    # Correct the endpoint count using both columns.
    endpoint_counts = []
    for (intervention, transition), group in selected.groupby(
        ["intervention", "transition"],
        sort=False,
    ):
        endpoint_counts.append(
            {
                "intervention": intervention,
                "transition": transition,
                "unique_variant_endpoints": len(
                    set(group["variant_lo"])
                    | set(group["variant_hi"])
                ),
            }
        )
    endpoint_counts = pd.DataFrame(endpoint_counts)
    transition_support = transition_support.drop(
        columns=["unique_variant_endpoints"]
    ).merge(
        endpoint_counts,
        on=["intervention", "transition"],
        how="left",
        validate="one_to_one",
    )
    transition_support.to_csv(TRANSITION_FILE, index=False)

    manifest = {
        "script": Path(__file__).name,
        "python": sys.version,
        "platform": platform.platform(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
        "n_jobs": N_JOBS,
        "input_master": str(MASTER_FILE),
        "input_pairs": str(PAIR_FILE),
        "chemistry_supported_frameworks": int(len(master)),
        "eligible_stringent_pairs": int(len(pairs)),
        "selected_pairs": int(len(selected)),
        "distance": "Ledoit-Wolf shrinkage Mahalanobis",
        "scaling": "median and IQR on full chemistry-supported cohort",
        "unit_cell_volume_transform": "natural log",
        "selection": "reciprocal nearest neighbours within exact unordered chemistry change",
        "adsorption_outcomes_used": False,
        "missing_values_filled": False,
    }
    RUN_FILE.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print(
        f"N_JOBS={N_JOBS}; chemistry_supported_frameworks={len(master):,}; "
        f"eligible_stringent_pairs={len(pairs):,}; selected_pairs={len(selected):,}"
    )
    print("\nMATCHING SUMMARY")
    print(summary.to_string(index=False))
    print("\nMOST SUPPORTED SELECTED CHANGES")
    print(
        transition_support.groupby(
            "intervention",
            group_keys=False,
        )
        .head(15)
        .to_string(index=False)
    )
    print("\nOutputs:")
    print(OUTPUT_FILE)
    print(SUMMARY_FILE)
    print(TRANSITION_FILE)
    print(SCALE_FILE)
    print(PRECISION_FILE)
    print(RUN_FILE)
    print(
        "Adsorption outcomes were not read. Existing stringent limits and "
        "chemistry classifications were not changed. No missing value was filled."
    )


if __name__ == "__main__":
    main()

