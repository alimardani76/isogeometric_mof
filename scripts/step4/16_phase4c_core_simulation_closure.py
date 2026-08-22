#!/usr/bin/env python3
"""
Project 7B Step 4 - Phase 4C
Core simulation-branch closure.

Purpose
-------
Close the host-guest simulation branch for the CORE Step 4 paper without running
a new molecular simulation.

Phase 4B established:
- controlled reimplementation candidates exist for many selected non-N2 states;
- exact historical ARC-MOF reproduction remains blocked;
- the N2 model is an explicit in-house-parameter blocker;
- the historical FastMC commit/input deck is not pinned.

Core decision
-------------
Do NOT spend core-paper scope on reconstructing GCMC now.
Preserve the entire simulation/DFT branch as an OPTIONAL EXTENDED track.

This phase computes no new scientific quantity.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

TITLE = "PROJECT 7B STEP 4 - PHASE 4C CORE SIMULATION-BRANCH CLOSURE"


def find_root(start: Path) -> Path:
    p = start.resolve()
    for cand in [p] + list(p.parents):
        if (cand / "Step 3 results").exists() and (cand / "Step 4 extension").exists():
            return cand
    raise RuntimeError("Could not locate Project 7B root.")


def main():
    print(TITLE)
    print("=" * 72)

    root = find_root(Path.cwd())
    p4b = root / "Step 4 results" / "04_host_guest_maps" / "phase4b_external_protocol_reconstruction"
    out = root / "Step 4 results" / "04_host_guest_maps" / "phase4c_core_closure"
    out.mkdir(parents=True, exist_ok=True)

    summary_path = p4b / "phase4b_summary.json"
    protocol_path = p4b / "phase4b_external_protocol_evidence_registry.csv"
    guest_path = p4b / "phase4b_guest_feasibility_summary.csv"

    required = [summary_path, protocol_path, guest_path]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("Decision: FAIL")
        for p in missing:
            print(f"FATAL: missing {p}")
        sys.exit(2)

    s = json.loads(summary_path.read_text(encoding="utf-8"))
    protocol = pd.read_csv(protocol_path, low_memory=False)
    guests = pd.read_csv(guest_path, low_memory=False)

    expected = "CONTROLLED_REIMPLEMENTATION_CANDIDATES_EXIST_EXACT_REPRODUCTION_STILL_BLOCKED"
    if s.get("decision") != expected:
        print("Decision: FAIL")
        print(f"FATAL: Phase 4B decision was {s.get('decision')!r}, expected {expected!r}.")
        sys.exit(2)

    rows = [
        {
            "branch": "core_manuscript",
            "decision": "CLOSE_WITHOUT_NEW_GCMC",
            "reason": (
                "Selected-case structural chemistry already adds defensible core value, "
                "whereas exact ARC-MOF simulation reproduction requires a new protocol-reconstruction task."
            ),
            "next_action": "Proceed to Phase 6 core integration.",
        },
        {
            "branch": "selected_case_gcmc",
            "decision": "DEFER_EXTENDED_ONLY",
            "reason": (
                "720 selected-condition rows use guests whose literature models may be recoverable, "
                "but the historical engine/input deck and several protocol settings remain unpinned."
            ),
            "next_action": (
                "If extended later, choose one non-N2 frozen state point and reproduce uptake first."
            ),
        },
        {
            "branch": "n2_containing_gcmc",
            "decision": "BLOCKED_UNTIL_IN_HOUSE_N2_MODEL_RECOVERED",
            "reason": (
                "ARC-MOF used an in-house N2 parameterization; exact numerical parameters were not recovered."
            ),
            "next_action": "Do not attempt exact N2 reproduction from guessed parameters.",
        },
        {
            "branch": "density_site_occupancy_maps",
            "decision": "DEFER_UNTIL_UPTAKE_REPRODUCTION_PASSES",
            "reason": (
                "Mechanism visualizations inherit the simulation model and are not meaningful as reproduction evidence "
                "until at least one frozen adsorption state is reproduced satisfactorily."
            ),
            "next_action": "No density maps in the core paper.",
        },
        {
            "branch": "dft_or_higher_fidelity",
            "decision": "DEFER_EXTENDED_ONLY",
            "reason": (
                "No sufficiently narrow host-guest hypothesis has yet been established that justifies higher-fidelity work."
            ),
            "next_action": "Revisit only after a successful controlled GCMC reproduction creates a specific testable hypothesis.",
        },
    ]
    closure = pd.DataFrame(rows)
    closure.to_csv(out / "phase4c_branch_closure_map.csv", index=False)

    evidence = pd.DataFrame([
        {
            "object": "selected-case CIF/local chemistry",
            "core_status": "KEEP",
            "placement": "Figure 5 / supporting structural context",
            "boundary": "case-level structural chemistry only",
        },
        {
            "object": "same-chemistry controls",
            "core_status": "KEEP",
            "placement": "existing main robustness architecture",
            "boundary": "empirical observational null reference, not randomized permutation null",
        },
        {
            "object": "new GCMC reproduction",
            "core_status": "DO_NOT_ADD",
            "placement": "none",
            "boundary": "external protocol reconstruction remains incomplete",
        },
        {
            "object": "adsorption-density/site-occupancy maps",
            "core_status": "DO_NOT_ADD",
            "placement": "none",
            "boundary": "requires successful reproduction gate first",
        },
        {
            "object": "DFT mechanism validation",
            "core_status": "DO_NOT_ADD",
            "placement": "none",
            "boundary": "requires a sharper mechanism hypothesis from reproduced host-guest evidence",
        },
    ])
    evidence.to_csv(out / "phase4c_core_evidence_boundary_map.csv", index=False)

    report = [
        "PROJECT 7B STEP 4 - PHASE 4 CORE CLOSURE",
        "=" * 72,
        "",
        "Decision: PASS_AND_CLOSE_CORE_PHASE_4",
        "",
        "Core paper decision",
        "-------------------",
        "Do not run a new molecular simulation for the core Step 4 manuscript.",
        "",
        "Why",
        "---",
        "Phase 4B showed that controlled reimplementation is possible in principle for many",
        "non-N2 selected states, but exact historical reproduction remains blocked by missing",
        "input/protocol provenance. The N2 branch additionally depends on an unrecovered in-house",
        "guest model. Generating density maps now would therefore add a new simulation methodology",
        "rather than simply validate the frozen ARC-MOF evidence.",
        "",
        "What remains in the core",
        "------------------------",
        "- Phase 2 selected-case structural chemistry and validated site-level REPEAT charge mapping.",
        "- Phase 3 dependency-aware decision to retain same-chemistry controls rather than add an invalid permutation null.",
        "- Existing adsorption, HOA, robustness, topology, pressure, and process results from the frozen analysis.",
        "",
        "What moves to the extended track",
        "--------------------------------",
        "- selected-case GCMC reproduction",
        "- density/site-occupancy maps",
        "- host-guest energy decomposition",
        "- DFT / higher-fidelity binding validation",
        "",
        "Next",
        "----",
        "Proceed directly to Phase 6 core integration.",
    ]
    (out / "phase4c_core_closure_report.md").write_text("\n".join(report), encoding="utf-8")

    summary = {
        "decision": "PASS_AND_CLOSE_CORE_PHASE_4",
        "core_new_gcmc": False,
        "core_density_maps": False,
        "core_dft": False,
        "extended_gcmc": "DEFERRED",
        "extended_dft": "DEFERRED",
        "phase5_core_status": "SKIPPED_NOT_REQUIRED",
        "next_phase": "PHASE_6_CORE_INTEGRATION",
    }
    (out / "phase4c_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Decision: PASS_AND_CLOSE_CORE_PHASE_4")
    print("New GCMC for core paper: NOT ADDED")
    print("Density/site-occupancy maps for core paper: NOT ADDED")
    print("DFT/higher-fidelity work for core paper: NOT ADDED")
    print("Extended simulation branch: DEFERRED")
    print("Phase 5 core status: SKIPPED_NOT_REQUIRED")
    print("")
    print("Next: PHASE_6_CORE_INTEGRATION")
    print("No molecular simulation or new scientific effect was computed.")
    print(f"Outputs: {out}")


if __name__ == "__main__":
    main()
