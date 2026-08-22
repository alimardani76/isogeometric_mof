#!/usr/bin/env python3
"""Step 3a of 5: construct an outcome-blind same-chemistry control set.

Purpose
-------
Build geometrically close framework pairs that do not contain the defined metal,
linker, or functional-motif change. These controls estimate the adsorption
separation observed between close frameworks when the chemistry representation
used by Project 7 is held fixed.

This stage reads no adsorption outcome. It does not replace the primary matched
pairs. It creates a baseline for Step 3b.

Control definition
------------------
Both frameworks must have:
- the same topology and dimensionality;
- the same actual metal composition;
- the same metal, linker, and functional cluster assignments;
- metal multiplicity agreeing within 5%;
- all seven measured geometry differences inside the primary limits.

Within each exact chemistry/structure context, reciprocal nearest neighbours are
selected using the existing Ledoit-Wolf covariance-aware geometry distance.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import json
import platform
import sys

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
MASTER_FILE = ANALYSIS / "framework_master.parquet"
CHEMISTRY_FILE = ANALYSIS / "cif_chemistry.parquet"
SCALING_FILE = ANALYSIS / "reciprocal_covariance_geometry_scaling.csv"
PRECISION_FILE = ANALYSIS / "reciprocal_covariance_precision_matrix.csv"

OUTPUT_FILE = ANALYSIS / "step3_same_chemistry_control_pairs.parquet"
SUMMARY_FILE = ANALYSIS / "step3_same_chemistry_control_summary.csv"
CONTEXT_FILE = ANALYSIS / "step3_same_chemistry_control_contexts.csv"
RUN_FILE = ANALYSIS / "step3_same_chemistry_control_manifest.json"

N_JOBS = 6
QUERY_NEIGHBOURS = 32
NUMERICAL_TOLERANCE = 1e-12
METAL_MULTIPLICITY_RATIO_LIMIT = 1.05

GEOMETRY = ["Di", "Df", "Dif", "Density", "UC_volume", "AVAf", "POAVAf"]
TRANSFORMED = ["Di", "Df", "Dif", "Density", "log_UC_volume", "AVAf", "POAVAf"]
LIMITS = {
    "Di": 0.03,
    "Df": 0.03,
    "Dif": 0.03,
    "Density": 0.05,
    "UC_volume": 0.05,
    "AVAf": 0.03,
    "POAVAf": 0.03,
}
CONTEXT = [
    "topology",
    "Dimensionality",
    "metals",
    "metal_cluster",
    "linker_cluster",
    "functional_cluster",
]


def rel_diff(a, b):
    denominator = (abs(a) + abs(b)) / 2.0
    return abs(a - b) / denominator if denominator > 0 else 0.0


def pair_differences(a, b):
    return {
        "Di_diff": rel_diff(a["Di"], b["Di"]),
        "Df_diff": rel_diff(a["Df"], b["Df"]),
        "Dif_diff": rel_diff(a["Dif"], b["Dif"]),
        "Density_diff": rel_diff(a["Density"], b["Density"]),
        "UC_volume_diff": rel_diff(a["UC_volume"], b["UC_volume"]),
        "AVAf_diff": abs(a["AVAf"] - b["AVAf"]),
        "POAVAf_diff": abs(a["POAVAf"] - b["POAVAf"]),
    }


def passes_primary(differences):
    return (
        differences["Di_diff"] <= LIMITS["Di"] + NUMERICAL_TOLERANCE
        and differences["Df_diff"] <= LIMITS["Df"] + NUMERICAL_TOLERANCE
        and differences["Dif_diff"] <= LIMITS["Dif"] + NUMERICAL_TOLERANCE
        and differences["Density_diff"] <= LIMITS["Density"] + NUMERICAL_TOLERANCE
        and differences["UC_volume_diff"] <= LIMITS["UC_volume"] + NUMERICAL_TOLERANCE
        and differences["AVAf_diff"] <= LIMITS["AVAf"] + NUMERICAL_TOLERANCE
        and differences["POAVAf_diff"] <= LIMITS["POAVAf"] + NUMERICAL_TOLERANCE
    )


def multiplicity_ratio(a, b):
    low = min(a, b)
    return max(a, b) / low if low > 0 else np.inf


def prepare_coordinates(group, medians, iqrs, factor):
    transformed = np.column_stack(
        [
            group["Di"].to_numpy(float),
            group["Df"].to_numpy(float),
            group["Dif"].to_numpy(float),
            group["Density"].to_numpy(float),
            np.log(group["UC_volume"].to_numpy(float)),
            group["AVAf"].to_numpy(float),
            group["POAVAf"].to_numpy(float),
        ]
    )
    scaled = (transformed - medians) / iqrs
    return scaled @ factor


def process_context(payload):
    context_id, group, medians, iqrs, factor = payload
    n = len(group)
    if n < 2:
        return {"context_id": context_id, "context_size": n, "pairs": []}

    group = group.reset_index(drop=True)
    coords = prepare_coordinates(group, medians, iqrs, factor)
    tree = cKDTree(coords)

    nearest = {}
    nearest_distance = {}
    nearest_differences = {}

    records = group.to_dict("records")

    for i in range(n):
        searched = 1
        query_size = min(QUERY_NEIGHBOURS + 1, n)

        while searched < n:
            distances, neighbours = tree.query(
                coords[i],
                k=query_size,
            )

            distances = np.atleast_1d(distances)
            neighbours = np.atleast_1d(neighbours)

            found = False

            for position in range(searched, len(neighbours)):
                j = int(neighbours[position])

                if i == j:
                    continue

                a = records[i]
                b = records[j]

                if (
                    multiplicity_ratio(
                        a["metal_site_count"],
                        b["metal_site_count"],
                    )
                    > METAL_MULTIPLICITY_RATIO_LIMIT
                ):
                    continue

                differences = pair_differences(a, b)

                if not passes_primary(differences):
                    continue

                nearest[i] = j
                nearest_distance[i] = float(
                    distances[position]
                )
                nearest_differences[i] = differences
                found = True
                break

            if found or query_size == n:
                break

            searched = query_size
            query_size = min(query_size * 2, n)

    pairs = []
    used = set()
    for i, j in nearest.items():
        if i in used or j in used:
            continue
        if nearest.get(j) != i:
            continue
        lo, hi = sorted([i, j])
        if lo in used or hi in used:
            continue
        a, b = records[lo], records[hi]
        differences = pair_differences(a, b)
        id_lo, id_hi = sorted([a["mof_id"], b["mof_id"]])
        pairs.append(
            {
                "control_pair_lo": id_lo,
                "control_pair_hi": id_hi,
                "id_a": a["mof_id"],
                "id_b": b["mof_id"],
                "context_id": context_id,
                "topology": a["topology"],
                "Dimensionality": a["Dimensionality"],
                "metals": a["metals"],
                "metal_cluster": a["metal_cluster"],
                "linker_cluster": a["linker_cluster"],
                "functional_cluster": a["functional_cluster"],
                "metal_site_count_a": a["metal_site_count"],
                "metal_site_count_b": b["metal_site_count"],
                "metal_multiplicity_ratio": multiplicity_ratio(
                    a["metal_site_count"], b["metal_site_count"]
                ),
                "covariance_distance": nearest_distance[lo],
                **differences,
            }
        )
        used.update([lo, hi])

    return {"context_id": context_id, "context_size": n, "pairs": pairs}


def main():
    for path in [MASTER_FILE, CHEMISTRY_FILE, SCALING_FILE, PRECISION_FILE]:
        if not path.exists():
            raise FileNotFoundError(path)

    master = pd.read_parquet(MASTER_FILE)
    master = master.loc[master["chemistry_verification_eligible"]].copy()
    chemistry = pd.read_parquet(
        CHEMISTRY_FILE,
        columns=["mof_id", "parse_ok", "metals", "metal_site_count"],
    )
    frame = master.merge(
        chemistry,
        on="mof_id",
        how="left",
        validate="one_to_one",
    )
    frame = frame.loc[frame["parse_ok"].fillna(False)].copy()

    required = ["mof_id", *CONTEXT, "metal_site_count", *GEOMETRY]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if frame[required].isna().any().any():
        counts = frame[required].isna().sum()
        raise RuntimeError(
            "Missing values in control construction columns:\n"
            + counts[counts > 0].to_string()
        )
    if (frame["UC_volume"] <= 0).any():
        raise RuntimeError("Nonpositive unit-cell volume")

    scaling = pd.read_csv(SCALING_FILE).set_index("variable").loc[TRANSFORMED]
    medians = scaling["median"].to_numpy(float)
    iqrs = scaling["iqr"].to_numpy(float)
    precision = pd.read_csv(PRECISION_FILE, index_col=0).loc[TRANSFORMED, TRANSFORMED].to_numpy(float)

    # If P = L L^T, then (x-y)P(x-y)^T = ||(x-y)L||^2.
    factor = np.linalg.cholesky(precision)

    payloads = []
    context_rows = []
    for context_id, (keys, group) in enumerate(
        frame.groupby(CONTEXT, sort=False, dropna=False)
    ):
        if len(group) < 2:
            continue
        payloads.append(
            (
                context_id,
                group[required].copy(),
                medians,
                iqrs,
                factor,
            )
        )
        context_rows.append(
            {
                "context_id": context_id,
                **dict(zip(CONTEXT, keys if isinstance(keys, tuple) else (keys,))),
                "frameworks": len(group),
            }
        )

    print(
        f"N_JOBS={N_JOBS}; frameworks={len(frame):,}; "
        f"eligible_contexts={len(payloads):,}; query_neighbours={QUERY_NEIGHBOURS}"
    )

    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:
        results = list(executor.map(process_context, payloads, chunksize=25))

    pair_rows = [pair for result in results for pair in result["pairs"]]
    controls = pd.DataFrame(pair_rows)
    if controls.empty:
        raise RuntimeError("No same-chemistry controls were found")
    if controls[["control_pair_lo", "control_pair_hi"]].duplicated().any():
        raise RuntimeError("Duplicate unordered control pairs")

    controls.to_parquet(OUTPUT_FILE, index=False)
    contexts = pd.DataFrame(context_rows)
    produced = pd.DataFrame(
        {
            "context_id": [result["context_id"] for result in results],
            "control_pairs": [len(result["pairs"]) for result in results],
        }
    )
    contexts = contexts.merge(
        produced,
        on="context_id",
        how="left",
        validate="one_to_one",
    )
    contexts.to_csv(CONTEXT_FILE, index=False)

    summary = pd.DataFrame(
        [
            ("chemistry_supported_frameworks", len(frame)),
            ("eligible_exact_chemistry_contexts", len(contexts)),
            ("contexts_with_control_pairs", int(contexts["control_pairs"].gt(0).sum())),
            ("same_chemistry_control_pairs", len(controls)),
            ("unique_control_frameworks", len(set(controls["id_a"]) | set(controls["id_b"]))),
            ("topologies", controls["topology"].nunique(dropna=True)),
            ("metal_compositions", controls["metals"].nunique(dropna=True)),
            ("median_covariance_distance", controls["covariance_distance"].median()),
            ("maximum_covariance_distance", controls["covariance_distance"].max()),
        ],
        columns=["metric", "value"],
    )
    summary.to_csv(SUMMARY_FILE, index=False)

    manifest = {
        "script": Path(__file__).name,
        "python": sys.version,
        "platform": platform.platform(),
        "n_jobs": N_JOBS,
        "query_neighbours": QUERY_NEIGHBOURS,
        "numerical_tolerance": NUMERICAL_TOLERANCE,
        "metal_multiplicity_ratio_limit": METAL_MULTIPLICITY_RATIO_LIMIT,
        "chemistry_context": CONTEXT,
        "geometry_limits": LIMITS,
        "adsorption_outcomes_used": False,
        "missing_values_filled": False,
        "control_pairs": int(len(controls)),
    }
    RUN_FILE.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("\nSAME-CHEMISTRY CONTROL SUMMARY")
    print(summary.to_string(index=False))
    print("\nCONTROL PAIRS BY METAL COMPOSITION")
    print(controls["metals"].value_counts().head(20).to_string())
    print("\nOutputs:")
    print(OUTPUT_FILE)
    print(SUMMARY_FILE)
    print(CONTEXT_FILE)
    print(RUN_FILE)
    print(
        "Adsorption outcomes were not read. No primary pair or threshold was "
        "changed. No missing value was filled."
    )


if __name__ == "__main__":
    main()

