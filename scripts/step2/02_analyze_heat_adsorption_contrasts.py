#!/usr/bin/env python3
"""
Project 7B2: matched heat-of-adsorption contrast analysis.

Place inside:
    Step 2 chemistry strengthening/

Run from project root:
    python "Step 2 chemistry strengthening/analyze_heat_adsorption_contrasts.py"

Scientific question
-------------------
Within the frozen geometry-matched pairs, is adsorption separation associated
with an independently reported energetic contrast, |Delta HOA|, and does the
pressure dependence of |Delta HOA| track the pressure dependence of adsorption
separation?

This is an associational energetic-correlate analysis, not a causal mechanism
or directional substitution analysis. Missing HOA values are not filled.

Inputs
------
    analysis/final_primary_pair_effect_magnitudes.parquet
    raw/*.csv containing hoa/kcal/mol

Outputs
-------
    Step 2 results/heat_analysis/
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import spearmanr

STEP2 = Path(__file__).resolve().parent
ROOT = STEP2.parent
ANALYSIS = ROOT / "analysis"
RAW = ROOT / "raw"
EFFECTS = ANALYSIS / "final_primary_pair_effect_magnitudes.parquet"
OUT = ROOT / "Step 2 results" / "heat_analysis"
OUT.mkdir(parents=True, exist_ok=True)

N_JOBS = 6
N_BOOT = 10_000
SEED = 2701
CHUNKSIZE = 200_000

RAW_TARGET_MAP = {
    "landfill-CH4": "landfill_CH4",
    "landfill-CO2": "landfill_CO2",
    "methane_purification-CH4": "methane_purification_CH4",
    "methane_purification-CO2": "methane_purification_CO2",
    "methane": "methane_storage_CH4",
    "post_comb_vsa-CO2": "post_combustion_CO2",
    "post_comb_vsa-N2": "post_combustion_N2",
    "pre_comb_4040-CO2": "pre_combustion_CO2",
    "pre_comb_4040-H2": "pre_combustion_H2",
}
REQ_RAW = ["filename", "T/K", "p/bar", "hoa/kcal/mol", "stdev.3"]
EFFECT_MEASURES = [
    "absolute_log_difference",
    "standardized_absolute_difference",
]


def canonical_id(values: pd.Series) -> pd.Series:
    return (
        values.astype("string")
        .str.strip()
        .str.replace(r"(?i)\.cif$", "", regex=True)
        .str.replace(r"(?i)_repeat$", "", regex=True)
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def bootstrap_median(values: np.ndarray, seed: int) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return np.nan, np.nan, np.nan
    estimate = float(np.median(values))
    rng = np.random.default_rng(seed)
    out = np.empty(N_BOOT, dtype=float)
    n = values.size
    for i in range(N_BOOT):
        out[i] = np.median(values[rng.integers(0, n, n)])
    low, high = np.quantile(out, [0.025, 0.975])
    return estimate, float(low), float(high)


def bootstrap_spearman(x: np.ndarray, y: np.ndarray, seed: int) -> tuple[float, float, float]:
    mask = np.isfinite(x) & np.isfinite(y)
    x = np.asarray(x, dtype=float)[mask]
    y = np.asarray(y, dtype=float)[mask]
    if x.size < 8 or np.unique(x).size < 2 or np.unique(y).size < 2:
        return np.nan, np.nan, np.nan
    estimate = float(spearmanr(x, y).statistic)
    rng = np.random.default_rng(seed)
    vals = []
    n = x.size
    for _ in range(N_BOOT):
        idx = rng.integers(0, n, n)
        xb, yb = x[idx], y[idx]
        if np.unique(xb).size > 1 and np.unique(yb).size > 1:
            vals.append(float(spearmanr(xb, yb).statistic))
    if not vals:
        return estimate, np.nan, np.nan
    low, high = np.quantile(vals, [0.025, 0.975])
    return estimate, float(low), float(high)


def load_heat(endpoint_ids: set[str], frozen_targets: set[str]) -> tuple[pd.DataFrame, list[Path]]:
    parts = []
    files = []
    for path in sorted(RAW.glob("*.csv")):
        try:
            cols = pd.read_csv(path, nrows=0).columns.tolist()
        except Exception:
            continue
        if not all(c in cols for c in REQ_RAW):
            continue
        if path.stem not in RAW_TARGET_MAP:
            continue
        target = RAW_TARGET_MAP[path.stem]
        if target not in frozen_targets:
            raise RuntimeError(f"Mapped target {target!r} is absent from frozen effects")
        files.append(path)
        for chunk in pd.read_csv(path, usecols=REQ_RAW, chunksize=CHUNKSIZE, low_memory=False):
            chunk["mof_id"] = canonical_id(chunk["filename"])
            chunk = chunk.loc[chunk["mof_id"].isin(endpoint_ids)].copy()
            if chunk.empty:
                continue
            chunk["target"] = target
            chunk["T/K"] = pd.to_numeric(chunk["T/K"], errors="coerce")
            chunk["p/bar"] = pd.to_numeric(chunk["p/bar"], errors="coerce")
            chunk["hoa"] = pd.to_numeric(chunk["hoa/kcal/mol"], errors="coerce")
            chunk["hoa_stdev"] = pd.to_numeric(chunk["stdev.3"], errors="coerce")
            parts.append(chunk[["mof_id", "target", "T/K", "p/bar", "hoa", "hoa_stdev"]])
    if not parts:
        raise RuntimeError("No heat rows matched frozen pair endpoints")
    heat = pd.concat(parts, ignore_index=True)
    key = ["mof_id", "target", "T/K", "p/bar"]
    dup = heat.duplicated(key, keep=False)
    if dup.any():
        heat.loc[dup].sort_values(key).to_csv(OUT / "duplicate_heat_keys.csv", index=False)
        raise RuntimeError("Duplicate heat keys found; no averaging performed")
    return heat, files


def condition_task(key, group: pd.DataFrame, task_id: int) -> dict:
    intervention, target, temp, pressure, measure = key
    x = group["absolute_hoa_difference"].to_numpy(float)
    y = group[measure].to_numpy(float)
    heat_med, heat_lo, heat_hi = bootstrap_median(x, SEED + task_id * 17)
    rho, rho_lo, rho_hi = bootstrap_spearman(x, y, SEED + task_id * 17 + 1)
    return {
        "intervention": intervention,
        "target": target,
        "T/K": temp,
        "p/bar": pressure,
        "effect_measure": measure,
        "related_groups": len(group),
        "median_absolute_hoa_difference": heat_med,
        "bootstrap_95_low_absolute_hoa_difference": heat_lo,
        "bootstrap_95_high_absolute_hoa_difference": heat_hi,
        "spearman_rho_heat_vs_adsorption_separation": rho,
        "bootstrap_95_low_rho": rho_lo,
        "bootstrap_95_high_rho": rho_hi,
    }


def pressure_task(key, group: pd.DataFrame, task_id: int) -> dict | None:
    intervention, target, temp, measure = key
    pressures = sorted(group["p/bar"].dropna().unique())
    if len(pressures) != 2:
        return None
    low_p, high_p = pressures
    low = group.loc[group["p/bar"].eq(low_p), [
        "dependence_family_id", "absolute_hoa_difference", measure
    ]].rename(columns={
        "absolute_hoa_difference": "heat_low", measure: "adsorption_low"
    })
    high = group.loc[group["p/bar"].eq(high_p), [
        "dependence_family_id", "absolute_hoa_difference", measure
    ]].rename(columns={
        "absolute_hoa_difference": "heat_high", measure: "adsorption_high"
    })
    paired = low.merge(high, on="dependence_family_id", how="inner", validate="one_to_one")
    if paired.empty:
        return None
    paired["heat_change_high_minus_low"] = paired["heat_high"] - paired["heat_low"]
    paired["adsorption_change_high_minus_low"] = paired["adsorption_high"] - paired["adsorption_low"]
    rho, rho_lo, rho_hi = bootstrap_spearman(
        paired["heat_change_high_minus_low"].to_numpy(float),
        paired["adsorption_change_high_minus_low"].to_numpy(float),
        SEED + task_id * 31,
    )
    concordance = np.mean(
        np.sign(paired["heat_change_high_minus_low"]) ==
        np.sign(paired["adsorption_change_high_minus_low"])
    )
    return {
        "intervention": intervention,
        "target": target,
        "T/K": temp,
        "effect_measure": measure,
        "p/bar_low": low_p,
        "p/bar_high": high_p,
        "paired_related_groups": len(paired),
        "median_heat_low": float(paired["heat_low"].median()),
        "median_heat_high": float(paired["heat_high"].median()),
        "median_heat_change_high_minus_low": float(paired["heat_change_high_minus_low"].median()),
        "median_adsorption_low": float(paired["adsorption_low"].median()),
        "median_adsorption_high": float(paired["adsorption_high"].median()),
        "median_adsorption_change_high_minus_low": float(paired["adsorption_change_high_minus_low"].median()),
        "spearman_rho_pressure_change_heat_vs_adsorption": rho,
        "bootstrap_95_low_rho": rho_lo,
        "bootstrap_95_high_rho": rho_hi,
        "direction_concordance_fraction": float(concordance),
    }


def main() -> None:
    if not EFFECTS.exists():
        raise FileNotFoundError(EFFECTS)

    cols = [
        "id_a", "id_b", "intervention", "dependence_family_id",
        "target", "T/K", "p/bar", "outcome_complete",
        "absolute_log_difference", "standardized_absolute_difference",
    ]
    pairs = pd.read_parquet(EFFECTS, columns=cols)
    pairs["id_a"] = canonical_id(pairs["id_a"])
    pairs["id_b"] = canonical_id(pairs["id_b"])
    pairs["target"] = pairs["target"].astype("string")
    pairs["T/K"] = pd.to_numeric(pairs["T/K"], errors="coerce")
    pairs["p/bar"] = pd.to_numeric(pairs["p/bar"], errors="coerce")
    endpoint_ids = set(pairs["id_a"].dropna()) | set(pairs["id_b"].dropna())
    heat, raw_files = load_heat(endpoint_ids, set(pairs["target"].dropna().astype(str)))

    a = heat.rename(columns={"mof_id": "id_a", "hoa": "hoa_a", "hoa_stdev": "hoa_stdev_a"})
    b = heat.rename(columns={"mof_id": "id_b", "hoa": "hoa_b", "hoa_stdev": "hoa_stdev_b"})
    join = ["target", "T/K", "p/bar"]
    pairs = pairs.merge(a, on=["id_a"] + join, how="left", validate="many_to_one")
    pairs = pairs.merge(b, on=["id_b"] + join, how="left", validate="many_to_one")
    pairs["hoa_pair_complete"] = pairs["hoa_a"].notna() & pairs["hoa_b"].notna()
    pairs["absolute_hoa_difference"] = (pairs["hoa_b"] - pairs["hoa_a"]).abs()

    eligible = pairs.loc[pairs["hoa_pair_complete"] & pairs["outcome_complete"].eq(True)].copy()
    attrition = (
        pairs.groupby(["intervention", "target", "T/K", "p/bar"], dropna=False)
        .agg(
            expected_rows=("id_a", "size"),
            adsorption_complete_rows=("outcome_complete", "sum"),
            heat_complete_rows=("hoa_pair_complete", "sum"),
            expected_groups=("dependence_family_id", "nunique"),
        ).reset_index()
    )
    attrition.to_csv(OUT / "heat_analysis_attrition.csv", index=False)

    # Preserve frozen dependence handling: median within dependence family.
    group_cols = ["intervention", "dependence_family_id", "target", "T/K", "p/bar"]
    grouped = eligible.groupby(group_cols, dropna=False).agg(
        raw_pair_rows=("id_a", "size"),
        absolute_hoa_difference=("absolute_hoa_difference", "median"),
        absolute_log_difference=("absolute_log_difference", "median"),
        standardized_absolute_difference=("standardized_absolute_difference", "median"),
    ).reset_index()
    grouped.to_parquet(OUT / "matched_heat_group_data.parquet", index=False)

    expanded = pd.concat(
        [grouped.assign(effect_measure=m) for m in EFFECT_MEASURES], ignore_index=True
    )
    tasks = []
    for key, g in expanded.groupby(
        ["intervention", "target", "T/K", "p/bar", "effect_measure"], dropna=False
    ):
        tasks.append((key, g.copy()))
    condition_results = Parallel(n_jobs=N_JOBS, prefer="processes") (
        delayed(condition_task)(key, g, i) for i, (key, g) in enumerate(tasks)
    )
    condition_df = pd.DataFrame(condition_results)
    condition_df.to_csv(OUT / "heat_adsorption_condition_results.csv", index=False)

    pressure_tasks = []
    for key, g in expanded.groupby(
        ["intervention", "target", "T/K", "effect_measure"], dropna=False
    ):
        pressure_tasks.append((key, g.copy()))
    pressure_results = Parallel(n_jobs=N_JOBS, prefer="processes") (
        delayed(pressure_task)(key, g, i) for i, (key, g) in enumerate(pressure_tasks)
    )
    pressure_df = pd.DataFrame([x for x in pressure_results if x is not None])
    pressure_df.to_csv(OUT / "heat_adsorption_pressure_results.csv", index=False)

    # Compact interpretation summary. No automatic mechanistic claim.
    summary_rows = []
    for intervention, g in condition_df.groupby("intervention"):
        for measure, gm in g.groupby("effect_measure"):
            summary_rows.append({
                "intervention": intervention,
                "effect_measure": measure,
                "conditions": len(gm),
                "positive_rho": int((gm["spearman_rho_heat_vs_adsorption_separation"] > 0).sum()),
                "interval_above_zero": int((gm["bootstrap_95_low_rho"] > 0).sum()),
                "median_rho": float(gm["spearman_rho_heat_vs_adsorption_separation"].median()),
                "maximum_absolute_rho": float(gm["spearman_rho_heat_vs_adsorption_separation"].abs().max()),
            })
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / "heat_analysis_summary.csv", index=False)

    linker = summary.loc[summary["intervention"].eq("linker_family_change")]
    if not linker.empty and (linker["interval_above_zero"] >= 9).any():
        decision = "ENERGETIC_ASSOCIATION_SUPPORTED_IN_MULTIPLE_CONDITIONS"
    elif not linker.empty and (linker["positive_rho"] >= 12).any():
        decision = "DESCRIPTIVE_ENERGETIC_ASSOCIATION_ONLY"
    else:
        decision = "NO_CONSISTENT_ENERGETIC_ASSOCIATION"

    report = [
        "PROJECT 7B2 MATCHED HEAT-CONTRAST ANALYSIS",
        "=" * 72,
        f"Decision: {decision}",
        f"Frozen pair-condition rows: {len(pairs):,}",
        f"Complete adsorption + heat rows analyzed: {len(eligible):,}",
        f"Dependence-family condition rows: {len(grouped):,}",
        f"Condition-level association rows: {len(condition_df):,}",
        f"Pressure-comparison rows: {len(pressure_df):,}",
        "",
        "Summary:",
        summary.to_string(index=False),
        "",
        "Interpretation boundary:",
        "  |Delta HOA| is an energetic correlate, not proof of a molecular mechanism.",
        "  All chemistry transitions remain unordered.",
        "  No missing value was filled; no pair or threshold was reselected.",
        "  Group medians and group bootstrap preserve the frozen dependence design.",
    ]
    (OUT / "heat_analysis_report.txt").write_text("\n".join(report), encoding="utf-8", newline="\n")

    manifest = {
        "stage": "7B2 matched heat-of-adsorption contrast analysis",
        "created": datetime.now().isoformat(timespec="seconds"),
        "scientific_question": "Do energetic contrast magnitudes track adsorption separation and its pressure dependence within frozen matched pairs?",
        "n_jobs": N_JOBS,
        "bootstrap_replicates": N_BOOT,
        "seed": SEED,
        "frozen_input": str(EFFECTS),
        "frozen_input_sha256": sha256(EFFECTS),
        "raw_inputs": [{"file": str(p), "sha256": sha256(p)} for p in raw_files],
        "missing_values_filled": False,
        "pair_reselection": False,
        "chemical_direction_assigned": False,
        "model_fitted": False,
        "decision": decision,
        "outputs": [
            "heat_analysis_attrition.csv",
            "matched_heat_group_data.parquet",
            "heat_adsorption_condition_results.csv",
            "heat_adsorption_pressure_results.csv",
            "heat_analysis_summary.csv",
            "heat_analysis_report.txt",
        ],
        "python": sys.version,
        "pandas": pd.__version__,
    }
    (OUT / "heat_analysis_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8", newline="\n"
    )

    print("\n".join(report))
    print(f"\nOutputs: {OUT}")


if __name__ == "__main__":
    main()
