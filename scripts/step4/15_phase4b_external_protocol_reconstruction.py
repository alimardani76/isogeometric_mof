#!/usr/bin/env python3
"""
Project 7B Step 4 - Phase 4B
External ARC-MOF protocol reconstruction and selected-state-point feasibility audit.

Important correction
--------------------
The original ARC-MOF adsorption screening was NOT reported as a RASPA workflow.
The ARC-MOF paper describes an in-house GCMC code based on DL_POLY. A public
uowoolab/FastMC repository exists and is a plausible code-family candidate, but
the ARC-MOF paper/dataset does not pin the historical commit used for the
published screening.

This phase does NOT run any simulation. It combines:
  (1) externally recovered protocol facts from the ARC-MOF primary paper,
  (2) public FastMC code provenance,
  (3) the frozen selected-case adsorption-condition table.

READ ONLY with respect to Steps 1-3 and prior Step 4 outputs.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

TITLE = "PROJECT 7B STEP 4 - PHASE 4B EXTERNAL ARC-MOF PROTOCOL RECONSTRUCTION"

FASTMC_COMMIT_CANDIDATE = "8ff3f8fdce72bbcb7bf693a568deb5a3535bae28"
FASTMC_COMMIT_DATE = "2022-12-18"

GUEST_TOKEN_PATTERNS = {
    "CO2": [r"\bCO2\b", r"CO_?2"],
    "N2": [r"\bN2\b", r"N_?2"],
    "CH4": [r"\bCH4\b", r"CH_?4"],
    "H2": [r"\bH2\b", r"H_?2"],
}

PROCESS_PATTERNS = {
    "methane_purification": [r"methane.?purif", r"natural.?gas"],
    "post_combustion_vsa": [r"post.?comb", r"\bvsa\b"],
    "pre_combustion_psa": [r"pre.?comb", r"\bpsa\b"],
    "methane_storage": [r"methane.?stor", r"storage"],
    "landfill_vpsa": [r"landfill", r"\bvpsa\b"],
}

EXTERNAL_PROTOCOL = [
    {
        "object": "simulation_engine_family",
        "status": "PRIMARY_SOURCE_RECOVERED",
        "value": "in-house GCMC code based on DL_POLY",
        "source": "Burner et al., ARC-MOF, Chem. Mater. 2023, 35, 900-916; DOI 10.1021/acs.chemmater.2c02485",
        "exact_reproduction_role": "required",
    },
    {
        "object": "public_code_candidate",
        "status": "PUBLIC_CODE_CANDIDATE_NOT_HISTORICALLY_PINNED",
        "value": f"uowoolab/FastMC, candidate commit {FASTMC_COMMIT_CANDIDATE} ({FASTMC_COMMIT_DATE})",
        "source": "https://github.com/uowoolab/FastMC",
        "exact_reproduction_role": "historical version must still be justified",
    },
    {
        "object": "framework_lj",
        "status": "PRIMARY_SOURCE_RECOVERED",
        "value": "UFF Lennard-Jones parameters for framework atoms",
        "source": "ARC-MOF GCMC methods",
        "exact_reproduction_role": "required",
    },
    {
        "object": "framework_partial_charges",
        "status": "PRIMARY_SOURCE_RECOVERED_AND_LOCAL_SELECTED_CIFS_VALIDATED",
        "value": "DFT-derived REPEAT charges for ARC-MOF screening",
        "source": "ARC-MOF GCMC methods + Project 7B Phase 2B2",
        "exact_reproduction_role": "required",
    },
    {
        "object": "cross_lj_mixing",
        "status": "PRIMARY_SOURCE_RECOVERED",
        "value": "Lorentz-Berthelot mixing rules",
        "source": "ARC-MOF GCMC methods",
        "exact_reproduction_role": "required",
    },
    {
        "object": "co2_guest_model",
        "status": "PAPER_REFERENCE_RECOVERED_PARAMETER_FILE_NOT_LOCAL",
        "value": "intermolecular potential parameters from Garcia-Sanchez et al.",
        "source": "ARC-MOF GCMC methods",
        "exact_reproduction_role": "recover exact numerical parameterization before run",
    },
    {
        "object": "n2_guest_model",
        "status": "BLOCKER_IN_HOUSE_PARAMETERIZATION",
        "value": "developed in-house to reproduce experimental N2 uptake isotherms in MOFs",
        "source": "ARC-MOF GCMC methods",
        "exact_reproduction_role": "exact numerical parameters must be recovered from authors/code/files",
    },
    {
        "object": "ch4_guest_model",
        "status": "PAPER_REFERENCE_RECOVERED_PARAMETER_FILE_NOT_LOCAL",
        "value": "parameters from Martin et al.",
        "source": "ARC-MOF GCMC methods",
        "exact_reproduction_role": "recover exact numerical parameterization before run",
    },
    {
        "object": "h2_guest_model",
        "status": "PAPER_REFERENCE_RECOVERED_PARAMETER_FILE_NOT_LOCAL",
        "value": "parameters from Belof et al.",
        "source": "ARC-MOF GCMC methods",
        "exact_reproduction_role": "recover exact numerical parameterization before run",
    },
    {
        "object": "screening_cycles",
        "status": "PRIMARY_SOURCE_RECOVERED",
        "value": "10,000 MC cycles total, split evenly between equilibration and production",
        "source": "ARC-MOF GCMC methods",
        "exact_reproduction_role": "required",
    },
    {
        "object": "exact_historical_input_deck",
        "status": "NOT_RECOVERED",
        "value": "",
        "source": "not present in Project 7B / ARC-MOF data package audit",
        "exact_reproduction_role": "blocker",
    },
    {
        "object": "historical_fastmc_commit_used_for_arc_mof",
        "status": "NOT_PINNED_BY_PRIMARY_SOURCE",
        "value": "",
        "source": "public repository history exists, but published screening commit was not recovered",
        "exact_reproduction_role": "blocker for bitwise/exact historical reproduction",
    },
    {
        "object": "dispersion_cutoff_and_shift",
        "status": "NOT_VERIFIED_FOR_ARC_MOF_SCREENING",
        "value": "",
        "source": "must not be inferred from other screening studies",
        "exact_reproduction_role": "blocker",
    },
    {
        "object": "electrostatics_method_and_precision",
        "status": "NOT_VERIFIED_FOR_ARC_MOF_SCREENING",
        "value": "",
        "source": "FastMC contains Ewald capability, but capability is not evidence of the ARC-MOF setting",
        "exact_reproduction_role": "blocker",
    },
    {
        "object": "simulation_supercell_rule",
        "status": "NOT_VERIFIED_FOR_ARC_MOF_SCREENING",
        "value": "",
        "source": "must be recovered rather than borrowed from unrelated screening protocols",
        "exact_reproduction_role": "blocker",
    },
    {
        "object": "mc_move_probabilities",
        "status": "NOT_VERIFIED_FOR_ARC_MOF_SCREENING",
        "value": "",
        "source": "FastMC parser supports move probabilities; published setting not yet recovered",
        "exact_reproduction_role": "blocker",
    },
    {
        "object": "pressure_to_fugacity_treatment",
        "status": "NOT_VERIFIED_FOR_ARC_MOF_SCREENING",
        "value": "",
        "source": "FastMC parser supports fugacity controls; published setting not yet recovered",
        "exact_reproduction_role": "blocker for non-ideal/high-pressure states",
    },
    {
        "object": "random_seed_policy",
        "status": "NOT_RECOVERED",
        "value": "",
        "source": "not recovered from Project 7B or primary paper",
        "exact_reproduction_role": "needed for exact trajectory reproduction, not necessarily ensemble reproduction",
    },
    {
        "object": "hoa_estimator_protocol",
        "status": "NOT_VERIFIED_FOR_ARC_MOF_SCREENING",
        "value": "",
        "source": "heat-of-adsorption values are provided, but exact estimator/settings not recovered in Phase 4A",
        "exact_reproduction_role": "blocker for HOA reproduction; not necessarily for uptake-only reproduction",
    },
]


def find_root(start: Path) -> Path:
    p = start.resolve()
    for cand in [p] + list(p.parents):
        if (cand / "Step 3 results").exists() and (cand / "Step 4 extension").exists():
            return cand
    raise RuntimeError("Could not locate Project 7B root.")


def resolve_col(df: pd.DataFrame, candidates: list[str]):
    lower = {str(c).lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    for actual in df.columns:
        al = str(actual).lower()
        for c in candidates:
            cc = c.lower()
            if len(cc) >= 4 and cc in al:
                return actual
    return None


def detect_tokens(text: str, patterns: dict[str, list[str]]) -> list[str]:
    found = []
    for name, pats in patterns.items():
        if any(re.search(p, text, flags=re.I) for p in pats):
            found.append(name)
    return found


def row_text(row: pd.Series) -> str:
    vals = []
    for v in row.tolist():
        if pd.isna(v):
            continue
        vals.append(str(v))
    return " | ".join(vals)


def classify_guest_feasibility(guests: list[str]) -> tuple[str, str]:
    gs = set(guests)
    if not gs:
        return (
            "GUEST_IDENTITY_NOT_RESOLVED",
            "Inspect source row/column semantics before any reconstruction."
        )
    if "N2" in gs:
        return (
            "BLOCKED_EXACT_N2_MODEL",
            "ARC-MOF used an in-house N2 parameterization; exact numerical model is not yet recovered."
        )
    if gs.issubset({"CO2", "CH4", "H2"}):
        return (
            "PUBLIC_REFERENCE_GUEST_MODELS_POTENTIALLY_RECOVERABLE",
            "Guest model references are named in the ARC-MOF paper, but numerical parameters/files still need recovery and validation."
        )
    return (
        "UNRESOLVED_GUEST_MODEL",
        "At least one guest lies outside the recovered ARC-MOF screening model registry."
    )


def main():
    print(TITLE)
    print("=" * 72)

    root = find_root(Path.cwd())
    frozen = root / "Step 3 results" / "Paper7B_Hosein_to_Shayan_Frozen_Source_Package"
    phase4a = root / "Step 4 results" / "04_host_guest_maps" / "phase4a_simulation_provenance"
    out = root / "Step 4 results" / "04_host_guest_maps" / "phase4b_external_protocol_reconstruction"
    out.mkdir(parents=True, exist_ok=True)

    p4a_summary = phase4a / "phase4a_summary.json"
    if not p4a_summary.exists():
        raise RuntimeError("Phase 4A summary is missing.")
    s4a = json.loads(p4a_summary.read_text(encoding="utf-8"))
    if s4a.get("decision") != "NO_EXACT_REPRODUCTION_DECK_IN_PROJECT":
        print("Decision: FAIL")
        print("FATAL: Phase 4A did not establish NO_EXACT_REPRODUCTION_DECK_IN_PROJECT.")
        sys.exit(2)

    state_candidates = [
        frozen / "08_structures" / "candidate_adsorption_conditions.csv",
        root / "analysis" / "final_structure_case_inspection" / "candidate_adsorption_conditions.csv",
    ]
    state_path = next((p for p in state_candidates if p.exists()), None)
    if state_path is None:
        raise RuntimeError("No selected-case adsorption-condition table found.")

    states = pd.read_csv(state_path, low_memory=False)

    pair_col = resolve_col(states, ["pair_id", "pair_key", "pair"])
    role_col = resolve_col(states, ["case_role", "selection_category", "role"])
    mof_col = resolve_col(states, ["mof_id", "framework_id", "framework", "mof"])
    condition_col = resolve_col(states, ["condition", "condition_id", "adsorption_condition"])
    guest_col = resolve_col(states, ["guest", "gas", "component", "species"])
    pressure_col = resolve_col(states, ["pressure", "pressure_bar", "pressure_kpa", "pressure_pa"])
    temp_col = resolve_col(states, ["temperature", "temperature_k", "temp_k"])

    row_rows = []
    for idx, r in states.iterrows():
        text = row_text(r)
        guests = detect_tokens(text, GUEST_TOKEN_PATTERNS)
        processes = detect_tokens(text, PROCESS_PATTERNS)
        status, reason = classify_guest_feasibility(guests)

        row_rows.append({
            "source_row": int(idx),
            "pair_id": str(r[pair_col]) if pair_col else "",
            "case_role": str(r[role_col]) if role_col else "",
            "mof_id": str(r[mof_col]) if mof_col else "",
            "condition": str(r[condition_col]) if condition_col else "",
            "explicit_guest": str(r[guest_col]) if guest_col else "",
            "pressure": str(r[pressure_col]) if pressure_col else "",
            "temperature": str(r[temp_col]) if temp_col else "",
            "detected_guests": ";".join(guests),
            "detected_processes": ";".join(processes),
            "guest_model_feasibility": status,
            "guest_model_reason": reason,
        })

    state_audit = pd.DataFrame(row_rows)
    state_audit.to_csv(out / "phase4b_selected_state_point_guest_feasibility.csv", index=False)

    protocol = pd.DataFrame(EXTERNAL_PROTOCOL)
    blocker_statuses = {
        "NOT_RECOVERED",
        "NOT_PINNED_BY_PRIMARY_SOURCE",
        "NOT_VERIFIED_FOR_ARC_MOF_SCREENING",
        "BLOCKER_IN_HOUSE_PARAMETERIZATION",
    }
    protocol["is_exact_reproduction_blocker"] = protocol["status"].isin(blocker_statuses)
    protocol.to_csv(out / "phase4b_external_protocol_evidence_registry.csv", index=False)

    fastmc = pd.DataFrame([{
        "repository": "uowoolab/FastMC",
        "candidate_commit": FASTMC_COMMIT_CANDIDATE,
        "candidate_commit_date": FASTMC_COMMIT_DATE,
        "evidence": (
            "public repository contains gcmc.f, readinputs.f, ewald.f, mc_moves.f; "
            "current parser exposes GCMC, pressure, fugacity, equilibration, cutoff, "
            "and move-probability controls"
        ),
        "historical_arc_mof_run_commit_known": False,
        "permission": "CODE_FAMILY_INSPECTION_ONLY_UNTIL_HISTORICAL_PROTOCOL_IS_VALIDATED",
    }])
    fastmc.to_csv(out / "phase4b_fastmc_code_provenance.csv", index=False)

    guest_summary = (
        state_audit.groupby(["detected_guests", "guest_model_feasibility"], dropna=False)
        .size().rename("rows").reset_index().sort_values("rows", ascending=False)
        if len(state_audit)
        else pd.DataFrame(columns=["detected_guests", "guest_model_feasibility", "rows"])
    )
    guest_summary.to_csv(out / "phase4b_guest_feasibility_summary.csv", index=False)

    n_public_candidate = int(
        (state_audit["guest_model_feasibility"] ==
         "PUBLIC_REFERENCE_GUEST_MODELS_POTENTIALLY_RECOVERABLE").sum()
    )
    n_n2_blocked = int(
        (state_audit["guest_model_feasibility"] == "BLOCKED_EXACT_N2_MODEL").sum()
    )
    n_unresolved = int(
        state_audit["guest_model_feasibility"].isin(
            ["GUEST_IDENTITY_NOT_RESOLVED", "UNRESOLVED_GUEST_MODEL"]
        ).sum()
    )
    exact_blockers = int(protocol["is_exact_reproduction_blocker"].sum())

    if n_public_candidate > 0:
        decision = "CONTROLLED_REIMPLEMENTATION_CANDIDATES_EXIST_EXACT_REPRODUCTION_STILL_BLOCKED"
        next_step = (
            "CHOOSE ONE NON-N2 SELECTED STATE POINT, RECOVER ITS EXACT GUEST NUMERICAL PARAMETERS, "
            "THEN AUDIT FASTMC INPUT/BUILD REQUIREMENTS BEFORE ANY GCMC RUN"
        )
    else:
        decision = "NO_SELECTED_STATE_POINT_READY_FOR_CONTROLLED_REIMPLEMENTATION"
        next_step = (
            "DO NOT BUILD SIMULATION SOFTWARE; RESOLVE GUEST/STATE-POINT PROVENANCE OR CLOSE PHASE 4"
        )

    summary = {
        "decision": decision,
        "state_point_rows": int(len(state_audit)),
        "state_rows_with_public_reference_guest_models": n_public_candidate,
        "state_rows_blocked_by_in_house_n2": n_n2_blocked,
        "state_rows_unresolved": n_unresolved,
        "protocol_objects": int(len(protocol)),
        "exact_reproduction_blockers": exact_blockers,
        "historical_arc_mof_fastmc_commit_pinned": False,
        "raspa_is_original_arc_mof_engine": False,
        "next_step": next_step,
    }
    (out / "phase4b_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    report = [
        "PROJECT 7B STEP 4 - PHASE 4B EXTERNAL PROTOCOL RECONSTRUCTION",
        "=" * 72,
        "",
        f"Decision: {decision}",
        "",
        "Critical correction",
        "-------------------",
        "ARC-MOF reports an in-house GCMC code based on DL_POLY, not RASPA.",
        "RASPA could be used only as an independent reimplementation, not as exact",
        "reproduction of the original ARC-MOF engine.",
        "",
        "Recovered from the ARC-MOF methods",
        "----------------------------------",
        "- framework LJ: UFF",
        "- framework charges for screening: REPEAT",
        "- unlike LJ mixing: Lorentz-Berthelot",
        "- CO2 model: Garcia-Sanchez et al.",
        "- N2 model: in-house (exact parameters not yet recovered)",
        "- CH4 model: Martin et al.",
        "- H2 model: Belof et al.",
        "- screening length: 10,000 MC cycles, half equilibration and half production",
        "",
        "Still missing",
        "-------------",
        "- historical input deck and exact code commit used for ARC-MOF",
        "- cutoff/shift convention",
        "- electrostatics settings",
        "- supercell construction rule",
        "- move probabilities",
        "- fugacity treatment",
        "- seed policy",
        "- exact numerical guest parameter files",
        "- exact HOA estimator if HOA reproduction is attempted",
        "",
        f"Next: {next_step}",
    ]
    (out / "phase4b_report.md").write_text("\n".join(report), encoding="utf-8")

    print(f"Decision: {decision}")
    print(f"Selected adsorption-condition rows audited: {len(state_audit)}")
    print(f"Rows with potentially recoverable public-reference guest models: {n_public_candidate}")
    print(f"Rows blocked by in-house N2 model: {n_n2_blocked}")
    print(f"Rows with unresolved guest identity/model: {n_unresolved}")
    print(f"Protocol objects audited: {len(protocol)}")
    print(f"Exact-reproduction blockers still open: {exact_blockers}")
    print("Historical ARC-MOF FastMC commit pinned: False")
    print("Original ARC-MOF engine was RASPA: False")

    if not guest_summary.empty:
        print("\nSelected-state guest feasibility:")
        for _, r in guest_summary.iterrows():
            print(
                f"  guests={r['detected_guests'] or '<unresolved>'} | "
                f"{r['guest_model_feasibility']} | rows={int(r['rows'])}"
            )

    print(f"\nNext: {next_step}")
    print("No molecular simulation was run and no adsorption/HOA value was recomputed.")
    print(f"Outputs: {out}")


if __name__ == "__main__":
    main()
