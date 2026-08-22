#!/usr/bin/env python3
"""Step 5B: symmetric nearest-pair chemistry versus same-chemistry control.

This is the final matching robustness check for the main adsorption claim.
Both arms use already selected outcome-blind nearest-pair catalogues:

- chemistry-change arm: covariance-aware reciprocal matched pairs;
- control arm: covariance-aware reciprocal same-represented-chemistry pairs.

The script compares the two arms only within shared topology and residual-
geometry ranges. It does not search for new pairs, alter the primary catalogue,
choose conditions from outcomes, orient metal changes, fit a predictive model,
or fill missing values.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import gc
import hashlib
import json
import platform
import re

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
RAW = ROOT / "raw"

CHEMISTRY_PAIRS = ANALYSIS / "reciprocal_covariance_matched_pairs.parquet"
CHEMISTRY_EFFECTS = ANALYSIS / "reciprocal_pair_effect_magnitudes.parquet"
CONTROL_PAIRS = ANALYSIS / "step3_same_chemistry_control_pairs.parquet"
SCALES_FILE = ANALYSIS / "adsorption_condition_scales.csv"
PREVIOUS_RESULTS = ANALYSIS / "step3_same_chemistry_control_results.csv"

DESIGN_OUTPUT = ANALYSIS / "step5b_symmetric_control_design.parquet"
CELL_OUTPUT = ANALYSIS / "step5b_symmetric_control_cells.csv"
RESULT_OUTPUT = ANALYSIS / "step5b_symmetric_control_results.csv"
SUMMARY_OUTPUT = ANALYSIS / "step5b_symmetric_control_summary.csv"
MANIFEST_OUTPUT = ANALYSIS / "step5b_symmetric_control_manifest.json"

N_JOBS = 6
BOOTSTRAP_REPLICATES = 10_000
BASE_SEED = 1701
GEOMETRY_BINS = 5
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

EFFECT_COLUMNS = [
    "absolute_uptake_difference",
    "absolute_log_difference",
    "standardized_absolute_difference",
]

PRIMARY_LIMITS = {
    "Di_relative_difference": 0.03,
    "Df_relative_difference": 0.03,
    "Dif_relative_difference": 0.03,
    "Density_relative_difference": 0.05,
    "UC_volume_relative_difference": 0.05,
    "AVAf_absolute_difference": 0.03,
    "POAVAf_absolute_difference": 0.03,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_id(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"(?i)\.cif$", "", regex=True)
        .str.replace(r"(?i)_repeat$", "", regex=True)
    )


def pair_key(frame: pd.DataFrame) -> pd.Series:
    lo = frame[["id_a", "id_b"]].min(axis=1).astype("string")
    hi = frame[["id_a", "id_b"]].max(axis=1).astype("string")
    return lo + " || " + hi


def choose_column(columns, candidates, purpose, required=True):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    if required:
        raise ValueError(
            f"Could not identify {purpose}. Available columns:\n"
            + "\n".join(map(str, columns))
        )
    return None


def standardize_pair_table(frame: pd.DataFrame, design_type: str) -> pd.DataFrame:
    """Standardize an already selected reciprocal-pair table.

    Both reciprocal catalogues were built with the same robust scaling and
    Ledoit-Wolf precision matrix. Their stored covariance-aware distance is
    therefore the correct common pair-quality measure for the symmetric
    control comparison. No componentwise geometry fields are needed here.
    """
    frame = frame.copy()

    id_a = choose_column(
        frame.columns,
        ["id_a", "mof_id_a", "pair_id_a"],
        "endpoint A",
    )
    id_b = choose_column(
        frame.columns,
        ["id_b", "mof_id_b", "pair_id_b"],
        "endpoint B",
    )
    topology = choose_column(
        frame.columns,
        ["topology", "likely topology", "likely_topology", "topology_primary"],
        "topology",
    )
    distance = choose_column(
        frame.columns,
        [
            "covariance_distance",
            "mahalanobis_distance",
            "geometry_distance",
            "distance",
        ],
        "covariance-aware geometry distance",
    )

    frame = frame.rename(
        columns={
            id_a: "id_a",
            id_b: "id_b",
            topology: "topology",
            distance: "geometry_match_distance",
        }
    )

    if design_type == "chemistry_change":
        intervention = choose_column(
            frame.columns,
            ["intervention", "intervention_class", "chemistry_class"],
            "intervention",
        )
        if intervention != "intervention":
            frame = frame.rename(columns={intervention: "intervention"})
    else:
        frame["intervention"] = "same_chemistry_control"

    frame["id_a"] = canonical_id(frame["id_a"])
    frame["id_b"] = canonical_id(frame["id_b"])
    frame["topology"] = frame["topology"].astype("string").str.strip()
    frame["geometry_match_distance"] = pd.to_numeric(
        frame["geometry_match_distance"], errors="coerce"
    )
    frame["pair_key"] = pair_key(frame)
    frame["design_type"] = design_type

    required_values = [
        "id_a",
        "id_b",
        "topology",
        "geometry_match_distance",
        "pair_key",
    ]
    if frame[required_values].isna().any().any():
        raise RuntimeError(
            f"Missing required values in {design_type} reciprocal-pair table"
        )
    if (frame["geometry_match_distance"] < 0).any():
        raise RuntimeError(
            f"Negative covariance-aware distance in {design_type} table"
        )

    frame = frame.drop_duplicates(["pair_key", "intervention"]).copy()

    return frame[
        [
            "pair_key",
            "id_a",
            "id_b",
            "topology",
            "geometry_match_distance",
            "intervention",
            "design_type",
        ]
    ]

def assign_common_support_cells(design: pd.DataFrame) -> pd.DataFrame:
    parts = []

    for topology, group in design.groupby("topology", sort=True, dropna=False):
        group = group.copy()
        n_unique = group["geometry_match_distance"].nunique(dropna=True)
        bins = min(GEOMETRY_BINS, int(n_unique), len(group))

        if bins < 1:
            continue

        if bins == 1:
            group["geometry_bin"] = 0
        else:
            ranked = group["geometry_match_distance"].rank(
                method="first", pct=True
            )
            group["geometry_bin"] = np.minimum(
                np.floor(ranked * bins).astype(int), bins - 1
            )

        group["support_cell"] = (
            group["topology"].astype("string")
            + " || q"
            + group["geometry_bin"].astype(str)
        )
        parts.append(group)

    if not parts:
        raise RuntimeError("No common-support cells could be formed")

    design = pd.concat(parts, ignore_index=True)

    cell_types = (
        design.groupby("support_cell")["design_type"]
        .nunique()
    )
    common_cells = set(cell_types[cell_types == 2].index)
    design = design.loc[design["support_cell"].isin(common_cells)].copy()

    if design.empty:
        raise RuntimeError("No topology-by-geometry cells contain both design arms")

    return design


def load_scales() -> pd.DataFrame:
    scales = pd.read_csv(SCALES_FILE, low_memory=False)

    target = choose_column(scales.columns, ["target"], "target")
    temperature = choose_column(scales.columns, ["T/K", "temperature", "temperature_K"], "temperature")
    pressure = choose_column(scales.columns, ["p/bar", "pressure", "pressure_bar"], "pressure")
    epsilon = choose_column(
        scales.columns,
        ["epsilon_primary", "epsilon", "log_epsilon"],
        "primary logarithmic offset",
    )
    robust = choose_column(
        scales.columns,
        [
            "robust_scale_iqr_over_1_349",
            "robust_scale",
            "uptake_robust_scale",
        ],
        "robust uptake scale",
        required=False,
    )

    if robust is None:
        iqr = choose_column(
            scales.columns,
            ["uptake_iqr", "iqr_mmol_g", "IQR"],
            "uptake IQR",
        )
        scales["robust_scale"] = pd.to_numeric(scales[iqr], errors="coerce") / 1.349
        robust = "robust_scale"

    scales = scales.rename(
        columns={
            target: "target",
            temperature: "T/K",
            pressure: "p/bar",
            epsilon: "epsilon_primary",
            robust: "robust_scale",
        }
    )

    scales = scales[
        ["target", "T/K", "p/bar", "epsilon_primary", "robust_scale"]
    ].copy()

    for column in ["T/K", "p/bar", "epsilon_primary", "robust_scale"]:
        scales[column] = pd.to_numeric(scales[column], errors="coerce")

    if scales.isna().any().any():
        raise RuntimeError("Condition-scale table contains missing required values")
    if (scales[["epsilon_primary", "robust_scale"]] <= 0).any().any():
        raise RuntimeError("Condition-scale table contains nonpositive scales")
    if scales.duplicated(["target", "T/K", "p/bar"]).any():
        raise RuntimeError("Condition-scale table contains duplicate conditions")

    return scales


def load_adsorption(needed_ids: set[str]) -> pd.DataFrame:
    parts = []

    for filename, target in ADSORPTION_FILES.items():
        path = RAW / filename
        if not path.exists():
            raise FileNotFoundError(path)

        kept = []
        source_rows = 0
        for chunk in pd.read_csv(
            path,
            usecols=["filename", "T/K", "p/bar", "mmol/g"],
            chunksize=CHUNK_SIZE,
            low_memory=False,
        ):
            source_rows += len(chunk)
            chunk["mof_id"] = canonical_id(chunk["filename"])
            chunk = chunk.loc[chunk["mof_id"].isin(needed_ids)].copy()
            if not chunk.empty:
                chunk["target"] = target
                kept.append(chunk[["mof_id", "target", "T/K", "p/bar", "mmol/g"]])

        if kept:
            retained = pd.concat(kept, ignore_index=True)
            parts.append(retained)
            print(f"loaded {filename}: source_rows={source_rows:,}; retained={len(retained):,}")
        else:
            print(f"loaded {filename}: source_rows={source_rows:,}; retained=0")

        del kept
        gc.collect()

    adsorption = pd.concat(parts, ignore_index=True)

    for column in ["T/K", "p/bar", "mmol/g"]:
        adsorption[column] = pd.to_numeric(adsorption[column], errors="coerce")

    if adsorption[["mof_id", "target", "T/K", "p/bar"]].duplicated().any():
        raise RuntimeError("Duplicate framework-condition adsorption rows detected")

    negative = adsorption["mmol/g"].lt(0) & adsorption["mmol/g"].notna()
    if negative.any():
        raise RuntimeError("Negative observed uptake detected")

    return adsorption


def attach_control_effects(
    control_design: pd.DataFrame,
    adsorption: pd.DataFrame,
    scales: pd.DataFrame,
) -> pd.DataFrame:
    conditions = scales[["target", "T/K", "p/bar", "epsilon_primary", "robust_scale"]].copy()

    grid = (
        control_design.assign(_join_key=1)
        .merge(conditions.assign(_join_key=1), on="_join_key", how="inner")
        .drop(columns="_join_key")
    )

    left = adsorption.rename(columns={"mof_id": "id_a", "mmol/g": "uptake_a"})
    right = adsorption.rename(columns={"mof_id": "id_b", "mmol/g": "uptake_b"})

    merged = grid.merge(
        left,
        on=["id_a", "target", "T/K", "p/bar"],
        how="left",
        validate="many_to_one",
    )
    merged = merged.merge(
        right,
        on=["id_b", "target", "T/K", "p/bar"],
        how="left",
        validate="many_to_one",
    )

    merged["outcome_complete"] = merged["uptake_a"].notna() & merged["uptake_b"].notna()
    complete = merged.loc[merged["outcome_complete"]].copy()

    complete["absolute_uptake_difference"] = (
        complete["uptake_b"] - complete["uptake_a"]
    ).abs()
    complete["absolute_log_difference"] = (
        np.log(complete["uptake_b"] + complete["epsilon_primary"])
        - np.log(complete["uptake_a"] + complete["epsilon_primary"])
    ).abs()
    complete["standardized_absolute_difference"] = (
        complete["absolute_uptake_difference"] / complete["robust_scale"]
    )

    print(
        "control pair-condition grid: "
        f"expected={len(merged):,}; complete={len(complete):,}; "
        f"incomplete={len(merged)-len(complete):,}"
    )

    return complete


def load_chemistry_effects(chemistry_design: pd.DataFrame) -> pd.DataFrame:
    effects = pd.read_parquet(CHEMISTRY_EFFECTS)

    rename = {}
    if "pair_key" not in effects.columns:
        if {"id_a", "id_b"}.issubset(effects.columns):
            effects["pair_key"] = pair_key(effects)
        else:
            raise ValueError("Chemistry effect table lacks pair identifiers")

    for required in ["target", "T/K", "p/bar"] + EFFECT_COLUMNS:
        if required not in effects.columns:
            raise ValueError(
                f"Chemistry effect table lacks {required}. Available columns:\n"
                + "\n".join(map(str, effects.columns))
            )

    keep = chemistry_design[
        ["pair_key", "support_cell", "intervention", "topology", "geometry_match_distance"]
    ].drop_duplicates(["pair_key", "intervention"])

    merged = effects.merge(
        keep,
        on=["pair_key", "intervention"],
        how="inner",
        validate="many_to_one",
    )

    if merged.empty:
        raise RuntimeError("No reciprocal chemistry effects matched the common-support design")

    return merged


def analyze_task(task):
    (
        intervention,
        target,
        temperature,
        pressure,
        effect_measure,
        chemistry_rows,
        control_rows,
        seed,
    ) = task

    chem = pd.DataFrame(chemistry_rows)
    ctrl = pd.DataFrame(control_rows)

    chem_cells = chem.groupby("support_cell")[effect_measure].median()
    ctrl_cells = ctrl.groupby("support_cell")[effect_measure].median()

    common = chem_cells.index.intersection(ctrl_cells.index)
    chem_cells = chem_cells.loc[common]
    ctrl_cells = ctrl_cells.loc[common]

    differences = (chem_cells - ctrl_cells).dropna()

    if differences.empty:
        return {
            "intervention": intervention,
            "target": target,
            "T/K": temperature,
            "p/bar": pressure,
            "effect_measure": effect_measure,
            "common_support_cells": 0,
            "median_chemistry_minus_control": np.nan,
            "bootstrap_95_low": np.nan,
            "bootstrap_95_high": np.nan,
            "positive_cell_fraction": np.nan,
        }

    values = differences.to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(BOOTSTRAP_REPLICATES, len(values)))
    boot = np.median(values[indices], axis=1)

    return {
        "intervention": intervention,
        "target": target,
        "T/K": temperature,
        "p/bar": pressure,
        "effect_measure": effect_measure,
        "common_support_cells": int(len(values)),
        "chemistry_pairs": int(chem["pair_key"].nunique()),
        "control_pairs": int(ctrl["pair_key"].nunique()),
        "median_chemistry_minus_control": float(np.median(values)),
        "bootstrap_95_low": float(np.quantile(boot, 0.025)),
        "bootstrap_95_high": float(np.quantile(boot, 0.975)),
        "positive_cell_fraction": float(np.mean(values > 0)),
    }


def classify_interval(row):
    if pd.isna(row["bootstrap_95_low"]) or pd.isna(row["bootstrap_95_high"]):
        return "unavailable"
    if row["bootstrap_95_low"] > 0:
        return "above_control"
    if row["bootstrap_95_high"] < 0:
        return "below_control"
    return "crosses_zero"


def main() -> None:
    for path in [
        CHEMISTRY_PAIRS,
        CHEMISTRY_EFFECTS,
        CONTROL_PAIRS,
        SCALES_FILE,
    ]:
        if not path.exists():
            raise FileNotFoundError(path)

    chemistry_design = standardize_pair_table(
        pd.read_parquet(CHEMISTRY_PAIRS), "chemistry_change"
    )
    control_design = standardize_pair_table(
        pd.read_parquet(CONTROL_PAIRS), "same_chemistry_control"
    )

    design = pd.concat([chemistry_design, control_design], ignore_index=True)
    design = assign_common_support_cells(design)

    chemistry_design = design.loc[
        design["design_type"].eq("chemistry_change")
    ].copy()
    control_design = design.loc[
        design["design_type"].eq("same_chemistry_control")
    ].copy()

    needed_ids = set(control_design["id_a"]) | set(control_design["id_b"])
    scales = load_scales()
    adsorption = load_adsorption(needed_ids)

    control_effects = attach_control_effects(control_design, adsorption, scales)
    chemistry_effects = load_chemistry_effects(chemistry_design)

    DESIGN_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    design.to_parquet(DESIGN_OUTPUT, index=False)

    tasks = []
    task_index = 0

    for intervention in sorted(chemistry_effects["intervention"].dropna().unique()):
        chem_i = chemistry_effects.loc[
            chemistry_effects["intervention"].eq(intervention)
        ]

        condition_keys = (
            chem_i[["target", "T/K", "p/bar"]]
            .drop_duplicates()
            .sort_values(["target", "T/K", "p/bar"])
        )

        for condition in condition_keys.itertuples(index=False, name=None):
            target, temperature, pressure = condition
            chem_c = chem_i.loc[
                chem_i["target"].eq(target)
                & chem_i["T/K"].eq(temperature)
                & chem_i["p/bar"].eq(pressure)
            ]
            ctrl_c = control_effects.loc[
                control_effects["target"].eq(target)
                & control_effects["T/K"].eq(temperature)
                & control_effects["p/bar"].eq(pressure)
            ]

            for effect_measure in EFFECT_COLUMNS:
                chemistry_rows = chem_c[
                    ["pair_key", "support_cell", effect_measure]
                ].to_dict("records")
                control_rows = ctrl_c[
                    ["pair_key", "support_cell", effect_measure]
                ].to_dict("records")

                tasks.append(
                    (
                        intervention,
                        target,
                        float(temperature),
                        float(pressure),
                        effect_measure,
                        chemistry_rows,
                        control_rows,
                        BASE_SEED + task_index,
                    )
                )
                task_index += 1

    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:
        results = list(executor.map(analyze_task, tasks, chunksize=1))

    results = pd.DataFrame(results)
    results["control_status"] = results.apply(classify_interval, axis=1)
    results.to_csv(RESULT_OUTPUT, index=False)

    cells = (
        design.groupby(
            ["support_cell", "topology", "design_type", "intervention"],
            dropna=False,
        )
        .agg(
            pairs=("pair_key", "nunique"),
            median_geometry_match_distance=("geometry_match_distance", "median"),
        )
        .reset_index()
    )
    cells.to_csv(CELL_OUTPUT, index=False)

    summary = (
        results.groupby(["intervention", "effect_measure"], dropna=False)
        .agg(
            evaluated_conditions=("target", "size"),
            medians_above_control=(
                "median_chemistry_minus_control",
                lambda values: int((values > 0).sum()),
            ),
            intervals_above_control=(
                "control_status",
                lambda values: int((values == "above_control").sum()),
            ),
            intervals_below_control=(
                "control_status",
                lambda values: int((values == "below_control").sum()),
            ),
            median_common_support_cells=("common_support_cells", "median"),
        )
        .reset_index()
    )

    if PREVIOUS_RESULTS.exists():
        previous = pd.read_csv(PREVIOUS_RESULTS, low_memory=False)
        keys = ["intervention", "target", "T/K", "p/bar", "effect_measure"]
        previous_keep = previous[
            keys + [
                "median_chemistry_minus_control",
                "bootstrap_95_low",
                "bootstrap_95_high",
            ]
        ].rename(
            columns={
                "median_chemistry_minus_control": "previous_full_support_median",
                "bootstrap_95_low": "previous_full_support_low",
                "bootstrap_95_high": "previous_full_support_high",
            }
        )
        comparison = results.merge(previous_keep, on=keys, how="left")
        comparison["same_median_direction_as_full_support"] = (
            np.sign(comparison["median_chemistry_minus_control"])
            == np.sign(comparison["previous_full_support_median"])
        )
        agreement = (
            comparison.groupby(["intervention", "effect_measure"])[
                "same_median_direction_as_full_support"
            ]
            .agg(["count", "sum"])
            .reset_index()
            .rename(columns={"count": "comparable_conditions", "sum": "same_direction"})
        )
        summary = summary.merge(
            agreement,
            on=["intervention", "effect_measure"],
            how="left",
        )

    summary.to_csv(SUMMARY_OUTPUT, index=False)

    manifest = {
        "stage": "Step 5B - symmetric reciprocal chemistry/control comparison",
        "chemistry_pair_input": str(CHEMISTRY_PAIRS),
        "chemistry_pair_sha256": sha256(CHEMISTRY_PAIRS),
        "chemistry_effect_input": str(CHEMISTRY_EFFECTS),
        "chemistry_effect_sha256": sha256(CHEMISTRY_EFFECTS),
        "control_pair_input": str(CONTROL_PAIRS),
        "control_pair_sha256": sha256(CONTROL_PAIRS),
        "chemistry_pairs_in_common_support": int(chemistry_design["pair_key"].nunique()),
        "control_pairs_in_common_support": int(control_design["pair_key"].nunique()),
        "common_support_cells": int(design["support_cell"].nunique()),
        "geometry_bins": GEOMETRY_BINS,
        "common_support_geometry_measure": "stored covariance-aware distance",
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "seed_base": BASE_SEED,
        "n_jobs": N_JOBS,
        "pair_selection_used_adsorption": False,
        "metal_changes_oriented": False,
        "predictive_model_fitted": False,
        "missing_values_filled": False,
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
    }
    MANIFEST_OUTPUT.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

    print()
    print(
        f"N_JOBS={N_JOBS}; bootstrap_replicates={BOOTSTRAP_REPLICATES}; "
        f"seed_base={BASE_SEED}"
    )
    print()
    print("SYMMETRIC NEAREST-PAIR CONTROL DESIGN")
    design_summary = (
        design.groupby("design_type")
        .agg(
            pairs=("pair_key", "nunique"),
            frameworks_a=("id_a", "nunique"),
            frameworks_b=("id_b", "nunique"),
            topologies=("topology", "nunique"),
            cells=("support_cell", "nunique"),
        )
    )
    print(design_summary.to_string())

    print()
    print("SYMMETRIC CONTROL RESULT")
    print(summary.to_string(index=False))

    print()
    print("Outputs:")
    for path in [
        DESIGN_OUTPUT,
        CELL_OUTPUT,
        RESULT_OUTPUT,
        SUMMARY_OUTPUT,
        MANIFEST_OUTPUT,
    ]:
        print(path)

    print(
        "Both arms used outcome-blind nearest-pair catalogues. "
        "Metal changes remained unordered. No p-value, predictive model, "
        "outcome-driven pair selection, or missing-value filling was used."
    )


if __name__ == "__main__":
    main()

