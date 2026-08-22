#!/usr/bin/env python3
"""
Project 7B Step 4 - Phase 3B
Falsification closure and null-reference decision.

Purpose
-------
Close Phase 3 after the dependency/exchangeability audit established that no
simple shuffled-label or row-permutation test is currently defensible.

This phase performs NO permutation, NO p-value calculation, NO bootstrap, and
NO new scientific effect calculation. It records the statistical boundary and
freezes the existing same-chemistry controls as the defensible null reference.

READ ONLY with respect to Steps 1-3 and prior Step 4 outputs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

TITLE = "PROJECT 7B STEP 4 - PHASE 3B FALSIFICATION CLOSURE"


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
    p3a = root / "Step 4 results" / "03_falsification" / "phase3a_dependency_exchangeability_audit"
    out = root / "Step 4 results" / "03_falsification" / "phase3b_falsification_closure"
    out.mkdir(parents=True, exist_ok=True)

    summary_path = p3a / "phase3a_summary.json"
    schemes_path = p3a / "phase3a_candidate_randomization_schemes.csv"
    graph_path = p3a / "phase3a_primary_pair_graph_summary.csv"
    control_path = p3a / "phase3a_control_table_schema_audit.csv"

    required = [summary_path, schemes_path, graph_path, control_path]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("Decision: FAIL")
        for p in missing:
            print(f"FATAL: missing {p}")
        sys.exit(2)

    p3a_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    schemes = pd.read_csv(schemes_path, low_memory=False)
    graph = pd.read_csv(graph_path, low_memory=False)
    controls = pd.read_csv(control_path, low_memory=False)

    if p3a_summary.get("decision") != "NO_VALID_SHUFFLED_LABEL_TEST_ESTABLISHED":
        print("Decision: FAIL")
        print(
            "FATAL: Phase 3A did not establish the expected "
            "NO_VALID_SHUFFLED_LABEL_TEST_ESTABLISHED state."
        )
        sys.exit(2)

    # Freeze scheme decisions.
    closure_rows = []
    for _, r in schemes.iterrows():
        status = str(r["status"])
        if status.startswith("REJECT"):
            closure = "CLOSED_NOT_TO_BE_RUN"
        elif status.startswith("NO_IMPLEMENTABLE"):
            closure = "CLOSED_NO_VALID_OBJECT"
        elif status.startswith("CONDITIONAL"):
            closure = "DEFERRED_EXTENDED_METHOD_ONLY"
        elif status.startswith("POSSIBLE_NON_RANDOMIZATION"):
            closure = "DEFERRED_NOT_NEEDED_FOR_CORE"
        else:
            closure = "DEFERRED"

        closure_rows.append({
            "scheme": r["scheme"],
            "phase3a_status": status,
            "phase3b_closure": closure,
            "reason": r["reason"],
            "would_test": r["would_test"],
        })

    closure = pd.DataFrame(closure_rows)
    closure.to_csv(out / "phase3b_randomization_scheme_closure.csv", index=False)

    g = graph.iloc[0]
    framework_reuse = int(g["frameworks_used_in_more_than_one_pair"])
    unique_frameworks = int(g["unique_frameworks"])
    reuse_fraction = float(g["fraction_frameworks_used_in_more_than_one_pair"])
    components = int(g["connected_components"])
    largest_frameworks = int(g["largest_component_frameworks"])
    largest_edges = int(g["largest_component_pair_edges"])

    evidence_map = pd.DataFrame([
        {
            "object": "primary same-chemistry controls",
            "status": "KEEP_AS_DEFENSIBLE_NULL_REFERENCE",
            "allowed_use": (
                "Empirical matched background for asking whether observed chemistry "
                "separation exceeds same-chemistry separation under the existing design."
            ),
            "boundary": (
                "Observational matched control distribution, not randomized treatment assignment "
                "and not an exact permutation null."
            ),
        },
        {
            "object": "symmetric same-chemistry controls",
            "status": "KEEP_AS_ROBUSTNESS_NULL_REFERENCE",
            "allowed_use": (
                "Symmetry-balanced control reference supporting the robustness of the "
                "chemistry-versus-control comparison."
            ),
            "boundary": (
                "Still observational and dependent through shared framework structure."
            ),
        },
        {
            "object": "global shuffled-label null",
            "status": "REJECT",
            "allowed_use": "none",
            "boundary": (
                "Framework reuse and repeated pair-condition rows violate independent row/edge exchangeability."
            ),
        },
        {
            "object": "matched-set treatment/control permutation",
            "status": "REJECT_FOR_CURRENT_FROZEN_OBJECTS",
            "allowed_use": "none",
            "boundary": (
                "No implementable explicit matched-set object with justified exchangeable treatment/control assignment exists."
            ),
        },
        {
            "object": "component-cluster bootstrap / sandwich sensitivity",
            "status": "DEFERRED_EXTENDED_ONLY",
            "allowed_use": (
                "Possible future dependence-aware asymptotic sensitivity if a reviewer specifically "
                "requires additional uncertainty treatment."
            ),
            "boundary": (
                "Not an exact shuffled-label null; requires a new inferential layer and sufficient independent components."
            ),
        },
    ])
    evidence_map.to_csv(out / "phase3b_null_reference_evidence_map.csv", index=False)

    report = [
        "PROJECT 7B STEP 4 - PHASE 3 FALSIFICATION CLOSURE",
        "=" * 72,
        "",
        "Decision: PASS_AND_CLOSE_PHASE_3",
        "",
        "Why no permutation test is added",
        "--------------------------------",
        f"- {framework_reuse:,} of {unique_frameworks:,} frameworks "
        f"({reuse_fraction:.1%}) occur in more than one primary pair.",
        f"- The primary pair graph contains {components:,} connected components; "
        f"the largest contains {largest_frameworks} frameworks and {largest_edges} pair edges.",
        "- Pair effects are repeated over adsorption conditions rather than being independent rows.",
        "- The frozen control outputs do not contain an implementable matched-set randomization object.",
        "- Chemistry/intervention labels are observed structural categories, not randomized assignments.",
        "",
        "Core decision",
        "-------------",
        "Do not add a shuffled-label, row-shuffle, condition-shuffle, or sign-flip p-value.",
        "The existing primary and symmetric same-chemistry control distributions remain the",
        "scientifically defensible empirical null references for the core manuscript.",
        "",
        "Deferred only if later demanded",
        "-------------------------------",
        "A component-cluster bootstrap, sandwich-style sensitivity, or restricted residual",
        "permutation would be a genuinely new inferential layer. It is not required for the",
        "core Project 7B claim and should not be added merely to create another p-value.",
        "",
        "Next",
        "----",
        "Proceed to Phase 4A only if selected-case host-guest mapping is still desired.",
        "Phase 4A must first recover the exact original adsorption simulation protocol and",
        "test whether the selected structures can reproduce the frozen adsorption/HOA values",
        "before any density map or mechanism visualization is generated.",
    ]
    (out / "phase3b_closure_report.md").write_text("\n".join(report), encoding="utf-8")

    summary = {
        "decision": "PASS_AND_CLOSE_PHASE_3",
        "permutation_test_added": False,
        "permutation_p_values_added": False,
        "primary_same_chemistry_controls": "KEEP_AS_DEFENSIBLE_NULL_REFERENCE",
        "symmetric_same_chemistry_controls": "KEEP_AS_ROBUSTNESS_NULL_REFERENCE",
        "dependency_cluster_fallback": "DEFERRED_EXTENDED_ONLY",
        "next_phase": "PHASE_4A_SIMULATION_PROVENANCE_AND_REPRODUCTION_FEASIBILITY",
    }
    (out / "phase3b_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Decision: PASS_AND_CLOSE_PHASE_3")
    print("Permutation / shuffled-label test: NOT ADDED")
    print("Permutation p-values / FDR: NOT ADDED")
    print("Primary same-chemistry controls: KEEP_AS_DEFENSIBLE_NULL_REFERENCE")
    print("Symmetric same-chemistry controls: KEEP_AS_ROBUSTNESS_NULL_REFERENCE")
    print("Dependency-cluster fallback: DEFERRED_EXTENDED_ONLY")

    print("\nClosed/deferred schemes:")
    for _, r in closure.iterrows():
        print(f"  {r['scheme']} -> {r['phase3b_closure']}")

    print("\nNext: PHASE_4A_SIMULATION_PROVENANCE_AND_REPRODUCTION_FEASIBILITY")
    print("No labels were shuffled and no new scientific effect was computed.")
    print(f"Outputs: {out}")


if __name__ == "__main__":
    main()
