#!/usr/bin/env python3
"""Step 3b of 5: compare chemistry-change pairs with same-chemistry controls.

The comparison is outcome-blind at the design stage. Primary chemistry-change
pairs and same-chemistry controls are placed on common support using topology
and quintiles of the remaining geometry-difference score. Adsorption magnitudes
are then summarized once per group of related chemistry-change comparisons and
once per control pair. Common topology-by-geometry cells contribute equally.

No signed metal direction, p-value, predictive model, pair reselection from
adsorption outcomes, or missing-value filling is used.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from collections import defaultdict
import gc
import hashlib
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
ANALYSIS = ROOT / "analysis"

INTERVENTION_FILE = ANALYSIS / "caliper_sensitivity_pair_assignments.parquet"
CONTROL_FILE = ANALYSIS / "step3_same_chemistry_control_pairs.parquet"
SCALE_FILE = ANALYSIS / "adsorption_condition_scales.csv"

DESIGN_OUTPUT = ANALYSIS / "step3_control_common_support_design.parquet"
CELL_OUTPUT = ANALYSIS / "step3_control_cell_estimates.csv"
RESULT_OUTPUT = ANALYSIS / "step3_same_chemistry_control_results.csv"
SUMMARY_OUTPUT = ANALYSIS / "step3_same_chemistry_control_run_summary.csv"

N_JOBS = 6
BOOTSTRAP_REPLICATES = 10_000
BASE_SEED = 1701
NUMERICAL_TOLERANCE = 1e-12
SCORE_BINS = 5

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

LIMITS = {
    "Di_diff": 0.03,
    "Df_diff": 0.03,
    "Dif_diff": 0.03,
    "Density_diff": 0.05,
    "UC_volume_diff": 0.05,
    "AVAf_diff": 0.03,
    "POAVAf_diff": 0.03,
}
DIFF_COLUMNS = list(LIMITS)


class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def canonical_id(series):
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"(?i)\.cif$", "", regex=True)
        .str.replace(r"(?i)_repeat$", "", regex=True)
    )


def variant_family(value):
    value = str(value)
    return re.sub(r"(?i)_(clean|freeONLY)$", "", value)


def choose_column(frame, candidates, label):
    for column in candidates:
        if column in frame.columns:
            return column
    raise ValueError(f"Cannot find {label}; tried {candidates}")


def geometry_score(frame):
    matrix = np.column_stack(
        [frame[column].to_numpy(float) / limit for column, limit in LIMITS.items()]
    )
    return np.sqrt(np.mean(matrix ** 2, axis=1))


def build_related_groups(frame):
    output = frame.copy()
    group_ids = pd.Series(index=output.index, dtype="string")
    for intervention, subset in output.groupby("intervention", sort=False):
        uf = UnionFind()
        for row in subset.itertuples():
            a = variant_family(row.id_a)
            b = variant_family(row.id_b)
            uf.union(a, b)
        roots = {}
        for idx, row in subset.iterrows():
            root = uf.find(variant_family(row["id_a"]))
            if root not in roots:
                roots[root] = "group_" + hashlib.sha1(
                    f"{intervention}|{root}".encode("utf-8")
                ).hexdigest()[:16]
            group_ids.loc[idx] = roots[root]
    output["related_group"] = group_ids
    return output


def load_primary_interventions():
    frame = pd.read_parquet(INTERVENTION_FILE)
    tier_column = choose_column(frame, ["tier", "geometry_tier"], "tier column")
    frame = frame.loc[frame[tier_column].astype(str).eq("primary")].copy()
    if frame.empty:
        raise RuntimeError("No primary pairs found")

    id_a = choose_column(frame, ["id_a", "mof_id_a"], "endpoint A")
    id_b = choose_column(frame, ["id_b", "mof_id_b"], "endpoint B")
    topology = choose_column(frame, ["topology", "likely topology"], "topology")
    frame = frame.rename(columns={id_a: "id_a", id_b: "id_b", topology: "topology"})

    missing = [column for column in ["intervention", "id_a", "id_b", "topology", *DIFF_COLUMNS] if column not in frame.columns]
    if missing:
        raise ValueError(f"Primary pair assignments missing columns: {missing}")
    if frame[["id_a", "id_b", "topology", *DIFF_COLUMNS]].isna().any().any():
        raise RuntimeError("Missing primary design values")

    frame["design_type"] = "chemistry_change"
    frame["design_id"] = (
        frame[["id_a", "id_b"]].min(axis=1).astype(str)
        + "||"
        + frame[["id_a", "id_b"]].max(axis=1).astype(str)
        + "||"
        + frame["intervention"].astype(str)
    )
    frame["geometry_score"] = geometry_score(frame)
    frame = build_related_groups(frame)
    return frame[["design_type", "design_id", "intervention", "id_a", "id_b", "topology", "related_group", "geometry_score", *DIFF_COLUMNS]].copy()


def load_controls():
    frame = pd.read_parquet(CONTROL_FILE)
    missing = [column for column in ["id_a", "id_b", "topology", *DIFF_COLUMNS] if column not in frame.columns]
    if missing:
        raise ValueError(f"Control table missing columns: {missing}")
    frame["design_type"] = "same_chemistry_control"
    frame["design_id"] = (
        frame[["id_a", "id_b"]].min(axis=1).astype(str)
        + "||"
        + frame[["id_a", "id_b"]].max(axis=1).astype(str)
    )
    frame["related_group"] = frame["design_id"]
    frame["geometry_score"] = geometry_score(frame)
    return frame[["design_type", "design_id", "id_a", "id_b", "topology", "related_group", "geometry_score", *DIFF_COLUMNS]].copy()


def assign_common_support(interventions, controls):
    # Fixed bins are defined from the combined, outcome-blind geometry-score distribution.
    combined_scores = pd.concat([interventions["geometry_score"], controls["geometry_score"]], ignore_index=True)
    edges = np.unique(np.quantile(combined_scores, np.linspace(0, 1, SCORE_BINS + 1)))
    if len(edges) < 3:
        raise RuntimeError("Insufficient geometry-score variation for common-support bins")
    edges[0] = -np.inf
    edges[-1] = np.inf

    interventions["score_bin"] = pd.cut(interventions["geometry_score"], bins=edges, labels=False, include_lowest=True)
    controls["score_bin"] = pd.cut(controls["geometry_score"], bins=edges, labels=False, include_lowest=True)

    control_cells = set(zip(controls["topology"].astype(str), controls["score_bin"].astype(int)))
    interventions["common_support"] = [
        (str(topology), int(score_bin)) in control_cells
        for topology, score_bin in zip(interventions["topology"], interventions["score_bin"])
    ]
    intervention_cells = set(zip(interventions.loc[interventions["common_support"], "topology"].astype(str), interventions.loc[interventions["common_support"], "score_bin"].astype(int)))
    controls["common_support"] = [
        (str(topology), int(score_bin)) in intervention_cells
        for topology, score_bin in zip(controls["topology"], controls["score_bin"])
    ]
    return interventions, controls, edges


def read_adsorption(wanted_ids):
    parts = []
    for filename, target in ADSORPTION_FILES.items():
        retained = []
        for chunk in pd.read_csv(
            RAW / filename,
            usecols=["filename", "T/K", "p/bar", "mmol/g"],
            chunksize=250_000,
            low_memory=False,
        ):
            chunk["mof_id"] = canonical_id(chunk["filename"])
            chunk = chunk.loc[chunk["mof_id"].isin(wanted_ids), ["mof_id", "T/K", "p/bar", "mmol/g"]]
            if not chunk.empty:
                retained.append(chunk)
        data = pd.concat(retained, ignore_index=True)
        data["target"] = target
        for column in ["T/K", "p/bar", "mmol/g"]:
            data[column] = pd.to_numeric(data[column], errors="coerce")
        parts.append(data)
        print(f"loaded {filename}: retained={len(data):,}")
        del retained, data
        gc.collect()
    adsorption = pd.concat(parts, ignore_index=True)
    if adsorption.duplicated(["mof_id", "target", "T/K", "p/bar"]).any():
        raise RuntimeError("Duplicate framework-condition adsorption rows")
    return adsorption


def attach_effects(design, adsorption, scales):
    """Create the complete pair-condition grid, then attach both endpoints.

    The complete grid prevents a missing endpoint-A observation from deleting
    the expected pair-condition row before missingness is evaluated.
    """
    condition_columns = ["target", "T/K", "p/bar"]
    conditions = (
        scales[condition_columns]
        .drop_duplicates()
        .sort_values(condition_columns)
        .reset_index(drop=True)
    )

    expected = (
        design.assign(_join_key=1)
        .merge(
            conditions.assign(_join_key=1),
            on="_join_key",
            how="inner",
            validate="many_to_many",
        )
        .drop(columns="_join_key")
    )

    left = adsorption.rename(
        columns={"mof_id": "id_a", "mmol/g": "uptake_a"}
    )
    right = adsorption.rename(
        columns={"mof_id": "id_b", "mmol/g": "uptake_b"}
    )

    merged = expected.merge(
        left,
        on=["id_a", *condition_columns],
        how="left",
        validate="many_to_one",
    )
    merged = merged.merge(
        right,
        on=["id_b", *condition_columns],
        how="left",
        validate="many_to_one",
    )

    merged["outcome_complete"] = (
        merged["uptake_a"].notna()
        & merged["uptake_b"].notna()
    )
    merged["missing_a"] = merged["uptake_a"].isna()
    merged["missing_b"] = merged["uptake_b"].isna()

    expected_rows = len(design) * len(conditions)
    if len(merged) != expected_rows:
        raise RuntimeError(
            f"Expected {expected_rows:,} pair-condition rows, "
            f"obtained {len(merged):,}"
        )

    complete = merged.loc[merged["outcome_complete"]].copy()
    if (complete[["uptake_a", "uptake_b"]] < 0).any().any():
        raise RuntimeError("Negative uptake in complete rows")

    complete = complete.merge(
        scales,
        on=condition_columns,
        how="left",
        validate="many_to_one",
    )
    if complete[["epsilon_primary", "robust_scale"]].isna().any().any():
        raise RuntimeError("Missing condition scale")

    complete["absolute_uptake_difference"] = (
        complete["uptake_b"] - complete["uptake_a"]
    ).abs()
    complete["absolute_log_difference"] = (
        np.log(complete["uptake_b"] + complete["epsilon_primary"])
        - np.log(complete["uptake_a"] + complete["epsilon_primary"])
    ).abs()
    complete["standardized_absolute_difference"] = (
        complete["absolute_uptake_difference"]
        / complete["robust_scale"]
    )

    missing_summary = (
        merged.loc[~merged["outcome_complete"]]
        .groupby(condition_columns, as_index=False, dropna=False)
        .agg(
            incomplete_rows=("design_id", "size"),
            missing_a=("missing_a", "sum"),
            missing_b=("missing_b", "sum"),
        )
    )

    print(
        f"expected_pair_condition_rows={expected_rows:,}; "
        f"complete={len(complete):,}; "
        f"incomplete={expected_rows - len(complete):,}"
    )
    if not missing_summary.empty:
        print("\nINCOMPLETE OUTCOMES BY CONDITION")
        print(missing_summary.to_string(index=False))

    return complete

def bootstrap_task(payload):
    key, cells, seed = payload
    rng = np.random.default_rng(seed)
    values = cells["chemistry_minus_control"].to_numpy(float)
    if len(values) == 0:
        return (*key, 0, np.nan, np.nan, np.nan, np.nan)
    draws = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    for i in range(BOOTSTRAP_REPLICATES):
        sample = rng.choice(values, size=len(values), replace=True)
        draws[i] = np.median(sample)
    return (
        *key,
        len(values),
        float(np.median(values)),
        float(np.quantile(draws, 0.025)),
        float(np.quantile(draws, 0.975)),
        float(np.mean(values > 0)),
    )


def main():
    for path in [INTERVENTION_FILE, CONTROL_FILE, SCALE_FILE]:
        if not path.exists():
            raise FileNotFoundError(path)

    interventions = load_primary_interventions()
    controls = load_controls()
    interventions, controls, edges = assign_common_support(interventions, controls)

    design = pd.concat(
        [
            interventions.loc[interventions["common_support"]],
            controls.loc[controls["common_support"]],
        ],
        ignore_index=True,
        sort=False,
    )
    design.to_parquet(DESIGN_OUTPUT, index=False)

    wanted_ids = set(design["id_a"]) | set(design["id_b"])
    adsorption = read_adsorption(wanted_ids)
    scales = pd.read_csv(SCALE_FILE)

    # Normalize the frozen condition-scale schema instead of assuming one
    # historical column name. Scientific values are not recalculated or filled.
    epsilon_candidates = [
        "epsilon_primary",
        "primary_epsilon",
        "epsilon_1pct",
        "epsilon",
    ]
    robust_candidates = [
        "robust_scale",
        "robust_scale_mmol_g",
        "condition_robust_scale",
        "uptake_robust_scale",
        "iqr_over_1_349",
        "iqr_div_1_349",
    ]

    epsilon_source = next(
        (column for column in epsilon_candidates if column in scales.columns),
        None,
    )
    robust_source = next(
        (column for column in robust_candidates if column in scales.columns),
        None,
    )

    if robust_source is None:
        robust_like = [
            column for column in scales.columns
            if "robust" in column.lower() and "scale" in column.lower()
        ]
        if len(robust_like) == 1:
            robust_source = robust_like[0]

    if robust_source is None and "uptake_iqr" in scales.columns:
        scales["robust_scale"] = (
            pd.to_numeric(scales["uptake_iqr"], errors="coerce") / 1.349
        )
        robust_source = "robust_scale"

    if robust_source is None and {"q25", "q75"}.issubset(scales.columns):
        scales["robust_scale"] = (
            pd.to_numeric(scales["q75"], errors="coerce")
            - pd.to_numeric(scales["q25"], errors="coerce")
        ) / 1.349
        robust_source = "robust_scale"

    if epsilon_source is None or robust_source is None:
        raise ValueError(
            "Could not identify the frozen epsilon/robust-scale columns in "
            f"{SCALE_FILE}. Available columns: {list(scales.columns)}"
        )

    scales = scales.rename(
        columns={
            epsilon_source: "epsilon_primary",
            robust_source: "robust_scale",
        }
    )

    required_scale_columns = [
        "target", "T/K", "p/bar", "epsilon_primary", "robust_scale"
    ]
    missing_scale_columns = [
        column for column in required_scale_columns
        if column not in scales.columns
    ]
    if missing_scale_columns:
        raise ValueError(
            f"Condition-scale table is missing: {missing_scale_columns}"
        )

    scales = scales[required_scale_columns].copy()
    for column in ["T/K", "p/bar", "epsilon_primary", "robust_scale"]:
        scales[column] = pd.to_numeric(scales[column], errors="coerce")

    if scales[required_scale_columns].isna().any().any():
        raise RuntimeError(
            "The frozen condition-scale table contains missing or nonnumeric "
            "required values; no value was filled."
        )
    if (scales[["epsilon_primary", "robust_scale"]] <= 0).any().any():
        raise RuntimeError(
            "The frozen epsilon and robust scale must be positive for every "
            "adsorption condition."
        )
    if scales.duplicated(["target", "T/K", "p/bar"]).any():
        raise RuntimeError(
            "Duplicate target-temperature-pressure rows in condition scales."
        )

    print(
        f"condition scales: epsilon={epsilon_source}; "
        f"robust_scale={robust_source}"
    )

    effects = attach_effects(design, adsorption, scales)

    measures = [
        "absolute_uptake_difference",
        "absolute_log_difference",
        "standardized_absolute_difference",
    ]
    cell_rows = []
    for intervention, changed in effects.loc[effects["design_type"].eq("chemistry_change")].groupby("intervention", sort=False):
        controls_effect = effects.loc[effects["design_type"].eq("same_chemistry_control")].copy()
        for measure in measures:
            changed_group = (
                changed.groupby(
                    ["related_group", "topology", "score_bin", "target", "T/K", "p/bar"],
                    as_index=False,
                    dropna=False,
                )[measure]
                .median()
                .rename(columns={measure: "chemistry_magnitude"})
            )
            control_group = (
                controls_effect.groupby(
                    ["related_group", "topology", "score_bin", "target", "T/K", "p/bar"],
                    as_index=False,
                    dropna=False,
                )[measure]
                .median()
                .rename(columns={measure: "control_magnitude"})
            )
            changed_cells = changed_group.groupby(["topology", "score_bin", "target", "T/K", "p/bar"], as_index=False).agg(
                chemistry_magnitude=("chemistry_magnitude", "median"),
                chemistry_groups=("related_group", "nunique"),
            )
            control_cells = control_group.groupby(["topology", "score_bin", "target", "T/K", "p/bar"], as_index=False).agg(
                control_magnitude=("control_magnitude", "median"),
                control_pairs=("related_group", "nunique"),
            )
            common = changed_cells.merge(
                control_cells,
                on=["topology", "score_bin", "target", "T/K", "p/bar"],
                how="inner",
                validate="one_to_one",
            )
            common["intervention"] = intervention
            common["effect_measure"] = measure
            common["chemistry_minus_control"] = common["chemistry_magnitude"] - common["control_magnitude"]
            cell_rows.append(common)

    cells = pd.concat(cell_rows, ignore_index=True)
    cells.to_csv(CELL_OUTPUT, index=False)

    task_keys = list(
        cells.groupby(["intervention", "effect_measure", "target", "T/K", "p/bar"], sort=True).groups
    )
    tasks = []
    for i, key in enumerate(task_keys):
        subset = cells.loc[
            (cells["intervention"] == key[0])
            & (cells["effect_measure"] == key[1])
            & (cells["target"] == key[2])
            & (cells["T/K"] == key[3])
            & (cells["p/bar"] == key[4])
        ].copy()
        tasks.append((key, subset, BASE_SEED + i))

    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:
        result_rows = list(executor.map(bootstrap_task, tasks, chunksize=1))

    columns = [
        "intervention", "effect_measure", "target", "T/K", "p/bar",
        "common_support_cells", "median_chemistry_minus_control",
        "bootstrap_95_low", "bootstrap_95_high", "positive_cell_fraction",
    ]
    results = pd.DataFrame(result_rows, columns=columns)
    results.to_csv(RESULT_OUTPUT, index=False)

    summary_rows = []
    for (intervention, measure), group in results.groupby(["intervention", "effect_measure"], sort=False):
        summary_rows.append(
            {
                "intervention": intervention,
                "effect_measure": measure,
                "conditions": len(group),
                "median_conditions_above_control": int((group["median_chemistry_minus_control"] > 0).sum()),
                "intervals_entirely_above_control": int((group["bootstrap_95_low"] > 0).sum()),
                "intervals_entirely_below_control": int((group["bootstrap_95_high"] < 0).sum()),
                "median_common_support_cells": float(group["common_support_cells"].median()),
            }
        )
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(SUMMARY_OUTPUT, index=False)

    design_summary = pd.DataFrame(
        [
            {
                "design_type": "chemistry_change",
                "pairs": int((design["design_type"] == "chemistry_change").sum()),
                "frameworks": len(set(design.loc[design["design_type"] == "chemistry_change", "id_a"]) | set(design.loc[design["design_type"] == "chemistry_change", "id_b"])),
                "topologies": design.loc[design["design_type"] == "chemistry_change", "topology"].nunique(),
            },
            {
                "design_type": "same_chemistry_control",
                "pairs": int((design["design_type"] == "same_chemistry_control").sum()),
                "frameworks": len(set(design.loc[design["design_type"] == "same_chemistry_control", "id_a"]) | set(design.loc[design["design_type"] == "same_chemistry_control", "id_b"])),
                "topologies": design.loc[design["design_type"] == "same_chemistry_control", "topology"].nunique(),
            },
        ]
    )

    print(
        f"N_JOBS={N_JOBS}; bootstrap_replicates={BOOTSTRAP_REPLICATES}; "
        f"common_support_pairs={len(design):,}; cells={len(cells):,}"
    )
    print("\nCOMMON-SUPPORT DESIGN")
    print(design_summary.to_string(index=False))
    print("\nSAME-CHEMISTRY CONTROL RESULT")
    print(summary.to_string(index=False))
    print("\nOutputs:")
    print(DESIGN_OUTPUT)
    print(CELL_OUTPUT)
    print(RESULT_OUTPUT)
    print(SUMMARY_OUTPUT)
    print(
        "Controls and chemistry-change pairs were compared only in shared "
        "topology-by-geometry-score cells. No signed metal direction, p-value, "
        "predictive model, outcome-driven pair selection, or missing-value "
        "filling was used."
    )


if __name__ == "__main__":
    main()

