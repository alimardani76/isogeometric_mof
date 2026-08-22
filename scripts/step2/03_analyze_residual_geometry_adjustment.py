#!/usr/bin/env python3
"""
Project 7B2 Step 2, file 03: residual-geometry-adjusted linker sensitivity.

Place inside:
    Step 2 chemistry strengthening/

Run from project root:
    python "Step 2 chemistry strengthening/03_analyze_residual_geometry_adjustment.py"

Question
--------
Does the linker-family versus symmetric same-chemistry control contrast remain
positive after transparent linear adjustment for the seven measured geometry
differences retained within the frozen matching limits?

This is an associational sensitivity analysis. The frozen matched-control
median contrast remains primary. No pair is reselected and no value is imputed.

Outputs
-------
    Step 2 results/residual_adjustment/03_*.csv|txt|json
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

STEP2 = Path(__file__).resolve().parent
ROOT = STEP2.parent
ANALYSIS = ROOT / "analysis"
RAW = ROOT / "raw"
OUT = ROOT / "Step 2 results" / "residual_adjustment"
OUT.mkdir(parents=True, exist_ok=True)

DESIGN = ANALYSIS / "step5b_symmetric_control_design.parquet"
PRIMARY = ANALYSIS / "final_primary_pairs.parquet"
CONTROLS = ANALYSIS / "step3_same_chemistry_control_pairs.parquet"
SCALES = ANALYSIS / "adsorption_condition_scales.csv"

N_JOBS = 6
N_BOOT = 10_000
SEED = 3701
CHUNKSIZE = 200_000
MIN_MIXED_CELLS = 8

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
RAW_COLS = ["filename", "T/K", "p/bar", "mmol/g"]
GEOM = ["Di_diff", "Df_diff", "Dif_diff", "Density_diff", "UC_volume_diff", "AVAf_diff", "POAVAf_diff"]
FRAC = ["g_Di", "g_Df", "g_Dif", "g_Density", "g_UC_volume", "g_AVAf", "g_POAVAf"]
LIMITS = dict(zip(GEOM, [0.03, 0.03, 0.03, 0.05, 0.05, 0.03, 0.03]))
MEASURES = ["absolute_log_difference", "standardized_absolute_difference"]


def canonical_id(s: pd.Series) -> pd.Series:
    return (s.astype("string").str.strip()
            .str.replace(r"(?i)\.cif$", "", regex=True)
            .str.replace(r"(?i)_repeat$", "", regex=True))


def pair_key(a: pd.Series, b: pd.Series) -> pd.Series:
    return np.where(a <= b, a + " || " + b, b + " || " + a)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require(paths):
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing required input(s):\n" + "\n".join(missing))


def geometry_table() -> pd.DataFrame:
    design = pd.read_parquet(DESIGN)
    needed = {"pair_key", "id_a", "id_b", "intervention", "design_type", "support_cell"}
    absent = needed - set(design.columns)
    if absent:
        raise RuntimeError(f"Symmetric design missing columns: {sorted(absent)}")
    design["id_a"] = canonical_id(design["id_a"])
    design["id_b"] = canonical_id(design["id_b"])
    design["pair_key"] = pair_key(design["id_a"], design["id_b"])
    # Retain the linker chemistry arm plus the shared same-chemistry control arm.
    # In the frozen symmetric design, controls are labelled by design_type and
    # do not carry intervention == "linker_family_change".
    keep = (
        (design["design_type"].eq("chemistry_change") &
         design["intervention"].eq("linker_family_change")) |
        design["design_type"].eq("same_chemistry_control")
    )
    design = design.loc[keep].copy()

    primary_cols = ["id_a", "id_b", "pair_key", "related_group_id"] + GEOM
    primary = pd.read_parquet(PRIMARY, columns=primary_cols)
    primary["id_a"] = canonical_id(primary["id_a"])
    primary["id_b"] = canonical_id(primary["id_b"])
    primary["pair_key"] = pair_key(primary["id_a"], primary["id_b"])
    primary = primary.rename(columns={"related_group_id": "dependence_unit"})

    control_cols = ["id_a", "id_b"] + GEOM
    controls = pd.read_parquet(CONTROLS, columns=control_cols)
    controls["id_a"] = canonical_id(controls["id_a"])
    controls["id_b"] = canonical_id(controls["id_b"])
    controls["pair_key"] = pair_key(controls["id_a"], controls["id_b"])
    controls["dependence_unit"] = "control::" + controls["pair_key"].astype(str)

    chem = design.loc[design["design_type"].eq("chemistry_change")].merge(
        primary[["pair_key", "dependence_unit"] + GEOM], on="pair_key", how="left", validate="one_to_one"
    )
    ctrl = design.loc[design["design_type"].eq("same_chemistry_control")].merge(
        controls[["pair_key", "dependence_unit"] + GEOM], on="pair_key", how="left", validate="one_to_one"
    )
    out = pd.concat([chem, ctrl], ignore_index=True)
    if out[GEOM + ["dependence_unit"]].isna().any().any():
        bad = out.loc[out[GEOM + ["dependence_unit"]].isna().any(axis=1)]
        bad.to_csv(OUT / "03_failed_geometry_joins.csv", index=False)
        raise RuntimeError(f"Geometry/dependence join failed for {len(bad)} design pairs")
    for raw, frac in zip(GEOM, FRAC):
        out[frac] = pd.to_numeric(out[raw], errors="coerce") / LIMITS[raw]
    if out[FRAC].isna().any().any():
        raise RuntimeError("Non-numeric geometry differences after exact join")
    out["treatment"] = out["design_type"].eq("chemistry_change").astype(float)
    arm_counts = out.groupby("design_type")["pair_key"].nunique().to_dict()
    if not {"chemistry_change", "same_chemistry_control"}.issubset(arm_counts):
        raise RuntimeError(f"Both symmetric arms were not retained: {arm_counts}")
    return out


def load_adsorption(ids: set[str], targets: set[str]) -> pd.DataFrame:
    parts = []
    for path in sorted(RAW.glob("*.csv")):
        if path.stem not in RAW_TARGET_MAP:
            continue
        target = RAW_TARGET_MAP[path.stem]
        if target not in targets:
            continue
        cols = pd.read_csv(path, nrows=0).columns.tolist()
        if not all(c in cols for c in RAW_COLS):
            continue
        for ch in pd.read_csv(path, usecols=RAW_COLS, chunksize=CHUNKSIZE, low_memory=False):
            ch["mof_id"] = canonical_id(ch["filename"])
            ch = ch.loc[ch["mof_id"].isin(ids)].copy()
            if ch.empty:
                continue
            ch["target"] = target
            ch["T/K"] = pd.to_numeric(ch["T/K"], errors="coerce")
            ch["p/bar"] = pd.to_numeric(ch["p/bar"], errors="coerce")
            ch["uptake"] = pd.to_numeric(ch["mmol/g"], errors="coerce")
            parts.append(ch[["mof_id", "target", "T/K", "p/bar", "uptake"]])
    if not parts:
        raise RuntimeError("No adsorption rows matched symmetric-design endpoints")
    x = pd.concat(parts, ignore_index=True)
    key = ["mof_id", "target", "T/K", "p/bar"]
    dup = x.duplicated(key, keep=False)
    if dup.any():
        x.loc[dup].sort_values(key).to_csv(OUT / "03_duplicate_adsorption_keys.csv", index=False)
        raise RuntimeError("Duplicate adsorption keys found; no averaging performed")
    return x


def cell_crossproducts(df: pd.DataFrame, outcome: str, adjusted: bool):
    # Frisch-Waugh-Lovell within support cells. Each support cell receives equal
    # total weight, preventing large cells from dominating the estimand.
    cols = ["treatment"] + (FRAC if adjusted else [])
    pieces = []
    for cell, g in df.groupby("support_cell", sort=False):
        if g["treatment"].nunique() < 2:
            continue
        X = g[cols].to_numpy(float)
        y = g[outcome].to_numpy(float)
        ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
        X, y = X[ok], y[ok]
        if len(y) < len(cols) + 2 or np.unique(X[:, 0]).size < 2:
            continue
        # Remove cell intercept, then equalize total cell weight.
        X = X - X.mean(axis=0, keepdims=True)
        y = y - y.mean()
        scale = 1.0 / len(y)
        pieces.append((str(cell), X.T @ X * scale, X.T @ y * scale, len(y)))
    return cols, pieces


def solve_beta(pieces, indices=None):
    if indices is None:
        indices = range(len(pieces))
    xtx = sum((pieces[i][1] for i in indices), start=np.zeros_like(pieces[0][1]))
    xty = sum((pieces[i][2] for i in indices), start=np.zeros_like(pieces[0][2]))
    return np.linalg.lstsq(xtx, xty, rcond=None)[0]


def fit_one(key, g: pd.DataFrame, task_id: int) -> dict:
    target, temp, pressure, outcome = key
    base_cols, base = cell_crossproducts(g, outcome, adjusted=False)
    adj_cols, adj = cell_crossproducts(g, outcome, adjusted=True)
    common_cells = sorted(set(x[0] for x in base) & set(x[0] for x in adj))
    base_map = {x[0]: x for x in base}; adj_map = {x[0]: x for x in adj}
    base = [base_map[c] for c in common_cells]; adj = [adj_map[c] for c in common_cells]
    if len(common_cells) < MIN_MIXED_CELLS:
        return {"target": target, "T/K": temp, "p/bar": pressure, "effect_measure": outcome,
                "status": "INSUFFICIENT_MIXED_CELLS", "mixed_support_cells": len(common_cells)}
    b0 = solve_beta(base)[0]
    b1 = solve_beta(adj)[0]
    rng = np.random.default_rng(SEED + 101 * task_id)
    boot0 = np.empty(N_BOOT); boot1 = np.empty(N_BOOT)
    n = len(common_cells)
    failed = 0
    for i in range(N_BOOT):
        idx = rng.integers(0, n, n)
        try:
            boot0[i] = solve_beta(base, idx)[0]
            boot1[i] = solve_beta(adj, idx)[0]
        except Exception:
            boot0[i] = np.nan; boot1[i] = np.nan; failed += 1
    q0 = np.nanquantile(boot0, [0.025, 0.975])
    q1 = np.nanquantile(boot1, [0.025, 0.975])
    change = b1 - b0
    rel_change = change / abs(b0) if b0 != 0 else np.nan
    # A high condition number flags unstable geometry adjustment.
    xtx_adj = sum((x[1] for x in adj), start=np.zeros_like(adj[0][1]))
    condition_number = float(np.linalg.cond(xtx_adj))
    return {
        "target": target, "T/K": temp, "p/bar": pressure, "effect_measure": outcome,
        "status": "OK", "mixed_support_cells": n,
        "chemistry_pairs": int(g.loc[g["treatment"].eq(1), "pair_key"].nunique()),
        "control_pairs": int(g.loc[g["treatment"].eq(0), "pair_key"].nunique()),
        "unadjusted_linker_minus_control": float(b0),
        "unadjusted_bootstrap_95_low": float(q0[0]),
        "unadjusted_bootstrap_95_high": float(q0[1]),
        "adjusted_linker_minus_control": float(b1),
        "adjusted_bootstrap_95_low": float(q1[0]),
        "adjusted_bootstrap_95_high": float(q1[1]),
        "adjustment_change": float(change),
        "relative_adjustment_change": float(rel_change),
        "adjusted_design_condition_number": condition_number,
        "failed_bootstrap_replicates": failed,
    }


def main():
    require([DESIGN, PRIMARY, CONTROLS, SCALES])
    design = geometry_table()
    scales = pd.read_csv(SCALES)
    for c in ["T/K", "p/bar", "epsilon_primary", "robust_scale_iqr_over_1_349"]:
        scales[c] = pd.to_numeric(scales[c], errors="coerce")
    scales["target"] = scales["target"].astype("string")
    ids = set(design["id_a"]) | set(design["id_b"])
    adsorption = load_adsorption(ids, set(scales["target"].dropna().astype(str)))
    a = adsorption.rename(columns={"mof_id": "id_a", "uptake": "uptake_a"})
    b = adsorption.rename(columns={"mof_id": "id_b", "uptake": "uptake_b"})
    cond = ["target", "T/K", "p/bar"]
    grid = design.assign(_k=1).merge(scales.assign(_k=1), on="_k", how="inner").drop(columns="_k")
    grid = grid.merge(a, on=["id_a"] + cond, how="left", validate="many_to_one")
    grid = grid.merge(b, on=["id_b"] + cond, how="left", validate="many_to_one")
    grid["outcome_complete"] = grid["uptake_a"].notna() & grid["uptake_b"].notna()
    grid["absolute_uptake_difference"] = (grid["uptake_b"] - grid["uptake_a"]).abs()
    grid["absolute_log_difference"] = (
        np.log(grid["uptake_b"] + grid["epsilon_primary"]) -
        np.log(grid["uptake_a"] + grid["epsilon_primary"])
    ).abs()
    grid["standardized_absolute_difference"] = (
        grid["absolute_uptake_difference"] / grid["robust_scale_iqr_over_1_349"]
    )

    attrition = (grid.groupby(["target", "T/K", "p/bar", "design_type"], dropna=False)
                 .agg(expected_rows=("pair_key", "size"), complete_rows=("outcome_complete", "sum"),
                      pairs=("pair_key", "nunique"), support_cells=("support_cell", "nunique"))
                 .reset_index())
    attrition.to_csv(OUT / "03_attrition.csv", index=False)
    eligible = grid.loc[grid["outcome_complete"]].copy()

    # Preserve chemistry dependence by taking a median within related group;
    # controls are non-overlapping and each form their own dependence unit.
    group_cols = ["target", "T/K", "p/bar", "support_cell", "design_type", "treatment", "dependence_unit"]
    agg = {"pair_key": "first", **{c: "median" for c in FRAC + MEASURES}}
    analysis_data = eligible.groupby(group_cols, dropna=False).agg(agg).reset_index()
    analysis_data.to_csv(OUT / "03_cohort.csv", index=False)

    tasks = []
    for outcome in MEASURES:
        for key, g in analysis_data.groupby(["target", "T/K", "p/bar"], dropna=False):
            tasks.append(((key[0], key[1], key[2], outcome), g.copy()))
    results = Parallel(n_jobs=N_JOBS, prefer="processes")(
        delayed(fit_one)(key, g, i) for i, (key, g) in enumerate(tasks)
    )
    res = pd.DataFrame(results)
    res.to_csv(OUT / "03_results.csv", index=False)

    ok = res.loc[res["status"].eq("OK")].copy()
    summary = []
    for measure, g in ok.groupby("effect_measure"):
        summary.append({
            "effect_measure": measure,
            "conditions": len(g),
            "unadjusted_positive": int((g["unadjusted_linker_minus_control"] > 0).sum()),
            "unadjusted_intervals_above_zero": int((g["unadjusted_bootstrap_95_low"] > 0).sum()),
            "adjusted_positive": int((g["adjusted_linker_minus_control"] > 0).sum()),
            "adjusted_intervals_above_zero": int((g["adjusted_bootstrap_95_low"] > 0).sum()),
            "median_relative_adjustment_change": float(g["relative_adjustment_change"].median()),
            "maximum_absolute_relative_adjustment_change": float(g["relative_adjustment_change"].abs().max()),
            "maximum_condition_number": float(g["adjusted_design_condition_number"].max()),
        })
    summary = pd.DataFrame(summary)
    summary.to_csv(OUT / "03_summary.csv", index=False)

    stable = (not summary.empty and
              (summary["adjusted_positive"] == summary["conditions"]).all() and
              (summary["adjusted_intervals_above_zero"] >= 14).all() and
              (summary["maximum_condition_number"] < 1e8).all())
    decision = "ADJUSTED_LINKER_RESULT_SUPPORTED" if stable else "ADJUSTED_RESULT_REQUIRES_CAUTION"
    report = [
        "PROJECT 7B2 RESIDUAL-GEOMETRY-ADJUSTED LINKER SENSITIVITY",
        "=" * 72,
        f"Decision: {decision}",
        f"Linker chemistry pairs: {design.loc[design['design_type'].eq('chemistry_change'), 'pair_key'].nunique():,}",
        f"Same-chemistry control pairs: {design.loc[design['design_type'].eq('same_chemistry_control'), 'pair_key'].nunique():,}",
        f"Total symmetric design pairs: {design['pair_key'].nunique():,}",
        f"Complete pair-condition rows: {len(eligible):,}",
        f"Dependence-unit condition rows: {len(analysis_data):,}",
        "",
        summary.to_string(index=False),
        "",
        "Interpretation boundary:",
        "  The adjusted coefficient is an associational sensitivity estimate.",
        "  The frozen matched-control median contrast remains the primary result.",
        "  No pair, support cell, threshold, or adsorption value was reselected.",
        "  No missing scientific value was filled.",
    ]
    (OUT / "03_report.txt").write_text("\n".join(report), encoding="utf-8", newline="\n")
    manifest = {
        "stage": "Project 7B2 residual-geometry-adjusted linker sensitivity",
        "created": datetime.now().isoformat(timespec="seconds"),
        "script": "03_analyze_residual_geometry_adjustment.py",
        "n_jobs": N_JOBS, "bootstrap_replicates": N_BOOT, "seed": SEED,
        "inputs": {str(p): sha256(p) for p in [DESIGN, PRIMARY, CONTROLS, SCALES]},
        "geometry_covariates": GEOM,
        "effect_measures": MEASURES,
        "support_cell_fixed_effects": True,
        "equal_total_weight_per_support_cell": True,
        "missing_values_filled": False,
        "pair_reselection": False,
        "causal_claim": False,
        "decision": decision,
        "outputs": ["03_cohort.csv", "03_attrition.csv", "03_results.csv", "03_summary.csv", "03_report.txt"],
        "python": sys.version, "pandas": pd.__version__,
    }
    (OUT / "03_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
    print("\n".join(report))
    print(f"\nOutputs: {OUT}")

if __name__ == "__main__":
    main()
