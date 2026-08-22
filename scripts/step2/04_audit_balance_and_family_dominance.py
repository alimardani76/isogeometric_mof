#!/usr/bin/env python3
"""
Project 7B2 Step 2, file 04: balance and family-dominance audit.

Place inside:
    Step 2 chemistry strengthening/

Run from project root:
    python "Step 2 chemistry strengthening/04_audit_balance_and_family_dominance.py"

Purpose
-------
A. Quantify measured-geometry balance between the linker chemistry arm and
   same-chemistry control arm in the frozen symmetric design.
B. Test whether linker and coordination-compatible metal effect magnitudes
   remain after excluding the largest and ten largest dependence families.

No matching, pair membership, threshold, or scientific value is changed.
No p-values, FDR procedure, prediction model, or causal estimator is used.

Outputs
-------
    Step 2 results/balance_family_dominance/04_*.csv|txt|json
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
OUT = ROOT / "Step 2 results" / "balance_family_dominance"
OUT.mkdir(parents=True, exist_ok=True)

DESIGN = ANALYSIS / "step5b_symmetric_control_design.parquet"
PRIMARY = ANALYSIS / "final_primary_pairs.parquet"
CONTROLS = ANALYSIS / "step3_same_chemistry_control_pairs.parquet"
GROUP_EFFECTS = ANALYSIS / "corrected_group_effect_magnitudes.parquet"

N_JOBS = 6
N_BOOT = 10_000
SEED = 4701

GEOM = ["Di_diff", "Df_diff", "Dif_diff", "Density_diff", "UC_volume_diff", "AVAf_diff", "POAVAf_diff"]
LIMITS = dict(zip(GEOM, [0.03, 0.03, 0.03, 0.05, 0.05, 0.03, 0.03]))
MEASURES = ["absolute_log_difference", "standardized_absolute_difference"]
INTERVENTIONS = ["linker_family_change", "metal_substitution"]


def canonical_id(s: pd.Series) -> pd.Series:
    return (s.astype("string").str.strip()
            .str.replace(r"(?i)\\.cif$", "", regex=True)
            .str.replace(r"(?i)_repeat$", "", regex=True))


def make_pair_key(a: pd.Series, b: pd.Series) -> pd.Series:
    return np.where(a <= b, a + " || " + b, b + " || " + a)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require(paths):
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing required input(s):\n" + "\n".join(missing))


def standardized_mean_difference(x1, x0):
    x1 = np.asarray(x1, dtype=float); x0 = np.asarray(x0, dtype=float)
    x1 = x1[np.isfinite(x1)]; x0 = x0[np.isfinite(x0)]
    if len(x1) < 2 or len(x0) < 2:
        return np.nan
    pooled = np.sqrt((np.var(x1, ddof=1) + np.var(x0, ddof=1)) / 2.0)
    if pooled == 0:
        return 0.0 if np.mean(x1) == np.mean(x0) else np.nan
    return float((np.mean(x1) - np.mean(x0)) / pooled)


def load_symmetric_geometry():
    design = pd.read_parquet(DESIGN)
    design["id_a"] = canonical_id(design["id_a"])
    design["id_b"] = canonical_id(design["id_b"])
    design["pair_key"] = make_pair_key(design["id_a"], design["id_b"])

    primary = pd.read_parquet(PRIMARY, columns=["id_a", "id_b"] + GEOM)
    primary["id_a"] = canonical_id(primary["id_a"])
    primary["id_b"] = canonical_id(primary["id_b"])
    primary["pair_key"] = make_pair_key(primary["id_a"], primary["id_b"])

    controls = pd.read_parquet(CONTROLS, columns=["id_a", "id_b"] + GEOM)
    controls["id_a"] = canonical_id(controls["id_a"])
    controls["id_b"] = canonical_id(controls["id_b"])
    controls["pair_key"] = make_pair_key(controls["id_a"], controls["id_b"])

    chem = design.loc[design["design_type"].eq("chemistry_change")].merge(
        primary[["pair_key"] + GEOM], on="pair_key", how="left", validate="one_to_one"
    )
    ctrl = design.loc[design["design_type"].eq("same_chemistry_control")].merge(
        controls[["pair_key"] + GEOM], on="pair_key", how="left", validate="one_to_one"
    )
    x = pd.concat([chem, ctrl], ignore_index=True)
    if x[GEOM].isna().any().any():
        x.loc[x[GEOM].isna().any(axis=1)].to_csv(OUT / "04_failed_geometry_joins.csv", index=False)
        raise RuntimeError("Geometry join failed; inspect 04_failed_geometry_joins.csv")
    for g in GEOM:
        x[g + "_fraction_of_limit"] = pd.to_numeric(x[g], errors="coerce") / LIMITS[g]
    return x


def balance_audit(x):
    rows = []
    # Main audit is intervention-specific: each chemistry class versus the same
    # frozen shared control arm. This avoids hiding a metal imbalance inside
    # the much larger linker arm.
    controls = x.loc[x["design_type"].eq("same_chemistry_control")]
    for intervention in INTERVENTIONS + ["functional_motif_change"]:
        chemistry = x.loc[
            x["design_type"].eq("chemistry_change") & x["intervention"].eq(intervention)
        ]
        if chemistry.empty:
            continue
        for g in GEOM:
            frac = g + "_fraction_of_limit"
            global_smd = standardized_mean_difference(chemistry[frac], controls[frac])
            cell_smd = []
            for cell in sorted(set(chemistry["support_cell"]) & set(controls["support_cell"])):
                a = chemistry.loc[chemistry["support_cell"].eq(cell), frac]
                b = controls.loc[controls["support_cell"].eq(cell), frac]
                s = standardized_mean_difference(a, b)
                if np.isfinite(s):
                    cell_smd.append(s)
            rows.append({
                "intervention": intervention,
                "geometry_variable": g,
                "chemistry_pairs": chemistry["pair_key"].nunique(),
                "control_pairs": controls["pair_key"].nunique(),
                "global_smd": global_smd,
                "absolute_global_smd": abs(global_smd) if np.isfinite(global_smd) else np.nan,
                "mixed_cells_with_estimable_smd": len(cell_smd),
                "median_cell_smd": float(np.median(cell_smd)) if cell_smd else np.nan,
                "median_absolute_cell_smd": float(np.median(np.abs(cell_smd))) if cell_smd else np.nan,
                "maximum_absolute_cell_smd": float(np.max(np.abs(cell_smd))) if cell_smd else np.nan,
                "fraction_cells_abs_smd_below_0_10": float(np.mean(np.abs(cell_smd) < 0.10)) if cell_smd else np.nan,
                "fraction_cells_abs_smd_below_0_20": float(np.mean(np.abs(cell_smd) < 0.20)) if cell_smd else np.nan,
            })
    return pd.DataFrame(rows)


def bootstrap_median(values, seed):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return np.nan, np.nan, np.nan
    est = float(np.median(values))
    rng = np.random.default_rng(seed)
    out = np.empty(N_BOOT)
    n = len(values)
    for i in range(N_BOOT):
        out[i] = np.median(values[rng.integers(0, n, n)])
    lo, hi = np.quantile(out, [0.025, 0.975])
    return est, float(lo), float(hi)


def family_task(key, g, rank_map, task_id):
    intervention, target, temp, pressure, measure = key
    scenarios = {
        "all_groups": set(g["dependence_family_id"]),
        "exclude_largest": set(g.loc[g["family_rank"] > 1, "dependence_family_id"]),
        "exclude_top_10": set(g.loc[g["family_rank"] > 10, "dependence_family_id"]),
    }
    result = []
    for j, (scenario, keep) in enumerate(scenarios.items()):
        vals = g.loc[g["dependence_family_id"].isin(keep), measure].to_numpy(float)
        est, lo, hi = bootstrap_median(vals, SEED + task_id * 37 + j)
        result.append({
            "intervention": intervention, "target": target, "T/K": temp, "p/bar": pressure,
            "effect_measure": measure, "scenario": scenario,
            "groups": len(np.unique(g.loc[g["dependence_family_id"].isin(keep), "dependence_family_id"])),
            "median_effect": est, "bootstrap_95_low": lo, "bootstrap_95_high": hi,
        })
    return result


def family_dominance_audit():
    cols = ["intervention", "dependence_family_id", "target", "T/K", "p/bar", "raw_pair_rows"] + MEASURES
    g = pd.read_parquet(GROUP_EFFECTS, columns=cols)
    g = g.loc[g["intervention"].isin(INTERVENTIONS)].copy()
    # Family size is fixed from maximum raw-pair support across conditions.
    sizes = (g.groupby(["intervention", "dependence_family_id"], as_index=False)
             ["raw_pair_rows"].max()
             .rename(columns={"raw_pair_rows": "family_raw_pair_support"}))
    sizes["family_rank"] = sizes.groupby("intervention")["family_raw_pair_support"].rank(
        method="first", ascending=False
    ).astype(int)
    g = g.merge(sizes, on=["intervention", "dependence_family_id"], validate="many_to_one")
    tasks = []
    for measure in MEASURES:
        for key, x in g.groupby(["intervention", "target", "T/K", "p/bar"], dropna=False):
            tasks.append(((key[0], key[1], key[2], key[3], measure), x.copy()))
    nested = Parallel(n_jobs=N_JOBS, prefer="processes")(
        delayed(family_task)(key, x, None, i) for i, (key, x) in enumerate(tasks)
    )
    results = pd.DataFrame([row for group in nested for row in group])
    return sizes, results


def main():
    require([DESIGN, PRIMARY, CONTROLS, GROUP_EFFECTS])
    geom = load_symmetric_geometry()
    balance = balance_audit(geom)
    balance.to_csv(OUT / "04_balance.csv", index=False)

    sizes, family = family_dominance_audit()
    sizes.to_csv(OUT / "04_family_sizes.csv", index=False)
    family.to_csv(OUT / "04_family_exclusion_results.csv", index=False)

    # Compare exclusion scenarios against the all-groups median.
    pivot = family.pivot_table(
        index=["intervention", "target", "T/K", "p/bar", "effect_measure"],
        columns="scenario", values="median_effect"
    ).reset_index()
    pivot["largest_relative_change"] = (
        (pivot["exclude_largest"] - pivot["all_groups"]) / pivot["all_groups"].abs()
    )
    pivot["top10_relative_change"] = (
        (pivot["exclude_top_10"] - pivot["all_groups"]) / pivot["all_groups"].abs()
    )
    pivot.to_csv(OUT / "04_family_exclusion_comparison.csv", index=False)

    summary_rows = []
    for intervention, x in pivot.groupby("intervention"):
        for measure, y in x.groupby("effect_measure"):
            summary_rows.append({
                "intervention": intervention,
                "effect_measure": measure,
                "conditions": len(y),
                "all_positive": int((y["all_groups"] > 0).sum()),
                "exclude_largest_positive": int((y["exclude_largest"] > 0).sum()),
                "exclude_top10_positive": int((y["exclude_top_10"] > 0).sum()),
                "median_abs_relative_change_excluding_largest": float(y["largest_relative_change"].abs().median()),
                "max_abs_relative_change_excluding_largest": float(y["largest_relative_change"].abs().max()),
                "median_abs_relative_change_excluding_top10": float(y["top10_relative_change"].abs().median()),
                "max_abs_relative_change_excluding_top10": float(y["top10_relative_change"].abs().max()),
            })
    family_summary = pd.DataFrame(summary_rows)
    family_summary.to_csv(OUT / "04_family_exclusion_summary.csv", index=False)

    balance_summary = (balance.groupby("intervention", as_index=False)
        .agg(max_absolute_global_smd=("absolute_global_smd", "max"),
             median_absolute_cell_smd=("median_absolute_cell_smd", "median"),
             worst_maximum_absolute_cell_smd=("maximum_absolute_cell_smd", "max"),
             minimum_fraction_cells_below_0_10=("fraction_cells_abs_smd_below_0_10", "min"),
             minimum_fraction_cells_below_0_20=("fraction_cells_abs_smd_below_0_20", "min")))
    balance_summary.to_csv(OUT / "04_balance_summary.csv", index=False)

    report = [
        "PROJECT 7B2 BALANCE AND FAMILY-DOMINANCE AUDIT", "=" * 72,
        "BALANCE SUMMARY", balance_summary.to_string(index=False), "",
        "FAMILY-EXCLUSION SUMMARY", family_summary.to_string(index=False), "",
        "Interpretation boundary:",
        "  SMD is reported as a diagnostic, not a new acceptance threshold.",
        "  Family exclusions retain frozen group-level outcomes and do not rerun matching.",
        "  No p-values, FDR correction, prediction model, pair reselection, or imputation was used.",
    ]
    (OUT / "04_report.txt").write_text("\n".join(report), encoding="utf-8", newline="\n")

    manifest = {
        "stage": "Project 7B2 balance and family-dominance audit",
        "created": datetime.now().isoformat(timespec="seconds"),
        "script": "04_audit_balance_and_family_dominance.py",
        "n_jobs": N_JOBS, "bootstrap_replicates": N_BOOT, "seed": SEED,
        "inputs": {str(p): sha256(p) for p in [DESIGN, PRIMARY, CONTROLS, GROUP_EFFECTS]},
        "missing_values_filled": False, "pair_reselection": False,
        "new_matching": False, "p_values_used": False, "fdr_used": False,
        "outputs": [
            "04_balance.csv", "04_balance_summary.csv", "04_family_sizes.csv",
            "04_family_exclusion_results.csv", "04_family_exclusion_comparison.csv",
            "04_family_exclusion_summary.csv", "04_report.txt"
        ],
        "python": sys.version, "pandas": pd.__version__,
    }
    (OUT / "04_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
    print("\n".join(report))
    print(f"\nOutputs: {OUT}")

if __name__ == "__main__":
    main()
