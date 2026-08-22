#!/usr/bin/env python3
"""
Project 7B Step 4 - Phase 2E
Selected-case chemistry closure and manuscript-evidence map.

Purpose
-------
Close Phase 2 conservatively after:
- exact recovery of the original CrystalNN definitions,
- selected-case CrystalNN + ChemEnv analysis,
- exact raw-CIF -> pymatgen REPEAT-charge mapping,
- case-level chemistry synthesis,
- confirmation that Project 7B has linker-family metadata but NO linker-atom mapping.

This script performs NO new scientific calculation. It only converts the audited
Phase 2 outputs into a manuscript-use decision map.

READ ONLY with respect to Steps 1-3 and prior Step 4 scientific outputs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

TITLE = "PROJECT 7B STEP 4 - PHASE 2E CHEMISTRY CLOSURE"


def find_root(start: Path) -> Path:
    p = start.resolve()
    for cand in [p] + list(p.parents):
        if (cand / "Step 3 results").exists() and (cand / "Step 4 extension").exists():
            return cand
    raise RuntimeError("Could not locate Project 7B root.")


def fmt(x, n=4):
    try:
        if pd.isna(x):
            return "NA"
        return f"{float(x):.{n}g}"
    except Exception:
        return str(x)


def role_key(s: str) -> str:
    return str(s).strip().lower()


def main():
    print(TITLE)
    print("=" * 72)

    root = find_root(Path.cwd())

    p2c = root / "Step 4 results" / "02_cif_chemistry" / "phase2c_case_chemistry_synthesis"
    p2d1 = root / "Step 4 results" / "02_cif_chemistry" / "phase2d1_linker_definition_recovery"
    p2b2 = root / "Step 4 results" / "02_cif_chemistry" / "phase2b2_exact_charge_site_bridge"
    out = root / "Step 4 results" / "02_cif_chemistry" / "phase2e_chemistry_closure"
    out.mkdir(parents=True, exist_ok=True)

    required = {
        "pair_cards": p2c / "phase2c_pair_case_chemistry_cards.csv",
        "integration_map": p2c / "phase2c_figure5_integration_decision_map.csv",
        "linker_summary": p2d1 / "phase2d1_summary.json",
        "charge_summary": p2b2 / "phase2b2_summary.json",
    }

    missing = [f"{k}: {p}" for k, p in required.items() if not p.exists()]
    if missing:
        print("Decision: FAIL")
        for x in missing:
            print(f"FATAL: missing {x}")
        sys.exit(2)

    cards = pd.read_csv(required["pair_cards"], low_memory=False)
    integ = pd.read_csv(required["integration_map"], low_memory=False)
    linker_summary = json.loads(required["linker_summary"].read_text(encoding="utf-8"))
    charge_summary = json.loads(required["charge_summary"].read_text(encoding="utf-8"))

    if linker_summary.get("decision") != "LINKER_FAMILY_OR_PAIR_RULE_EXISTS_BUT_NO_ATOM_MAPPING":
        print("Decision: FAIL")
        print("FATAL: Phase 2D1 did not establish the expected linker-boundary state.")
        sys.exit(2)

    if charge_summary.get("decision") != "PASS":
        print("Decision: FAIL")
        print("FATAL: Phase 2B2 charge-site bridge did not pass.")
        sys.exit(2)

    rows = []

    for _, r in cards.iterrows():
        role = role_key(r.get("case_role", ""))
        status = str(r.get("phase2c_status", ""))

        evidence = []
        allowed = []
        forbidden = []
        placement = "SI_DETAIL_ONLY"
        decision = "KEEP_AS_STRUCTURAL_CONTEXT"

        if int(r.get("method_sensitive_sites_total", 0)) > 0:
            evidence.append("CrystalNN coordination is method-sensitive in this pair")
        else:
            evidence.append("CrystalNN coordination is robust across the two recovered settings")

        if bool(r.get("crystalnn_shell_inventory_same", False)):
            evidence.append("default CrystalNN shell inventory is the same across the pair")
        else:
            evidence.append("default CrystalNN shell inventory differs across the pair")

        if bool(r.get("chemenv_inventory_same", False)):
            evidence.append("ChemEnv environment inventory is the same across the pair")
        else:
            evidence.append("ChemEnv environment inventory differs across the pair")

        evidence.append(
            "validated whole-structure REPEAT charge-distribution distance = "
            + fmt(r.get("all_atom_charge_wasserstein"))
        )
        evidence.append(
            "validated heteroatom REPEAT charge-distribution distance = "
            + fmt(r.get("heteroatom_charge_wasserstein"))
        )

        if "strong_linker" in role:
            decision = "PASS_MAIN_CONTEXT"
            placement = "FIGURE_5_COMPACT_ANNOTATION"
            allowed = [
                "Describe the selected pair as a strong linker-family example with robust metal-node context if the coordination checks are preserved.",
                "Report the whole-structure / heteroatom REPEAT-charge separation as a selected-case electrostatic fingerprint.",
                "Contrast qualitatively with the frozen near-null case as case-level context only.",
            ]
            forbidden = [
                "Do not call the REPEAT-charge difference linker-local.",
                "Do not identify a changed linker atom or adsorption site.",
                "Do not infer a causal electrostatic mechanism from the six selected cases.",
            ]

        elif "strong_metal" in role:
            decision = "PASS_MAIN_CONTEXT"
            placement = "FIGURE_5_COMPACT_ANNOTATION"
            allowed = [
                "Use robust local metal coordination, ChemEnv geometry, first-shell composition/distances, and validated REPEAT-charge fingerprints as case-level structural chemistry.",
                "State explicitly that the local coordination description is robust to the two original CrystalNN settings.",
            ]
            forbidden = [
                "Do not assign oxidation states from REPEAT charges.",
                "Do not claim charge transfer.",
                "Do not derive a universal or directional metal-substitution rule.",
                "Do not identify guest binding sites without host-guest evidence.",
            ]

        elif "cu_zn_pressure_exception" in role:
            decision = "PASS_MAIN_BOUNDARY"
            placement = "FIGURE_5_BOUNDARY_LABEL"
            allowed = [
                "Use this case as a coordination-method-sensitive boundary example.",
                "Retain the pressure-exception interpretation from the frozen adsorption evidence.",
            ]
            forbidden = [
                "Do not present its local coordination as method-robust.",
                "Do not use it to support a clean Cu-versus-Zn local mechanism.",
            ]

        elif "near_null" in role:
            decision = "PASS_MAIN_COMPARATOR"
            placement = "FIGURE_5_COMPARATOR"
            allowed = [
                "Use as the frozen near-null comparison.",
                "Its much smaller selected-case electrostatic fingerprint may be shown descriptively next to the strong-linker case.",
            ]
            forbidden = [
                "Do not convert the two-case contrast into a population-wide charge-effect relationship.",
                "Do not call the charge distance a mechanistic explanatory variable.",
            ]

        elif "process_discordant" in role:
            decision = "PASS_CONTEXT_BOUNDARY"
            placement = "FIGURE_5_OR_SI_EXISTING_ROLE"
            allowed = [
                "Retain as a process-discordance case with descriptive structural chemistry only.",
            ]
            forbidden = [
                "Do not use the selected-case chemistry fingerprint to explain process discordance causally.",
            ]

        elif "functional" in role:
            decision = "EXPLORATORY_ONLY"
            placement = "FIGURE_5_LIGHT_OR_SI"
            allowed = [
                "Retain only as an exploratory structural example because the functional-motif class is underpowered in the frozen catalogue.",
            ]
            forbidden = [
                "No class-level functional-motif mechanism or generalization.",
            ]

        else:
            allowed = ["Use only as descriptive selected-case structural context."]
            forbidden = ["No mechanism or generalization beyond the selected case."]

        rows.append({
            "pair_id": r.get("pair_id", ""),
            "case_role": r.get("case_role", ""),
            "phase2c_status": status,
            "phase2e_decision": decision,
            "recommended_placement": placement,
            "evidence_summary": " | ".join(evidence),
            "allowed_use": " | ".join(allowed),
            "forbidden_use": " | ".join(forbidden),
            "all_atom_charge_wasserstein": r.get("all_atom_charge_wasserstein", np.nan),
            "heteroatom_charge_wasserstein": r.get("heteroatom_charge_wasserstein", np.nan),
            "method_sensitive_sites_total": r.get("method_sensitive_sites_total", np.nan),
            "crystalnn_shell_inventory_same": r.get("crystalnn_shell_inventory_same", False),
            "chemenv_inventory_same": r.get("chemenv_inventory_same", False),
        })

    decision_map = pd.DataFrame(rows)
    decision_map.to_csv(out / "phase2e_case_manuscript_decision_map.csv", index=False)

    # Global Phase 2 boundaries.
    global_map = pd.DataFrame([
        {
            "object": "two-setting CrystalNN coordination",
            "status": "PASS_SELECTED_CASES",
            "main_use": "selected-case local coordination context",
            "boundary": "8/88 metal sites were method-sensitive; one frozen pair contains all method-sensitive sites",
        },
        {
            "object": "ChemEnv cross-check",
            "status": "PASS_SELECTED_CASES",
            "main_use": "independent coordination-geometry context",
            "boundary": "algorithmic structural classification, not adsorption mechanism",
        },
        {
            "object": "site-level REPEAT charge attachment",
            "status": "PASS_SELECTED_CASES",
            "main_use": "validated selected-case partial-charge fingerprints",
            "boundary": "not oxidation states, charge transfer, or binding-site evidence",
        },
        {
            "object": "linker family",
            "status": "PASS_PAIR_CLASSIFICATION_ONLY",
            "main_use": "existing linker-family intervention definition",
            "boundary": "no molecular linker identity or atom mapping exists in Project 7B",
        },
        {
            "object": "linker-local electrostatics",
            "status": "NOT_ESTABLISHED",
            "main_use": "none",
            "boundary": "would require a genuinely new linker atom-localization method",
        },
        {
            "object": "whole-structure charge Wasserstein distance",
            "status": "DESCRIPTIVE_SELECTED_CASE_ONLY",
            "main_use": "compact electrostatic fingerprint for the frozen examples",
            "boundary": "not a fitted predictor, causal mediator, or population-wide rule",
        },
    ])
    global_map.to_csv(out / "phase2e_global_evidence_boundary_map.csv", index=False)

    report = []
    report.append("PROJECT 7B STEP 4 - PHASE 2 CHEMISTRY CLOSURE")
    report.append("=" * 72)
    report.append("")
    report.append("Decision: PASS_AND_CLOSE_PHASE_2")
    report.append("")
    report.append("What Phase 2 established")
    report.append("------------------------")
    report.append(
        "1. The original two-setting CrystalNN definition was recovered exactly and "
        "reapplied to all 12 frozen selected structures."
    )
    report.append(
        "2. 80 of 88 selected metal sites had exactly identical CrystalNN neighbor "
        "shells under both recovered settings; 8 sites were method-sensitive."
    )
    report.append(
        "3. ChemEnv provided an independent selected-case coordination-geometry cross-check."
    )
    report.append(
        "4. All 2,836 frozen REPEAT-charge rows were mapped one-to-one onto pymatgen "
        "sites with zero coordinate discrepancy and no ambiguous assignments."
    )
    report.append(
        "5. The strong-linker case has substantially larger selected-case whole-structure "
        "and heteroatom charge-distribution separation than the frozen near-null linker case."
    )
    report.append(
        "6. Project 7B contains linker-family/pair-rule metadata but no molecular linker "
        "identity or linker-atom mapping."
    )
    report.append("")
    report.append("What Phase 2 did NOT establish")
    report.append("------------------------------")
    report.append("- No linker-local charge mechanism.")
    report.append("- No adsorption-site map.")
    report.append("- No oxidation-state or charge-transfer inference.")
    report.append("- No directional linker or metal substitution rule.")
    report.append("- No population-wide relationship between charge distance and adsorption effect.")
    report.append("- No atom-specific pore accessibility.")
    report.append("")
    report.append("Recommendation")
    report.append("--------------")
    report.append(
        "Stop the linker-localization branch here. Building a new graph-based linker atom "
        "mapping only for six post-selected cases would add method complexity without yet "
        "providing population-level evidence. Use the validated chemistry as compact Figure 5 "
        "context and preserve the strong claim boundary."
    )
    report.append(
        "The next scientifically distinct Step 4 question should be Phase 3: whether a "
        "dependency-aware falsification/randomization test can be defined without violating "
        "the matched-pair dependence structure."
    )

    (out / "phase2e_closure_report.md").write_text("\n".join(report), encoding="utf-8")

    summary = {
        "decision": "PASS_AND_CLOSE_PHASE_2",
        "case_decisions": int(len(decision_map)),
        "linker_atom_mapping": False,
        "site_level_repeat_charge_validated": True,
        "new_linker_localization_recommended": False,
        "next_phase": "PHASE_3_FALSIFICATION_DESIGN_AUDIT",
    }
    (out / "phase2e_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Decision: PASS_AND_CLOSE_PHASE_2")
    print(f"Case manuscript decisions: {len(decision_map)}")
    print("Site-level REPEAT charge attachment: VALIDATED_SELECTED_CASES")
    print("Existing linker-family definition: VALID_FOR_PAIR_CLASSIFICATION")
    print("Existing linker-atom mapping: NONE")
    print("New linker atom-localization method: NOT RECOMMENDED AT THIS STAGE")

    print("\nCase decisions:")
    for _, r in decision_map.iterrows():
        print(
            f"  {r['case_role']} -> {r['phase2e_decision']} "
            f"({r['recommended_placement']})"
        )

    print("\nNext: PHASE_3_FALSIFICATION_DESIGN_AUDIT")
    print("No new scientific effect was computed.")
    print(f"Outputs: {out}")


if __name__ == "__main__":
    main()
