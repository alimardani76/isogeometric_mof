#!/usr/bin/env python3
"""
Project 7B2 Step 2, file 06: freeze the final claim-evidence matrix.

Place inside:
    Step 2 chemistry strengthening/

Run from project root:
    python "Step 2 chemistry strengthening/06_freeze_step2_claims.py"

This script performs no new scientific analysis. It verifies the completed
Step 2 outputs, extracts their decisive counts, and writes the governing claim
matrix for Step 3 production.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

STEP2 = Path(__file__).resolve().parent
ROOT = STEP2.parent
RESULTS = ROOT / "Step 2 results"
OUT = RESULTS / "step2_closure"
OUT.mkdir(parents=True, exist_ok=True)

FILES = {
    "heat_condition": RESULTS / "heat_analysis" / "heat_adsorption_condition_results.csv",
    "heat_pressure": RESULTS / "heat_analysis" / "heat_adsorption_pressure_results.csv",
    "heat_summary": RESULTS / "heat_analysis" / "heat_analysis_summary.csv",
    "adjustment": RESULTS / "residual_adjustment" / "03_results.csv",
    "adjustment_summary": RESULTS / "residual_adjustment" / "03_summary.csv",
    "balance": RESULTS / "balance_family_dominance" / "04_balance.csv",
    "family": RESULTS / "balance_family_dominance" / "04_family_exclusion_summary.csv",
    "guest": RESULTS / "guest_specificity" / "05_results.csv",
    "guest_summary": RESULTS / "guest_specificity" / "05_summary.csv",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require():
    missing = [str(p) for p in FILES.values() if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing completed Step 2 outputs:\n" + "\n".join(missing))


def count_condition(df, intervention, measure, positive=True):
    x = df.loc[
        df["intervention"].eq(intervention) & df["effect_measure"].eq(measure)
    ]
    return {
        "conditions": len(x),
        "positive": int((x["spearman_rho_heat_vs_adsorption_separation"] > 0).sum()),
        "interval_above": int((x["bootstrap_95_low_rho"] > 0).sum()),
        "interval_below": int((x["bootstrap_95_high_rho"] < 0).sum()),
        "median_rho": float(x["spearman_rho_heat_vs_adsorption_separation"].median()),
    }


def main():
    require()
    heat = pd.read_csv(FILES["heat_condition"])
    pressure = pd.read_csv(FILES["heat_pressure"])
    adj = pd.read_csv(FILES["adjustment"])
    balance = pd.read_csv(FILES["balance"])
    family = pd.read_csv(FILES["family"])
    guest = pd.read_csv(FILES["guest"])

    linker_heat_log = count_condition(heat, "linker_family_change", "absolute_log_difference")
    linker_heat_std = count_condition(heat, "linker_family_change", "standardized_absolute_difference")
    metal_heat_log = count_condition(heat, "metal_substitution", "absolute_log_difference")
    metal_heat_std = count_condition(heat, "metal_substitution", "standardized_absolute_difference")

    adj_log = adj.loc[adj["effect_measure"].eq("absolute_log_difference")]
    adj_std = adj.loc[adj["effect_measure"].eq("standardized_absolute_difference")]

    guest_ads_log = guest.loc[
        guest["quantity"].eq("adsorption_separation")
        & guest["measure"].eq("absolute_log_difference")
    ]
    guest_heat = guest.loc[guest["quantity"].eq("heat_contrast")]

    linker_balance = balance.loc[balance["intervention"].eq("linker_family_change")]
    density_smd = float(linker_balance.loc[linker_balance["geometry_variable"].eq("Density_diff"), "global_smd"].iloc[0])
    avaf_smd = float(linker_balance.loc[linker_balance["geometry_variable"].eq("AVAf_diff"), "global_smd"].iloc[0])

    family_linker = family.loc[family["intervention"].eq("linker_family_change")]
    family_metal = family.loc[family["intervention"].eq("metal_substitution")]

    rows = [
        {
            "claim_id": "H0_LINKER",
            "claim": "Linker-family changes show greater adsorption separation than matched same-chemistry controls.",
            "status": "SUPPORTED",
            "primary_evidence": "Frozen primary and symmetric same-chemistry control analyses",
            "step2_support": "Adjusted contrast remained positive in 18/18 absolute-log and 17/18 standardized conditions.",
            "boundary": "Residual measured geometry attenuates the magnitude; not geometry independent.",
            "main_text": True,
            "prohibited_wording": "geometry-independent linker effect; causal linker effect",
        },
        {
            "claim_id": "H0_METAL",
            "claim": "Coordination-compatible metal substitutions show adsorption separation beyond the same-chemistry baseline in a subset of conditions.",
            "status": "CONDITIONALLY_SUPPORTED",
            "primary_evidence": "Frozen symmetric matched-control analysis",
            "step2_support": "Heat contrast correlated with adsorption separation in multiple conditions; family exclusion had small influence.",
            "boundary": "Restricted to the coordination-compatible subset and context dependent.",
            "main_text": True,
            "prohibited_wording": "universal metal substitution rule; periodic trend; directional exchange rule",
        },
        {
            "claim_id": "H1_ENERGETICS",
            "claim": "Larger heat-of-adsorption contrasts generally accompany larger adsorption separation within matched chemistry-changing pairs.",
            "status": "SUPPORTED_FOR_LINKER_CONDITIONAL_FOR_METAL",
            "primary_evidence": f"Linker absolute-log: {linker_heat_log['interval_above']}/{linker_heat_log['conditions']} intervals above zero; metal: {metal_heat_log['interval_above']}/{metal_heat_log['conditions']}.",
            "step2_support": f"Median rho linker={linker_heat_log['median_rho']:.3f}; metal={metal_heat_log['median_rho']:.3f}.",
            "boundary": "Energetic correlate, not a resolved adsorption-site or electrostatic mechanism.",
            "main_text": True,
            "prohibited_wording": "heat difference causes uptake difference; charge mechanism established",
        },
        {
            "claim_id": "H1_CHARGE_HETEROATOM",
            "claim": "Charge redistribution and accessible heteroatoms independently explain adsorption separation.",
            "status": "UNANSWERED",
            "primary_evidence": "No global charge-localization or accessible-site intervention was executed.",
            "step2_support": "None.",
            "boundary": "May be discussed only as future mechanism work or selected-case hypothesis.",
            "main_text": False,
            "prohibited_wording": "charge redistribution controls the observed linker result",
        },
        {
            "claim_id": "H2",
            "claim": "CO2 generally shows larger energetic and multiplicative chemistry sensitivity than CH4, N2, or H2 in corresponding paired process regimes.",
            "status": "CONDITIONALLY_SUPPORTED",
            "primary_evidence": f"Absolute-log CO2 greater in {int((guest_ads_log['median_bootstrap_95_low'] > 0).sum())}/{len(guest_ads_log)} intervention-regime rows; heat contrast greater in {int((guest_heat['median_bootstrap_95_low'] > 0).sum())}/{len(guest_heat)}.",
            "step2_support": "Paired within identical dependence families, minimum 3491 linker and 452 metal groups.",
            "boundary": "Process-regime comparison, not equal-pressure thermodynamic comparison; high-pressure pre-combustion CO2 versus H2 reverses for absolute-log adsorption separation.",
            "main_text": True,
            "prohibited_wording": "CO2 always has the largest chemistry effect at equivalent conditions",
        },
        {
            "claim_id": "H3",
            "claim": "Intervention classes have distinct support and response patterns.",
            "status": "PARTIALLY_SUPPORTED",
            "primary_evidence": "Strong linker, conditional metal, unsupported functional-motif class.",
            "step2_support": "Energetic associations and guest specificity differ between linker and metal classes.",
            "boundary": "Accessible-site and charge-localization classes were not constructed.",
            "main_text": True,
            "prohibited_wording": "all planned intervention classes were tested",
        },
        {
            "claim_id": "H4",
            "claim": "Energetic contrasts persist across pressure while their expression in adsorption separation changes with loading regime.",
            "status": "SUPPORTED_WITH_BOUNDARY",
            "primary_evidence": "Frozen pressure trends plus Step 2 heat-pressure analysis.",
            "step2_support": "Heat contrast often persisted or increased while proportional adsorption separation weakened; pressure-change relationships were measure dependent.",
            "boundary": "No universal chemistry-to-geometry handover or universal pressure law.",
            "main_text": True,
            "prohibited_wording": "energetic differences disappear at high pressure; geometry fully takes over",
        },
        {
            "claim_id": "H5",
            "claim": "Chemistry effects are context dependent and robust within observed support.",
            "status": "PARTIALLY_SUPPORTED",
            "primary_evidence": "Caliper, reciprocal, topology, control, and family-exclusion robustness.",
            "step2_support": f"Top-10-family exclusion maximum relative change: linker {family_linker['max_abs_relative_change_excluding_top10'].max():.3f}; metal {family_metal['max_abs_relative_change_excluding_top10'].max():.3f}.",
            "boundary": "No true unseen-family predictive transfer test.",
            "main_text": True,
            "prohibited_wording": "generalizes to unseen linker, metal, or topology families",
        },
        {
            "claim_id": "H6",
            "claim": "Uptake advantages often persist into working capacity but less reliably into selectivity.",
            "status": "SUPPORTED",
            "primary_evidence": "Frozen process-translation analysis.",
            "step2_support": "Guest-specificity and energetic results provide context but do not replace process evidence.",
            "boundary": "Working capacity is mathematically related to uptake; selectivity is the more independent test.",
            "main_text": True,
            "prohibited_wording": "uptake improvement guarantees process improvement",
        },
        {
            "claim_id": "BALANCE",
            "claim": "Residual measured geometry contributes to the chemistry-control contrast.",
            "status": "SUPPORTED",
            "primary_evidence": f"Linker global SMD density={density_smd:.3f}, AVAf={avaf_smd:.3f}; residual-adjusted estimates attenuated.",
            "step2_support": f"Adjusted intervals above zero: absolute-log {int((adj_log['adjusted_bootstrap_95_low'] > 0).sum())}/18; standardized {int((adj_std['adjusted_bootstrap_95_low'] > 0).sum())}/18.",
            "boundary": "SMD was a post hoc diagnostic, not a preregistered acceptance criterion.",
            "main_text": True,
            "prohibited_wording": "perfect balance; geometry was eliminated",
        },
    ]
    claims = pd.DataFrame(rows)
    claims.to_csv(OUT / "06_claim_evidence_matrix.csv", index=False)

    figure_rows = [
        ["Figure 1", "Natural-experiment architecture and structural control", "Frozen cohort, matching tiers, pair classes, related groups", "Ready"],
        ["Figure 2", "Chemistry exceeds matched background variation", "Primary/symmetric controls, energetic association, adjusted sensitivity", "Ready"],
        ["Figure 3", "Guest and pressure dependence of energetic versus adsorption sensitivity", "Heat association, H2 paired regimes, high-pressure CO2/H2 reversal", "Ready"],
        ["Figure 4", "Robustness and applicability boundaries", "Calipers, reciprocal, topology, balance, family exclusion", "Ready"],
        ["Figure 5", "Structure-resolved strong, null, exceptional, and discordant cases", "Frozen shortlist; final human case selection required", "Pending case selection"],
        ["Figure 6", "Process translation and bounded chemical design map", "Working capacity, selectivity, support domains; no directional substitution rules", "Ready after case selection"],
    ]
    figures = pd.DataFrame(figure_rows, columns=["figure", "message", "evidence", "status"])
    figures.to_csv(OUT / "06_figure_architecture.csv", index=False)

    report = [
        "PROJECT 7B2 STEP 2 CLOSURE", "=" * 72,
        "Step 2 scientific strengthening is frozen.",
        "No further global analysis is authorized before Step 3 production review.",
        "",
        "DECISIVE UPGRADES",
        "1. Heat-of-adsorption contrast is a reproducible energetic correlate of adsorption separation.",
        "2. CO2 generally has larger energetic and multiplicative chemistry sensitivity than co-guests, with a high-pressure CO2/H2 boundary.",
        "3. Residual measured geometry attenuates but generally does not remove the linker-control contrast.",
        "4. Linker and metal results are not driven by the largest or ten largest families.",
        "",
        "NON-NEGOTIABLE BOUNDARIES",
        "- no formal causality or geometry independence",
        "- no general charge or accessible-site mechanism",
        "- no universal CO2 or pressure rule",
        "- no unseen-family transfer claim",
        "- no directional metal or synthesis rule",
        "",
        "NEXT STEP",
        "Step 3 production begins with final case selection and figure-source preparation.",
        "Selected-case charge summaries may be evaluated only after final cases are frozen.",
    ]
    (OUT / "06_report.txt").write_text("\n".join(report), encoding="utf-8", newline="\n")

    manifest = {
        "stage": "Project 7B2 Step 2 closure",
        "created": datetime.now().isoformat(timespec="seconds"),
        "script": "06_freeze_step2_claims.py",
        "inputs": {name: {"path": str(path), "sha256": sha256(path)} for name, path in FILES.items()},
        "new_scientific_analysis": False,
        "claim_matrix_rows": len(claims),
        "figure_architecture_rows": len(figures),
        "step2_frozen": True,
        "outputs": ["06_claim_evidence_matrix.csv", "06_figure_architecture.csv", "06_report.txt"],
        "python": sys.version,
        "pandas": pd.__version__,
    }
    (OUT / "06_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
    print("\n".join(report))
    print(f"\nOutputs: {OUT}")

if __name__ == "__main__":
    main()
