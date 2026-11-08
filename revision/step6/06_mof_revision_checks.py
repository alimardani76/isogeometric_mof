#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project 7B2 | Step 6 | Statistical revision checks (06_mof_revision_checks.py).

Place this file at:
  <7B2>/Step 6 revision/06_mof_revision_checks.py

Run from PowerShell (quoted paths are important):
  py "<7B2>/Step 6 revision/06_mof_revision_checks.py" --mode all --bootstrap 1000

Required existing inputs, which are never changed:
  7B2/analysis/process_translation_pair_results_final.parquet
  7B2/analysis/process_translation_summary_final.csv   [frozen verification]
  7B2/Step 2 results/residual_adjustment/03_cohort.csv
  7B2/Step 2 results/residual_adjustment/03_results.csv [frozen verification]

Outputs: 7B2/Step 6 revision/results/ (CSV, report MD, JSON manifest).
Dependencies: Python >= 3.10; numpy, pandas, pyarrow.
  py -m pip install numpy pandas pyarrow

SCIENTIFIC BOUNDARIES
  * No raw data, matching, chemistry, RASPA, or manuscript inputs are changed.
  * C012: distinguish genuine sign reversals, process-metric ties, uptake ties,
    and missing endpoint data. Report raw pair counts and equal-family-weight
    percentages; verify historical group-weighted concordance exactly.
  * C011: use frozen 03_cohort.csv, the SAME 7 normalized geometry descriptors,
    outcomes and support cells; compare the original additive LINEAR model with
    outcome-independent additive QUADRATIC and PIECEWISE-LINEAR SPLINE models.
    No propensity fitting, outcome-based threshold selection, or pair reselection.
  * For uncertainty, resample complete support cells (as in historical Step 2),
    after the original family-median aggregation. This does NOT establish causal
    effects or resolve unmeasured geometry. CIs of nonlinear fits are sensitivity
    diagnostics, not a replacement for the frozen 10,000-bootstrap main results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

G = ["g_Di", "g_Df", "g_Dif", "g_Density", "g_UC_volume", "g_AVAf", "g_POAVAf"]
OUTCOMES = ["absolute_log_difference", "standardized_absolute_difference"]
PROCESS_METRICS = (
    ("working_capacity", "uptake_working_capacity_concordant"),
    ("selectivity", "uptake_selectivity_concordant"),
)
# Freeze feature expansion before looking at adsorption outcomes.
SPLINE_KNOTS = (1.0 / 3.0, 2.0 / 3.0)
MIN_MIXED_CELLS = 8
MAX_COND = 1e8
VERIFICATION_TOL = 1e-8


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def require_cols(df: pd.DataFrame, cols: List[str], name: str) -> None:
    missing = sorted(set(cols) - set(df.columns))
    if missing:
        raise ValueError(f"{name} missing required column(s): {missing}")


def as_bool(s: pd.Series, name: str) -> pd.Series:
    """Accept native Boolean columns; never coerce a literal 'False' to True."""
    if pd.api.types.is_bool_dtype(s) or str(s.dtype) == "boolean":
        return s.astype("boolean").fillna(False).astype(bool)
    if pd.api.types.is_numeric_dtype(s):
        ok = s.isna() | s.isin([0, 1])
        if not bool(ok.all()):
            raise ValueError(f"{name} has non-Boolean numbers")
        return s.fillna(0).astype(bool)
    mapping = {"true": True, "false": False, "1": True, "0": False}
    out = s.astype("string").str.strip().str.lower().map(mapping)
    if bool((s.notna() & out.isna()).any()):
        raise ValueError(f"{name} has unexpected Boolean strings")
    return out.fillna(False).astype(bool)


def ci_group_mean(v: np.ndarray, rng: np.random.Generator, reps: int) -> Tuple[float, float]:
    """Bootstrap dependence-family rates, not nominal pair rows."""
    v = np.asarray(v, dtype=float)
    if not np.isfinite(v).all() or len(v) == 0:
        return (float("nan"), float("nan"))
    if len(v) == 1:
        return float(v[0]), float(v[0])
    draws = np.empty(reps, float)
    k = 0
    while k < reps:
        batch = min(128, reps - k)
        inds = rng.integers(0, len(v), size=(batch, len(v)))
        draws[k:k + batch] = v[inds].mean(axis=1)
        k += batch
    return tuple(float(x) for x in np.quantile(draws, [0.025, 0.975]))


def run_process(root: Path, dest: Path, reps: int, seed: int) -> Dict:
    """C012: exact reversal vs tie counts, plus historical-concordance verification."""
    pair_file = root / "analysis" / "process_translation_pair_results_final.parquet"
    reference_file = root / "analysis" / "process_translation_summary_final.csv"
    if not pair_file.is_file() or not reference_file.is_file():
        raise FileNotFoundError(f"C012 requires BOTH:\n  {pair_file}\n  {reference_file}")
    print("[C012] Reading frozen pair-level process results...", flush=True)
    cols = ["id_a", "id_b", "intervention", "process", "related_group_id",
            "uptake_a", "uptake_b", "uptake_pair_complete"]
    for metric, historical in PROCESS_METRICS:
        cols += [f"{metric}_a", f"{metric}_b", f"{metric}_pair_complete", historical]
    df = pd.read_parquet(pair_file)
    require_cols(df, cols, str(pair_file))
    if df["related_group_id"].isna().any():
        raise ValueError("Missing related_group_id: cannot reproduce group weighting")
    if df.duplicated(subset=["id_a", "id_b", "intervention", "process"]).any():
        raise ValueError("Duplicate pair/process keys in frozen process file")

    for c in ["uptake_pair_complete"] + [f"{x}_pair_complete" for x, _ in PROCESS_METRICS]:
        df[c] = as_bool(df[c], c)
    for _, c in PROCESS_METRICS:
        if str(df[c].dtype) != "boolean":
            df[c] = df[c].astype("boolean")
    for c in ["uptake_a", "uptake_b"] + [f"{m}_{ab}" for m, _ in PROCESS_METRICS for ab in "ab"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    ref = pd.read_csv(reference_file)
    require_cols(ref, ["intervention", "process", "metric", "estimate"], str(reference_file))
    frozen = {(str(r.intervention), str(r.process), str(r.metric)): float(r.estimate)
              for r in ref.itertuples(index=False)}
    rows: List[Dict] = []
    mismatches: List[Dict] = []
    rng = np.random.default_rng(seed)

    for (intervention, process), pg in df.groupby(["intervention", "process"], sort=True, dropna=False):
        ud = pg["uptake_b"].to_numpy(float) - pg["uptake_a"].to_numpy(float)
        uvalid = pg["uptake_pair_complete"].to_numpy(bool) & np.isfinite(ud)
        untie = uvalid & (ud != 0)
        for metric, historical in PROCESS_METRICS:
            md = pg[f"{metric}_b"].to_numpy(float) - pg[f"{metric}_a"].to_numpy(float)
            mvalid = pg[f"{metric}_pair_complete"].to_numpy(bool) & np.isfinite(md)
            eligible = untie & mvalid
            sign_product = np.sign(ud) * md
            conc = eligible & (sign_product > 0)
            rev = eligible & (sign_product < 0)
            tie = eligible & (sign_product == 0)
            n = int(eligible.sum())
            nconc, nrev, ntie = int(conc.sum()), int(rev.sum()), int(tie.sum())
            if n != nconc + nrev + ntie:
                raise AssertionError(f"Missing sign category in {intervention}/{process}/{metric}")
            # Confirm historic per-pair concordance (metric ties are FALSE, not
            # reverse; uptake ties are excluded), before calculating group rates.
            reported = pg[historical].astype("boolean")
            actual = np.where(sign_product > 0, True, False)
            conflicting = eligible & (reported.isna().to_numpy() | (reported.fillna(False).to_numpy(bool) != actual))
            if conflicting.any():
                raise AssertionError(f"Historical concordance column differs in {int(conflicting.sum())} valid rows: "
                                     f"{intervention}/{process}/{metric}")
            if n == 0:
                rows.append({"intervention": intervention, "process": process, "metric": metric,
                             "status": "NO_VALID_COMPARISONS", "expected_rows": len(pg),
                             "eligible_pairs": 0, "uptake_ties": int((uvalid & (ud == 0)).sum()),
                             "missing_or_invalid_metric_or_uptake": int((~uvalid | ~mvalid).sum())})
                continue
            picked = pd.DataFrame({
                "group": pg.loc[eligible, "related_group_id"].to_numpy(),
                "concordant": conc[eligible].astype(float),
                "reverse": rev[eligible].astype(float),
                "metric_tie": tie[eligible].astype(float),
            })
            gr = picked.groupby("group", sort=True).mean(numeric_only=True)
            gw_conc = float(gr["concordant"].mean())
            gw_rev = float(gr["reverse"].mean())
            gw_tie = float(gr["metric_tie"].mean())
            if not np.isclose(gw_conc + gw_rev + gw_tie, 1, atol=1e-12):
                raise AssertionError("Group proportions do not sum to one")
            historical_est = frozen.get((intervention, process, historical), float("nan"))
            diff = abs(historical_est - gw_conc)
            if not np.isfinite(historical_est) or diff > VERIFICATION_TOL:
                mismatches.append({"intervention": intervention, "process": process,
                                   "metric": metric, "reported_concordance": historical_est,
                                   "recomputed_concordance": gw_conc, "absolute_difference": diff})
            low, high = ci_group_mean(gr["reverse"].to_numpy(float), rng, reps)
            rows.append({
                "intervention": intervention, "process": process, "metric": metric, "status": "OK",
                "expected_rows": int(len(pg)), "complete_uptake_pairs": int(uvalid.sum()),
                "uptake_ties": int((uvalid & (ud == 0)).sum()),
                "missing_or_invalid_metric_or_uptake": int((~uvalid | ~mvalid).sum()),
                "eligible_pairs": n, "concordant_pairs": nconc, "reversed_pairs": nrev,
                "process_metric_ties": ntie, "discordant_including_ties": nrev + ntie,
                "raw_pair_reversal_pct": 100.0 * nrev / n,
                "raw_pair_discordance_including_ties_pct": 100.0 * (nrev + ntie) / n,
                "raw_pair_concordance_pct": 100.0 * nconc / n,
                "dependence_families": int(len(gr)),
                "equal_family_reversal_pct": 100.0 * gw_rev,
                "equal_family_reversal_95_low_pct": 100.0 * low,
                "equal_family_reversal_95_high_pct": 100.0 * high,
                "equal_family_metric_tie_pct": 100.0 * gw_tie,
                "equal_family_concordance_pct": 100.0 * gw_conc,
                "frozen_family_concordance_pct": 100.0 * historical_est,
                "concordance_reproduction_error": diff,
            })

    out = pd.DataFrame(rows)
    out.to_csv(dest / "C012_exact_process_reversals.csv", index=False, float_format="%.12g")
    pd.DataFrame(mismatches, columns=["intervention", "process", "metric", "reported_concordance",
                                      "recomputed_concordance", "absolute_difference"]).to_csv(
                                          dest / "C012_reconciliation_failures.csv", index=False)
    if mismatches:
        raise RuntimeError(f"C012 FROZEN-SUMMARY RECONCILIATION FAILED for {len(mismatches)} rows. "
                           "See results/C012_reconciliation_failures.csv; do NOT cite revision counts.")
    return {"input": str(pair_file), "reference": str(reference_file),
            "summary_csv": "C012_exact_process_reversals.csv", "rows": len(out),
            "reconciled_to_frozen_summary": True, "results": out}


def feature_matrix(x: np.ndarray, treatment: np.ndarray, model: str) -> np.ndarray:
    """Nonlinear basis is determined without any adsorption outcome information."""
    xs = [treatment.reshape(-1, 1), x]
    if model == "linear":
        pass
    elif model == "quadratic":
        xs.append(x * x)
    elif model == "piecewise_linear_spline":
        for knot in SPLINE_KNOTS:
            xs.append(np.maximum(0.0, x - knot))
    elif model == "unadjusted":
        return treatment.reshape(-1, 1)
    else:
        raise ValueError(f"Unknown model {model}")
    return np.column_stack(xs)


def solve(products: np.ndarray, rhs: np.ndarray) -> Tuple[np.ndarray, float, int]:
    beta = np.linalg.lstsq(products, rhs, rcond=None)[0]
    cond = float(np.linalg.cond(products))
    rank = int(np.linalg.matrix_rank(products))
    return beta, cond, rank


def bootstrap_cell_coefficients(As: np.ndarray, Bs: np.ndarray,
                                counts: np.ndarray) -> Tuple[np.ndarray, int]:
    """Resample whole support cells; no row-wise bootstrap."""
    nboot, ncells = counts.shape
    if As.shape[0] != ncells or Bs.shape[0] != ncells:
        raise ValueError("Cell-bootstrap matrices are misaligned")
    draws = np.full(nboot, np.nan, dtype=float)
    failed = 0
    # Batch matrix aggregation to avoid allocating large intermediate tensors.
    for start in range(0, nboot, 128):
        take = counts[start:start+128]
        AA = np.einsum("rc,cij->rij", take, As, optimize=True)
        bb = np.einsum("rc,ci->ri", take, Bs, optimize=True)
        for j in range(len(take)):
            if np.linalg.matrix_rank(AA[j]) < AA.shape[-1]:
                failed += 1
                continue
            try:
                draws[start+j] = float(np.linalg.solve(AA[j], bb[j])[0])
            except np.linalg.LinAlgError:
                failed += 1
    return draws, failed


def run_geometry(root: Path, dest: Path, reps: int, seed: int) -> Dict:
    """C011: verify original linear results then fit two fixed nonlinear bases."""
    folder = root / "Step 2 results" / "residual_adjustment"
    cohort_file = folder / "03_cohort.csv"
    original_file = folder / "03_results.csv"
    if not cohort_file.is_file() or not original_file.is_file():
        raise FileNotFoundError(f"C011 requires BOTH:\n  {cohort_file}\n  {original_file}")
    print("[C011] Reading frozen family-aggregated regression cohort (55 MB)...", flush=True)
    fields = ["target", "T/K", "p/bar", "support_cell", "treatment", *G, *OUTCOMES]
    d = pd.read_csv(cohort_file, low_memory=False)
    require_cols(d, fields, str(cohort_file))
    old = pd.read_csv(original_file, low_memory=False)
    require_cols(old, ["target", "T/K", "p/bar", "effect_measure", "status",
                       "unadjusted_linker_minus_control", "adjusted_linker_minus_control"], str(original_file))
    for k in ["T/K", "p/bar", "treatment", *G, *OUTCOMES]:
        d[k] = pd.to_numeric(d[k], errors="coerce")
    if (d["treatment"].isna() | ~d["treatment"].isin([0, 1])).any():
        raise ValueError("Cohort treatment must be exactly 0 or 1")
    if d["support_cell"].isna().any():
        raise ValueError("Missing support cell in 03_cohort.csv")
    if (d[G].isna() | ~np.isfinite(d[G])).any().any():
        raise ValueError("Missing or non-finite geometry in frozen cohort; do not impute")
    extreme = {g: int(((d[g] < -1e-8) | (d[g] > 1 + 1e-8)).sum()) for g in G}
    if any(extreme.values()):
        print(f"[C011] WARNING: some normalized geometry values fall outside [0,1]: {extreme}", flush=True)

    # Avoid attribute access: pandas may sanitize column names T/K and p/bar.
    old_map = {}
    for _, rec in old.iterrows():
        old_map[(str(rec["target"]), float(rec["T/K"]), float(rec["p/bar"]),
                 str(rec["effect_measure"]))] = rec
    rows: List[Dict] = []
    reconciliation: List[Dict] = []
    rng = np.random.default_rng(seed)
    models = ["unadjusted", "linear", "quadratic", "piecewise_linear_spline"]
    group_iter = d.groupby(["target", "T/K", "p/bar"], sort=True, dropna=False)
    total_conditions = len(group_iter)
    for condition_no, (key, group) in enumerate(group_iter, 1):
        target, temp, pressure = key
        print(f"[C011] Condition {condition_no}/{total_conditions}: {target} T={temp:g} p={pressure:g}", flush=True)
        for outcome in OUTCOMES:
            # The original fit filters missing outcomes independently by state.
            g = group.loc[np.isfinite(group[outcome].to_numpy(float))].copy()
            cells = []
            # Eligibility is EXACTLY the historical linear-adjusted threshold:
            # at least 7 geometry predictors + 1 treatment + 2 observations,
            # both arms present; same set is reused for every nonlinear fit.
            for cell, c in g.groupby("support_cell", sort=False):
                if len(c) < (1 + len(G) + 2) or c["treatment"].nunique() < 2:
                    continue
                cells.append((str(cell), c))
            cells.sort(key=lambda pair: pair[0])
            if len(cells) < MIN_MIXED_CELLS:
                raise RuntimeError(f"Fewer than {MIN_MIXED_CELLS} historically eligible mixed cells for "
                                   f"{target}/{temp}/{pressure}/{outcome}")
            n_cells = len(cells)
            count_draws = rng.multinomial(n_cells, np.full(n_cells, 1/n_cells), size=reps)
            fit = {}
            for model in models:
                products, rhss = [], []
                for _, c in cells:
                    x = c[G].to_numpy(float)
                    tr = c["treatment"].to_numpy(float)
                    y = c[outcome].to_numpy(float)
                    X = feature_matrix(x, tr, model)
                    Xc, yc = X - X.mean(axis=0), y - y.mean()
                    # Same Frisch-Waugh-Lovell within-support-cell calculation
                    # and equal total cell weight as the frozen analysis.
                    weight = 1.0 / len(y)
                    products.append((Xc.T @ Xc) * weight)
                    rhss.append((Xc.T @ yc) * weight)
                A = np.stack(products)
                B = np.stack(rhss)
                beta, cond, rank = solve(A.sum(axis=0), B.sum(axis=0))
                k = A.shape[1]
                stable = (rank == k and math.isfinite(cond) and cond < MAX_COND)
                # For unadjusted and linear fits, only point estimates are
                # needed: their authoritative CIs are the frozen 10k bootstrap.
                if model in ("quadratic", "piecewise_linear_spline") and stable:
                    draws, failed = bootstrap_cell_coefficients(A, B, count_draws)
                    finite = draws[np.isfinite(draws)]
                    if len(finite) >= max(50, int(0.8 * reps)):
                        low, high = (float(x) for x in np.quantile(finite, [.025, .975]))
                    else:
                        low, high = float("nan"), float("nan")
                else:
                    low, high, failed = float("nan"), float("nan"), 0
                fit[model] = {"value": float(beta[0]), "condition_number": cond,
                              "rank": rank, "design_columns": k, "stable": stable,
                              "bootstrap_95_low": low, "bootstrap_95_high": high,
                              "failed_bootstrap_replicates": failed}

            prior = old_map.get((str(target), float(temp), float(pressure), outcome))
            if prior is None or str(prior["status"]) != "OK":
                raise RuntimeError(f"Frozen result absent/non-OK for {target}/{temp}/{pressure}/{outcome}")
            for model, frozen_col in (("unadjusted", "unadjusted_linker_minus_control"),
                                      ("linear", "adjusted_linker_minus_control")):
                frozen = float(prior[frozen_col]); computed = fit[model]["value"]
                error = abs(frozen - computed)
                reconciliation.append({"target": target, "T/K": temp, "p/bar": pressure,
                                       "effect_measure": outcome, "model": model,
                                       "frozen": frozen, "reproduced": computed,
                                       "absolute_error": error,
                                       "pass": bool(error <= VERIFICATION_TOL)})
            for model in models:
                f = fit[model]
                baseline = fit["unadjusted"]["value"]
                if baseline == 0:
                    rel = float("nan")
                else:
                    rel = (f["value"] - baseline) / abs(baseline)
                rows.append({"target": target, "T/K": temp, "p/bar": pressure,
                             "effect_measure": outcome, "model": model,
                             "mixed_support_cells": n_cells,
                             "n_family_median_rows": int(sum(len(c) for _, c in cells)),
                             "coefficient": f["value"], "bootstrap_95_low": f["bootstrap_95_low"],
                             "bootstrap_95_high": f["bootstrap_95_high"],
                             "attenuation_fraction_from_unadjusted": -rel,
                             "condition_number": f["condition_number"],
                             "design_rank": f["rank"], "design_columns": f["design_columns"],
                             "stable_condition_and_full_rank": f["stable"],
                             "failed_bootstrap_replicates": f["failed_bootstrap_replicates"]})

    rr = pd.DataFrame(reconciliation)
    rr.to_csv(dest / "C011_frozen_linear_reconciliation.csv", index=False, float_format="%.12g")
    if not rr["pass"].all():
        raise RuntimeError("C011 original LINEAR COEFFICIENT REPRODUCTION FAILED; "
                           "see results/C011_frozen_linear_reconciliation.csv. "
                           "Do not interpret nonlinear fits until the mismatch is resolved.")
    out = pd.DataFrame(rows)
    out.to_csv(dest / "C011_nonlinear_geometry_by_condition.csv", index=False, float_format="%.12g")
    summary_rows = []
    for (effect_measure, model), t in out.groupby(["effect_measure", "model"], sort=True):
        ok = t["stable_condition_and_full_rank"].astype(bool)
        good = t.loc[ok]
        ci_complete = good["bootstrap_95_low"].notna()
        summary_rows.append({
            "effect_measure": effect_measure, "model": model, "conditions": len(t),
            "stable_full_rank_conditions": int(ok.sum()),
            "positive_stable_conditions": int((good["coefficient"] > 0).sum()),
            "nonlinear_intervals_above_zero": int((good["bootstrap_95_low"] > 0).sum()),
            "conditions_with_nonlin_ci": int(ci_complete.sum()),
            "median_attenuation_fraction_stable": float(good["attenuation_fraction_from_unadjusted"].median())
            if len(good) else float("nan"),
            "max_design_condition_number": float(t["condition_number"].max()),
        })
    summ = pd.DataFrame(summary_rows)
    summ.to_csv(dest / "C011_nonlinear_geometry_summary.csv", index=False, float_format="%.12g")
    return {"input": str(cohort_file), "reference": str(original_file),
            "frozen_linear_reproduced": True, "max_reproduction_error": float(rr["absolute_error"].max()),
            "normalized_geometry_out_of_range_rows_by_feature": extreme,
            "conditions": total_conditions, "summary": summ, "results": out}


def make_report(root: Path, dest: Path, process: Dict | None, geometry: Dict | None, reps: int) -> None:
    report = [
        "# Step 6 | Ashleigh Fletcher reviewer checks (C011, C012)", "",
        f"Run time: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Project root: `{root}`", "",
        "## Scientific scope and interpretation", "",
        "- Existing source records, matching, and simulations have **not** been recomputed or altered.",
        "- Pair-level reversal counts are **descriptive**; population summaries use equally weighted framework-connected families.",
        "- A process-metric tie is **not** a direction reversal. Uptake ties are excluded from direction comparisons.",
        "- The 36–40% original attenuation is **associational**, not a causal mediation percentage.",
        "- Both nonlinear specifications use prespecified outcome-independent basis expansions of the original seven normalized geometry differences.",
        "- Bootstrap unit for geometry sensitivity is the **support cell**, matching the original Step 2 regression workflow after dependence-family aggregation.",
        f"- New interval estimates use {reps} cell/group bootstrap draws; the original 10,000-draw main analysis remains authoritative.", "",
    ]
    if process:
        a = process["results"]
        report += ["## C012 — exact uptake-to-process reversals", "",
                   "FROZEN-SUMMARY RECONCILIATION: **PASS**.",
                   "`C012_exact_process_reversals.csv` contains all class/process/metric rows, exact denominators, "
                   "reverse counts, metric ties, uptake ties, raw pair percentages, equal-family percentages and bootstrap intervals.", "",
                   "**Key: `reversed_pairs` counts strictly negative uptake-oriented process changes. "
                   "`discordant_including_ties` also counts zero process changes and must not be called reversals.**", ""]
        b = a[(a["status"] == "OK") & a["intervention"].isin(["linker_family_change", "metal_substitution"])]
        report += ["| Chemistry class | Process | Metric | Reversed / eligible | Raw reversal % | Equal-family reversal % | Metric ties |",
                   "|---|---|---|---:|---:|---:|---:|"]
        for _, r in b.iterrows():
            report.append(f"| {r['intervention']} | {r['process']} | {r['metric']} | "
                          f"{int(r['reversed_pairs'])}/{int(r['eligible_pairs'])} | "
                          f"{r['raw_pair_reversal_pct']:.2f}% | {r['equal_family_reversal_pct']:.2f}% | "
                          f"{int(r['process_metric_ties'])} |")
        report += ["", "**Manuscript placement:** §2.5, immediately after reporting the concordance ranges. "
                   "State counts and denominators for the five process definitions; use the same unit throughout. "
                   "Retain the frozen family-weighted concordance estimates in Figure 4/SI Table S8.", ""]
    if geometry:
        a = geometry["summary"]
        report += ["## C011 — nonlinear residual geometry sensitivity", "",
                   "FROZEN LINEAR POINT-ESTIMATE RECONCILIATION: **PASS** ",
                   f"Maximum absolute discrepancy: {geometry['max_reproduction_error']:.3e}.",
                   "", "| Effect scale | Model | Stable states / 18 | Positive in stable states | Median attenuation |",
                   "|---|---|---:|---:|---:|"]
        for _, r in a.iterrows():
            att = r["median_attenuation_fraction_stable"]
            fmt = f"{100*att:.1f}%" if pd.notna(att) else "not estimable"
            report.append(f"| {r['effect_measure']} | {r['model']} | "
                          f"{int(r['stable_full_rank_conditions'])}/{int(r['conditions'])} | "
                          f"{int(r['positive_stable_conditions'])} | {fmt} |")
        report += ["", "**Do not automatically replace the paper's 36–40% figure.** These nonlinear fits are "
                   "sensitivity checks. If the nonlinear coefficient is unstable, crosses zero, or differs materially, "
                   "report that limitation without reinterpretation or further model tuning.",
                   "Use `C011_nonlinear_geometry_by_condition.csv` for state-wise coefficients, "
                   "ranks, condition numbers and confidence intervals.", ""]
    report += [
        "## Other Overleaf comments — does any additional computation become necessary?", "",
        "- **C001, C003, C006, C010:** no numerical analysis. Revise observational language; define "
        "same-chemistry as sameness of *represented labels*; identify the six motif cases as exploratory; "
        "state explicitly that packing/site mechanisms were not tested.",
        "- **C002, C004, C005, C007, C008:** editorial framing, spelling, hyphenation, and consistent "
        "qualification of the two 36%/40% scales. C008 is also checked numerically against the frozen linear regression.",
        "- **C009:** **figure-accessibility audit required**, but no adsorption/statistical rerun. "
        "Check every final PDF/figure in grayscale and distinguish series by marker shape, fill, and line style.",
        "- **C013:** **selection-protocol documentation audit required**, not a new model. "
        "Inspect the existing `scripts/step1/24_select_structure_cases.py` and "
        "`scripts/step3/01_prepare_final_case_selection.py` plus the frozen shortlist/selection ledger. "
        "Do not invent an outcome-blind or prespecified selection protocol: cases were deliberately selected to "
        "illustrate strong, near-null and boundary examples.",
        "- **C014:** **coordination-filter evidence audit required** but no new CrystalNN/DFT calculation by default. "
        "Use the existing two-setting classification and ChemEnv audit; describe agreement as a conservative "
        "algorithmic criterion, not proof of equivalent physical adsorption sites. New coordination calculations "
        "would only be justified if the existing ledgers fail to establish the stated exclusions.",
        "", "## Files", "",
        "- `C012_exact_process_reversals.csv` and `C012_reconciliation_failures.csv` (when C012 run)",
        "- `C011_frozen_linear_reconciliation.csv`, `C011_nonlinear_geometry_by_condition.csv`, "
        "`C011_nonlinear_geometry_summary.csv` (when C011 run)",
        "- `06_run_manifest.json`", "",
    ]
    (dest / "06_review_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description="06_mof_revision_checks.py | Project 7B2 revision: C011 nonlinear geometry + C012 process reversals")
    p.add_argument("--mode", choices=["all", "process", "geometry"], default="all")
    p.add_argument("--bootstrap", type=int, default=1000,
                   help="New sensitivity bootstrap draws; original frozen 10,000-draw results remain authoritative")
    p.add_argument("--seed", type=int, default=61108)
    p.add_argument("--project-root", type=Path, default=None,
                   help="Override auto-detected parent of 'Step 6 revision'")
    args = p.parse_args()
    if args.bootstrap < 200:
        p.error("--bootstrap must be >= 200 for a minimally interpretable sensitivity interval")
    here = Path(__file__).resolve().parent
    root = args.project_root.resolve() if args.project_root else here.parent
    if not (root / "analysis").is_dir():
        raise FileNotFoundError(f"Expected 7B2 root containing 'analysis': {root}\n"
                                "Put this .py in '<7B2>/Step 6 revision/' or pass --project-root")
    dest = here / "results"
    dest.mkdir(parents=True, exist_ok=True)
    print(f"Step 6 root: {root}\nOutput directory: {dest}", flush=True)
    process = geometry = None
    if args.mode in ("all", "process"):
        process = run_process(root, dest, args.bootstrap, args.seed)
        print("[C012] PASS: exact counts and frozen concordance reconciled.", flush=True)
    if args.mode in ("all", "geometry"):
        geometry = run_geometry(root, dest, args.bootstrap, args.seed + 10007)
        print("[C011] PASS: historical linear estimates reproduced; nonlinear models evaluated.", flush=True)
    make_report(root, dest, process, geometry, args.bootstrap)
    ins = {}
    for obj in (process, geometry):
        if obj:
            for key in ("input", "reference"):
                path = Path(obj[key]); ins[str(path.relative_to(root))] = {"bytes": path.stat().st_size,
                                                                   "sha256": sha256(path)}
    manifest = {
        "project": "7B2", "task": "Ashleigh review C011/C012", "utc_run_time": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode, "bootstrap_replicates_new": args.bootstrap, "rng_seed": args.seed,
        "input_files": ins,
        "frozen_process_reproduced": None if not process else process["reconciled_to_frozen_summary"],
        "frozen_geometry_reproduced": None if not geometry else geometry["frozen_linear_reproduced"],
        "nonlinear_model_features": {"quadratic": "7 original g plus 7 g^2 terms",
                                     "piecewise_linear_spline": "7 original g plus 7 max(0,g-1/3) and 7 max(0,g-2/3) terms"},
        "support_cell_weighting": "same equal-weight cell Frisch-Waugh-Lovell estimator as original",
        "bootstrap_unit": "whole support cell after family-median aggregation",
        "pair_reselection": False, "causal_inference_claim": False,
        "original_inputs_edited": False,
        "outputs": sorted(p.name for p in dest.iterdir() if p.is_file()),
        "python": sys.version, "numpy": np.__version__, "pandas": pd.__version__,
    }
    (dest / "06_run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"COMPLETE. Read: {dest / '06_review_report.md'}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print(f"STEP 6 FAILED — {type(ex).__name__}: {ex}", file=sys.stderr, flush=True)
        raise
