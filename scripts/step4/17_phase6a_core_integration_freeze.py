#!/usr/bin/env python3
"""
Project 7B Step 4 - Phase 6A
Core integration freeze and manuscript handoff map.

Purpose
-------
Convert the completed Step 4 CORE audits into one final integration package before
editing the manuscript or figures.

This phase does NOT:
- recompute any scientific result,
- alter Steps 1-3,
- edit main.tex,
- render or compile figures/PDFs.

It freezes:
1. what Step 4 adds to the core paper,
2. what remains extended-only,
3. what was explicitly rejected,
4. what Figure 5 may say,
5. exact claim boundaries for manuscript integration,
6. a reproducibility inventory for the Step 4 core outputs.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

TITLE = "PROJECT 7B STEP 4 - PHASE 6A CORE INTEGRATION FREEZE"


def find_root(start: Path) -> Path:
    p = start.resolve()
    for cand in [p] + list(p.parents):
        if (cand / "Step 3 results").exists() and (cand / "Step 4 extension").exists():
            return cand
    raise RuntimeError("Could not locate Project 7B root.")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require_json(path: Path, expected_decision: str):
    if not path.exists():
        raise RuntimeError(f"Missing required file: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if obj.get("decision") != expected_decision:
        raise RuntimeError(
            f"{path.name}: decision={obj.get('decision')!r}, "
            f"expected {expected_decision!r}"
        )
    return obj


def main():
    print(TITLE)
    print("=" * 72)

    root = find_root(Path.cwd())

    p2e = root / "Step 4 results" / "02_cif_chemistry" / "phase2e_chemistry_closure"
    p3b = root / "Step 4 results" / "03_falsification" / "phase3b_falsification_closure"
    p4c = root / "Step 4 results" / "04_host_guest_maps" / "phase4c_core_closure"
    p2c = root / "Step 4 results" / "02_cif_chemistry" / "phase2c_case_chemistry_synthesis"

    out = root / "Step 4 results" / "06_integration" / "phase6a_core_integration_freeze"
    out.mkdir(parents=True, exist_ok=True)

    s2 = require_json(p2e / "phase2e_summary.json", "PASS_AND_CLOSE_PHASE_2")
    s3 = require_json(p3b / "phase3b_summary.json", "PASS_AND_CLOSE_PHASE_3")
    s4 = require_json(p4c / "phase4c_summary.json", "PASS_AND_CLOSE_CORE_PHASE_4")

    case_map_path = p2e / "phase2e_case_manuscript_decision_map.csv"
    global_map_path = p2e / "phase2e_global_evidence_boundary_map.csv"
    null_map_path = p3b / "phase3b_null_reference_evidence_map.csv"
    branch_map_path = p4c / "phase4c_branch_closure_map.csv"
    p2c_cards_path = p2c / "phase2c_pair_case_chemistry_cards.csv"

    for p in [case_map_path, global_map_path, null_map_path, branch_map_path, p2c_cards_path]:
        if not p.exists():
            raise RuntimeError(f"Missing required integration object: {p}")

    case_map = pd.read_csv(case_map_path, low_memory=False)
    global_map = pd.read_csv(global_map_path, low_memory=False)
    null_map = pd.read_csv(null_map_path, low_memory=False)
    branch_map = pd.read_csv(branch_map_path, low_memory=False)
    case_cards = pd.read_csv(p2c_cards_path, low_memory=False)

    # ------------------------------------------------------------------
    # 1. Final analysis register
    # ------------------------------------------------------------------
    register = pd.DataFrame([
        {
            "analysis_object": "Frozen-input provenance audit",
            "final_class": "CORE_COMPLETE",
            "paper_role": "Reproducibility / governance",
            "decision": "KEEP",
            "boundary": "No new science; confirms canonical frozen evidence.",
        },
        {
            "analysis_object": "Existing-evidence exhaustion audit",
            "final_class": "CORE_COMPLETE",
            "paper_role": "Scope control",
            "decision": "KEEP_INTERNAL",
            "boundary": "Used to prevent unsupported/bloated upgrades.",
        },
        {
            "analysis_object": "Selected-case two-setting CrystalNN coordination",
            "final_class": "CORE_NEW_EVIDENCE",
            "paper_role": "Figure 5 structural chemistry",
            "decision": "KEEP",
            "boundary": "Selected cases only; algorithmic coordination context, not mechanism.",
        },
        {
            "analysis_object": "Selected-case ChemEnv cross-check",
            "final_class": "CORE_NEW_EVIDENCE",
            "paper_role": "Figure 5 / SI structural cross-check",
            "decision": "KEEP",
            "boundary": "Coordination geometry only; not adsorption-site evidence.",
        },
        {
            "analysis_object": "Exact REPEAT raw-CIF -> pymatgen site bridge",
            "final_class": "CORE_NEW_EVIDENCE",
            "paper_role": "Selected-case electrostatic structural context",
            "decision": "KEEP",
            "boundary": "Validated site-level partial charges; not oxidation state or charge transfer.",
        },
        {
            "analysis_object": "Whole-structure / heteroatom charge-distribution distances",
            "final_class": "CORE_NEW_EVIDENCE",
            "paper_role": "Compact selected-case Figure 5 annotation / SI",
            "decision": "KEEP_DESCRIPTIVE",
            "boundary": "Six frozen cases only; not a fitted predictor, causal mediator, or universal rule.",
        },
        {
            "analysis_object": "Linker-local charge mapping",
            "final_class": "NOT_ESTABLISHED",
            "paper_role": "None",
            "decision": "REJECT_FOR_CORE",
            "boundary": "Original project contains linker-family metadata but no linker atom mapping.",
        },
        {
            "analysis_object": "Shuffled-label / naive permutation null",
            "final_class": "REJECTED_METHOD",
            "paper_role": "None",
            "decision": "REJECT",
            "boundary": "Invalid under observed shared-framework and repeated-condition dependence.",
        },
        {
            "analysis_object": "Primary same-chemistry controls",
            "final_class": "CORE_EXISTING_EVIDENCE",
            "paper_role": "Empirical null reference",
            "decision": "KEEP",
            "boundary": "Observational matched background, not randomized assignment.",
        },
        {
            "analysis_object": "Symmetric same-chemistry controls",
            "final_class": "CORE_EXISTING_EVIDENCE",
            "paper_role": "Robustness null reference",
            "decision": "KEEP",
            "boundary": "Still observational/dependent; used as robustness reference.",
        },
        {
            "analysis_object": "Dependency-cluster bootstrap / structured residual permutation",
            "final_class": "EXTENDED_ONLY",
            "paper_role": "None in core",
            "decision": "DEFER",
            "boundary": "New inferential layer; revisit only if specifically demanded.",
        },
        {
            "analysis_object": "Selected-case GCMC reproduction",
            "final_class": "EXTENDED_ONLY",
            "paper_role": "None in core",
            "decision": "DEFER",
            "boundary": "Historical ARC-MOF protocol is incompletely pinned.",
        },
        {
            "analysis_object": "Density / site-occupancy maps",
            "final_class": "EXTENDED_ONLY",
            "paper_role": "None in core",
            "decision": "DEFER",
            "boundary": "Requires successful uptake-reproduction gate first.",
        },
        {
            "analysis_object": "DFT / higher-fidelity mechanism validation",
            "final_class": "EXTENDED_ONLY",
            "paper_role": "None in core",
            "decision": "DEFER",
            "boundary": "Requires a specific hypothesis from reproduced host-guest evidence.",
        },
        {
            "analysis_object": "SHAP / UMAP / t-SNE / decorative complexity",
            "final_class": "REJECTED_SCOPE",
            "paper_role": "None",
            "decision": "REJECT",
            "boundary": "No clear claim-level value for this matched-pair paper.",
        },
    ])
    register.to_csv(out / "phase6a_final_analysis_register.csv", index=False)

    # ------------------------------------------------------------------
    # 2. Manuscript claim map
    # ------------------------------------------------------------------
    claims = pd.DataFrame([
        {
            "claim_id": "S4-C1",
            "manuscript_location": "Results - selected structural cases / Figure 5",
            "status": "ADD",
            "claim_text": (
                "Across the frozen selected examples, the recovered two-setting CrystalNN "
                "analysis provides a reproducible local coordination description for most "
                "metal sites, while the Cu-Zn pressure-exception case remains explicitly "
                "method-sensitive."
            ),
            "support": "Phase 2B / 2C / 2E",
            "must_not_say": (
                "Do not generalize the selected-case coordination result to all primary pairs "
                "or call it an adsorption mechanism."
            ),
        },
        {
            "claim_id": "S4-C2",
            "manuscript_location": "Results - Figure 5 strong-metal example",
            "status": "ADD",
            "claim_text": (
                "The strong metal/process-aligned example supports a robust selected-case "
                "local-coordination and electrostatic structural description under the two "
                "recovered CrystalNN settings."
            ),
            "support": "Phase 2C / 2E",
            "must_not_say": (
                "No universal metal ranking, oxidation-state inference, charge transfer, "
                "or directional substitution mechanism."
            ),
        },
        {
            "claim_id": "S4-C3",
            "manuscript_location": "Results - Figure 5 strong-linker vs near-null context",
            "status": "ADD_CAREFULLY",
            "claim_text": (
                "The frozen strong-linker example shows a markedly larger descriptive "
                "whole-structure and heteroatom REPEAT-charge distribution separation than "
                "the frozen near-null linker comparison."
            ),
            "support": "Phase 2C / 2E",
            "must_not_say": (
                "Do not call the separation linker-local, causal, population-wide, "
                "or a fitted predictor of adsorption response."
            ),
        },
        {
            "claim_id": "S4-C4",
            "manuscript_location": "Methods / robustness or SI methods note",
            "status": "ADD",
            "claim_text": (
                "For the selected structures, frozen REPEAT atom rows were mapped onto "
                "pymatgen sites through exact raw-CIF row provenance and element-constrained "
                "periodic coordinate matching; all 2,836 rows mapped one-to-one with zero "
                "coordinate discrepancy and no ambiguous assignments."
            ),
            "support": "Phase 2B2",
            "must_not_say": (
                "This validates site-level attachment only; it does not establish linker "
                "assignment, adsorption sites, oxidation states, or charge-transfer mechanisms."
            ),
        },
        {
            "claim_id": "S4-C5",
            "manuscript_location": "Robustness / statistical limitations",
            "status": "ADD_OR_CLARIFY",
            "claim_text": (
                "No shuffled-label permutation test was added because the primary-pair "
                "network contains substantial shared-framework dependence and repeated "
                "condition-level observations; the pre-specified same-chemistry controls "
                "therefore remain the empirical null reference."
            ),
            "support": "Phase 3A / 3B",
            "must_not_say": (
                "Do not describe the control distribution as an exact randomized or "
                "permutation null."
            ),
        },
        {
            "claim_id": "S4-C6",
            "manuscript_location": "Discussion / limitations",
            "status": "ADD_OR_CLARIFY",
            "claim_text": (
                "The selected structural chemistry is consistent with chemically meaningful "
                "local and electrostatic context, but the frozen analysis does not establish "
                "a microscopic host-guest mechanism."
            ),
            "support": "Phase 2E + Phase 4C",
            "must_not_say": (
                "No binding-site, density-map, energy-decomposition, or DFT validation was "
                "performed for the core paper."
            ),
        },
    ])
    claims.to_csv(out / "phase6a_manuscript_claim_map.csv", index=False)

    # ------------------------------------------------------------------
    # 3. Figure 5 integration handoff
    # ------------------------------------------------------------------
    fig = case_map.merge(
        case_cards[
            [
                "pair_id",
                "all_atom_charge_wasserstein",
                "heteroatom_charge_wasserstein",
                "method_sensitive_sites_total",
                "crystalnn_shell_inventory_same",
                "chemenv_inventory_same",
            ]
        ],
        on="pair_id",
        how="left",
        suffixes=("", "_card"),
    )

    fig["core_annotation_rule"] = fig["phase2e_decision"].map({
        "PASS_MAIN_CONTEXT": "ADD_COMPACT_CHEMISTRY_ANNOTATION",
        "PASS_MAIN_BOUNDARY": "ADD_METHOD_SENSITIVE_BOUNDARY_LABEL",
        "PASS_MAIN_COMPARATOR": "ADD_COMPACT_COMPARATOR_ANNOTATION",
        "PASS_CONTEXT_BOUNDARY": "KEEP_LIGHT_CONTEXT",
        "EXPLORATORY_ONLY": "KEEP_EXPLORATORY_LIGHT_OR_MOVE_DETAIL_TO_SI",
    }).fillna("NO_NEW_ANNOTATION")

    fig.to_csv(out / "phase6a_figure5_core_integration_map.csv", index=False)

    # ------------------------------------------------------------------
    # 4. Main vs SI placement map
    # ------------------------------------------------------------------
    placement = pd.DataFrame([
        {
            "object": "Figure 5 case-role labels and compact chemistry annotations",
            "placement": "MAIN",
            "reason": "Directly strengthens the selected-case interpretation without changing the population-level estimand.",
        },
        {
            "object": "Full per-framework CrystalNN / ChemEnv summaries",
            "placement": "SI",
            "reason": "Necessary provenance and robustness detail, too granular for the main narrative.",
        },
        {
            "object": "Exact charge-site bridge audit statistics",
            "placement": "SI_METHODS_OR_TABLE",
            "reason": "Critical validation for the new charge attachment.",
        },
        {
            "object": "Whole-structure / heteroatom charge distribution distances for six cases",
            "placement": "MAIN_COMPACT + SI_FULL",
            "reason": "Useful selected-case context; full numerical detail belongs in SI.",
        },
        {
            "object": "Permutation/exchangeability audit details",
            "placement": "SI_OR_METHODS_NOTE",
            "reason": "Supports why no naive shuffled-label test was added.",
        },
        {
            "object": "Simulation provenance/reproduction feasibility audit",
            "placement": "NOT_IN_CORE_RESULTS",
            "reason": "Internal scope decision; mention only as a limitation/future-work boundary if useful.",
        },
        {
            "object": "GCMC / density maps / DFT",
            "placement": "NONE_CORE",
            "reason": "Deferred to optional extended work.",
        },
    ])
    placement.to_csv(out / "phase6a_main_vs_si_placement.csv", index=False)

    # ------------------------------------------------------------------
    # 5. Step 4 reproducibility manifest
    # ------------------------------------------------------------------
    manifest_rows = []
    result_root = root / "Step 4 results"
    for p in sorted(result_root.rglob("*")):
        if not p.is_file():
            continue
        # avoid hashing potentially huge future binary artifacts; current core should be small.
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size > 2 * 1024 * 1024 * 1024:
            digest = "SKIPPED_GT_2GB"
        else:
            digest = sha256(p)
        manifest_rows.append({
            "relative_path": str(p.relative_to(root)),
            "size_bytes": size,
            "sha256": digest,
        })

    manifest = pd.DataFrame(manifest_rows)
    manifest.to_csv(out / "phase6a_step4_reproducibility_manifest.csv", index=False)

    # ------------------------------------------------------------------
    # 6. Final integration report
    # ------------------------------------------------------------------
    report = [
        "PROJECT 7B STEP 4 - CORE INTEGRATION FREEZE",
        "=" * 72,
        "",
        "Decision: PASS_CORE_READY_FOR_MANUSCRIPT_INTEGRATION",
        "",
        "Core Step 4 additions",
        "---------------------",
        "1. Selected-case local coordination chemistry using the recovered two-setting CrystalNN definition.",
        "2. Independent ChemEnv selected-case coordination cross-check.",
        "3. Exact validated mapping of all 2,836 selected REPEAT-charge atom rows onto pymatgen sites.",
        "4. Descriptive selected-case electrostatic fingerprints, including the strong-linker / near-null contrast.",
        "5. Dependency-aware statistical audit establishing why naive shuffled-label permutation is not appropriate.",
        "6. Explicit closure of GCMC/density-map/DFT work as extended-only rather than core requirements.",
        "",
        "Core scientific boundary",
        "------------------------",
        "Project 7B remains an observational matched natural-experiment study. The new Step 4",
        "chemistry improves selected-case interpretation but does not convert the study into",
        "a microscopic causal mechanism paper.",
        "",
        "Next",
        "----",
        "Edit main.tex, Figure 5 source/annotations, and the SI using the frozen maps in this directory.",
        "Do not compile automatically.",
    ]
    (out / "phase6a_core_integration_report.md").write_text("\n".join(report), encoding="utf-8")

    summary = {
        "decision": "PASS_CORE_READY_FOR_MANUSCRIPT_INTEGRATION",
        "phase2": s2["decision"],
        "phase3": s3["decision"],
        "phase4_core": s4["decision"],
        "phase5_core": "SKIPPED_NOT_REQUIRED",
        "analysis_register_rows": len(register),
        "manuscript_claim_rows": len(claims),
        "figure5_case_rows": len(fig),
        "placement_rows": len(placement),
        "step4_manifest_files": len(manifest),
        "next": "EDIT_MAIN_TEX_FIGURE5_AND_SI_WITHOUT_COMPILING",
    }
    (out / "phase6a_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Decision: PASS_CORE_READY_FOR_MANUSCRIPT_INTEGRATION")
    print(f"Final analysis-register entries: {len(register)}")
    print(f"Manuscript claim-map entries: {len(claims)}")
    print(f"Figure 5 case-integration rows: {len(fig)}")
    print(f"Main/SI placement entries: {len(placement)}")
    print(f"Step 4 files hashed in reproducibility manifest: {len(manifest)}")
    print("Phase 5 core status: SKIPPED_NOT_REQUIRED")
    print("")
    print("Next: EDIT_MAIN_TEX_FIGURE5_AND_SI_WITHOUT_COMPILING")
    print("No scientific quantity was recomputed.")
    print(f"Outputs: {out}")


if __name__ == "__main__":
    main()
