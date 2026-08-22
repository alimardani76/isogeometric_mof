#!/usr/bin/env python3
"""
Project 7B2 Step 2, file 05: paired guest-specificity analysis.

Place inside:
    Step 2 chemistry strengthening/

Run from project root:
    python "Step 2 chemistry strengthening/05_analyze_guest_specificity.py"

Question
--------
Within the same frozen dependence families and corresponding low/high process
regimes, is chemistry-associated adsorption separation larger for CO2 than
for CH4, N2, or H2? Is the paired guest contrast accompanied by a difference
in absolute heat-of-adsorption contrast?

This directly evaluates H2 using existing observed data. It does not compare
unmatched families, fit a predictive model, assign substitution direction, or
claim a molecular mechanism.

Inputs
------
    analysis/corrected_group_effect_magnitudes.parquet
    Step 2 results/heat_analysis/matched_heat_group_data.parquet

Outputs
-------
    Step 2 results/guest_specificity/05_*.csv|txt|json
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
HEAT_DIR = ROOT / "Step 2 results" / "heat_analysis"
OUT = ROOT / "Step 2 results" / "guest_specificity"
OUT.mkdir(parents=True, exist_ok=True)

EFFECTS = ANALYSIS / "corrected_group_effect_magnitudes.parquet"
HEAT = HEAT_DIR / "matched_heat_group_data.parquet"

N_JOBS = 6
N_BOOT = 10_000
SEED = 5701
MIN_PAIRED_GROUPS = 30

MEASURES = ["absolute_log_difference", "standardized_absolute_difference"]
INTERVENTIONS = ["linker_family_change", "metal_substitution"]

# Exact process-regime pairing. Gas conditions are not assumed numerically
# identical; they are paired according to the process definitions represented
# in the frozen ARC--MOF adsorption files.
COMPARISONS = [
    {
        "comparison": "landfill_CO2_vs_CH4",
        "guest_a": "landfill_CO2", "guest_b": "landfill_CH4", "T/K": 338.0,
        "low_a": 0.26, "high_a": 3.2, "low_b": 0.01, "high_b": 4.4,
        "guest_class": "CO2_vs_CH4",
    },
    {
        "comparison": "methane_purification_CO2_vs_CH4",
        "guest_a": "methane_purification_CO2", "guest_b": "methane_purification_CH4", "T/K": 298.0,
        "low_a": 0.1, "high_a": 1.0, "low_b": 0.9, "high_b": 9.0,
        "guest_class": "CO2_vs_CH4",
    },
    {
        "comparison": "post_combustion_CO2_vs_N2",
        "guest_a": "post_combustion_CO2", "guest_b": "post_combustion_N2", "T/K": 298.0,
        "low_a": 0.015, "high_a": 0.15, "low_b": 0.075, "high_b": 0.75,
        "guest_class": "CO2_vs_N2",
    },
    {
        "comparison": "pre_combustion_CO2_vs_H2",
        "guest_a": "pre_combustion_CO2", "guest_b": "pre_combustion_H2", "T/K": 313.0,
        "low_a": 0.4, "high_a": 16.0, "low_b": 0.6, "high_b": 24.0,
        "guest_class": "CO2_vs_H2",
    },
]


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


def get_condition(df, intervention, target, temp, pressure, value_col):
    x = df.loc[
        df["intervention"].eq(intervention)
        & df["target"].eq(target)
        & np.isclose(df["T/K"].astype(float), temp)
        & np.isclose(df["p/bar"].astype(float), pressure),
        ["dependence_family_id", value_col],
    ].copy()
    if x["dependence_family_id"].duplicated().any():
        raise RuntimeError(
            f"Duplicate group-condition rows for {intervention}, {target}, {temp}, {pressure}, {value_col}"
        )
    return x


def paired_table(df, intervention, comp, regime, value_col):
    pa = comp[f"{regime}_a"]
    pb = comp[f"{regime}_b"]
    a = get_condition(df, intervention, comp["guest_a"], comp["T/K"], pa, value_col)
    b = get_condition(df, intervention, comp["guest_b"], comp["T/K"], pb, value_col)
    a = a.rename(columns={value_col: "value_CO2"})
    b = b.rename(columns={value_col: "value_coguest"})
    paired = a.merge(b, on="dependence_family_id", how="inner", validate="one_to_one")
    paired["paired_difference_CO2_minus_coguest"] = paired["value_CO2"] - paired["value_coguest"]
    paired["CO2_greater"] = paired["paired_difference_CO2_minus_coguest"] > 0
    return paired


def bootstrap_paired(values, seed):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return (np.nan,) * 6
    estimate = float(np.median(values))
    mean_est = float(np.mean(values))
    positive_fraction = float(np.mean(values > 0))
    rng = np.random.default_rng(seed)
    med = np.empty(N_BOOT); mean = np.empty(N_BOOT); frac = np.empty(N_BOOT)
    n = len(values)
    for i in range(N_BOOT):
        sample = values[rng.integers(0, n, n)]
        med[i] = np.median(sample)
        mean[i] = np.mean(sample)
        frac[i] = np.mean(sample > 0)
    med_ci = np.quantile(med, [0.025, 0.975])
    mean_ci = np.quantile(mean, [0.025, 0.975])
    frac_ci = np.quantile(frac, [0.025, 0.975])
    return (
        estimate, float(med_ci[0]), float(med_ci[1]),
        mean_est, float(mean_ci[0]), float(mean_ci[1]),
        positive_fraction, float(frac_ci[0]), float(frac_ci[1]),
    )


def one_task(df, intervention, comp, regime, measure, quantity, task_id):
    paired = paired_table(df, intervention, comp, regime, measure)
    n = len(paired)
    base = {
        "quantity": quantity,
        "intervention": intervention,
        "comparison": comp["comparison"],
        "guest_class": comp["guest_class"],
        "regime": regime,
        "T/K": comp["T/K"],
        "CO2_target": comp["guest_a"],
        "coguest_target": comp["guest_b"],
        "CO2_pressure_bar": comp[f"{regime}_a"],
        "coguest_pressure_bar": comp[f"{regime}_b"],
        "measure": measure,
        "paired_groups": n,
    }
    if n < MIN_PAIRED_GROUPS:
        return {**base, "status": "INSUFFICIENT_PAIRED_GROUPS"}, paired
    vals = paired["paired_difference_CO2_minus_coguest"].to_numpy(float)
    stats = bootstrap_paired(vals, SEED + 101 * task_id)
    return {
        **base,
        "status": "OK",
        "median_CO2": float(paired["value_CO2"].median()),
        "median_coguest": float(paired["value_coguest"].median()),
        "median_paired_difference_CO2_minus_coguest": stats[0],
        "median_bootstrap_95_low": stats[1],
        "median_bootstrap_95_high": stats[2],
        "mean_paired_difference_CO2_minus_coguest": stats[3],
        "mean_bootstrap_95_low": stats[4],
        "mean_bootstrap_95_high": stats[5],
        "fraction_groups_CO2_greater": stats[6],
        "fraction_bootstrap_95_low": stats[7],
        "fraction_bootstrap_95_high": stats[8],
    }, paired


def main():
    require([EFFECTS, HEAT])
    effect_cols = [
        "intervention", "dependence_family_id", "target", "T/K", "p/bar",
        "absolute_log_difference", "standardized_absolute_difference",
    ]
    effects = pd.read_parquet(EFFECTS, columns=effect_cols)
    effects = effects.loc[effects["intervention"].isin(INTERVENTIONS)].copy()
    heat = pd.read_parquet(HEAT)
    heat = heat.loc[heat["intervention"].isin(INTERVENTIONS)].copy()

    # Exact uniqueness is required for paired family comparison.
    key = ["intervention", "dependence_family_id", "target", "T/K", "p/bar"]
    if effects.duplicated(key).any():
        raise RuntimeError("Effect input contains duplicate family-condition rows")
    if heat.duplicated(key).any():
        raise RuntimeError("Heat input contains duplicate family-condition rows")

    task_specs = []
    for intervention in INTERVENTIONS:
        for comp in COMPARISONS:
            for regime in ["low", "high"]:
                for measure in MEASURES:
                    task_specs.append((effects, intervention, comp, regime, measure, "adsorption_separation"))
                task_specs.append((heat, intervention, comp, regime, "absolute_hoa_difference", "heat_contrast"))

    output = Parallel(n_jobs=N_JOBS, prefer="processes")(
        delayed(one_task)(*spec, task_id=i) for i, spec in enumerate(task_specs)
    )
    result_rows = [x[0] for x in output]
    paired_tables = []
    for row, (_, paired) in zip(result_rows, output):
        if not paired.empty:
            meta_cols = {
                "quantity": row["quantity"], "intervention": row["intervention"],
                "comparison": row["comparison"], "regime": row["regime"],
                "measure": row["measure"],
            }
            paired_tables.append(paired.assign(**meta_cols))

    results = pd.DataFrame(result_rows)
    results.to_csv(OUT / "05_results.csv", index=False)
    if paired_tables:
        pd.concat(paired_tables, ignore_index=True).to_parquet(OUT / "05_paired_group_data.parquet", index=False)

    ok = results.loc[results["status"].eq("OK")].copy()
    summary_rows = []
    for quantity, q in ok.groupby("quantity"):
        for intervention, x in q.groupby("intervention"):
            for measure, y in x.groupby("measure"):
                summary_rows.append({
                    "quantity": quantity,
                    "intervention": intervention,
                    "measure": measure,
                    "comparisons": len(y),
                    "median_CO2_greater": int((y["median_paired_difference_CO2_minus_coguest"] > 0).sum()),
                    "median_intervals_above_zero": int((y["median_bootstrap_95_low"] > 0).sum()),
                    "median_intervals_below_zero": int((y["median_bootstrap_95_high"] < 0).sum()),
                    "median_fraction_groups_CO2_greater": float(y["fraction_groups_CO2_greater"].median()),
                    "minimum_paired_groups": int(y["paired_groups"].min()),
                })
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / "05_summary.csv", index=False)

    # H2 is supported only if CO2 exceeds co-guests consistently for adsorption
    # separation, not merely in isolated process comparisons.
    linker_log = ok.loc[
        ok["quantity"].eq("adsorption_separation")
        & ok["intervention"].eq("linker_family_change")
        & ok["measure"].eq("absolute_log_difference")
    ]
    linker_std = ok.loc[
        ok["quantity"].eq("adsorption_separation")
        & ok["intervention"].eq("linker_family_change")
        & ok["measure"].eq("standardized_absolute_difference")
    ]
    if (
        len(linker_log) == 8 and len(linker_std) == 8
        and (linker_log["median_bootstrap_95_low"] > 0).sum() >= 6
        and (linker_std["median_bootstrap_95_low"] > 0).sum() >= 6
    ):
        decision = "H2_SUPPORTED_ACROSS_MOST_PAIRED_PROCESS_REGIMES"
    elif (
        (linker_log["median_paired_difference_CO2_minus_coguest"] > 0).sum() >= 5
        or (linker_std["median_paired_difference_CO2_minus_coguest"] > 0).sum() >= 5
    ):
        decision = "H2_CONDITIONALLY_SUPPORTED"
    else:
        decision = "H2_NOT_SUPPORTED_AS_A_GENERAL_RULE"

    report = [
        "PROJECT 7B2 PAIRED GUEST-SPECIFICITY ANALYSIS", "=" * 72,
        f"Decision: {decision}",
        "",
        "SUMMARY", summary.to_string(index=False), "",
        "Interpretation boundary:",
        "  Comparisons are paired within the same frozen dependence families.",
        "  Low/high labels refer to corresponding process regimes, not equal pressure across gases.",
        "  A positive value means larger chemistry-associated separation for CO2 than the co-guest.",
        "  No gas model, pressure interpolation, pair reselection, imputation, or directional chemistry was used.",
    ]
    (OUT / "05_report.txt").write_text("\n".join(report), encoding="utf-8", newline="\n")

    manifest = {
        "stage": "Project 7B2 paired guest-specificity analysis",
        "created": datetime.now().isoformat(timespec="seconds"),
        "script": "05_analyze_guest_specificity.py",
        "n_jobs": N_JOBS, "bootstrap_replicates": N_BOOT, "seed": SEED,
        "inputs": {str(p): sha256(p) for p in [EFFECTS, HEAT]},
        "comparisons": COMPARISONS,
        "missing_values_filled": False,
        "pressure_interpolation": False,
        "pair_reselection": False,
        "directional_chemistry_assigned": False,
        "formal_p_values": False,
        "decision": decision,
        "outputs": ["05_results.csv", "05_paired_group_data.parquet", "05_summary.csv", "05_report.txt"],
        "python": sys.version, "pandas": pd.__version__,
    }
    (OUT / "05_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
    print("\n".join(report))
    print(f"\nOutputs: {OUT}")

if __name__ == "__main__":
    main()
