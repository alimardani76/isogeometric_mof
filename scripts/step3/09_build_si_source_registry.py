#!/usr/bin/env python3
"""Project 7B2 Step 3, file 09: build the lean SI source registry.

Place inside:
    Step 3 production/

Run from the 7B2 project root:
    python "Step 3 production/09_build_si_source_registry.py"

Purpose
-------
Assess whether each proposed evidence-bearing SI figure and table can be built
from exact frozen outputs. This script does not render figures, typeset tables,
or perform scientific analysis.

Outputs
-------
    Step 3 results/si_production/
        09_si_item_registry.csv
        09_source_file_registry.csv
        09_blocked_items.csv
        09_report.txt
        09_manifest.json
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "Step 3 results" / "si_production"
OUT.mkdir(parents=True, exist_ok=True)

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", "archive", "tmp", "temp",
    "cache", "full_pair_rules_work", "full_pair_rules", "pair_rules_work",
    "si_production", "figure_source_data",
}

# Candidate basename groups are alternatives only where the same scientific
# source may have a different final filename. Every required-column check must
# pass on the resolved file.
SOURCE_SPECS = {
    "primary_counts": {
        "names": ["final_primary_pair_counts.csv"],
        "columns": ["intervention", "raw_pairs", "unique_pair_keys"],
    },
    "caliper_support": {
        "names": ["caliper_sensitivity_support.csv"],
        "columns": ["tier", "tier_order", "intervention", "raw_pairs", "related_groups"],
    },
    "residual_summary": {
        "names": ["step2_residual_geometry_summary.csv"],
        "columns": ["intervention", "effect_measure", "median_absolute_rho"],
    },
    "symmetric_controls": {
        "names": ["step5b_symmetric_control_results.csv"],
        "columns": ["intervention", "target", "effect_measure", "median_chemistry_minus_control"],
    },
    "primary_controls": {
        "names": ["step3_same_chemistry_control_results.csv"],
        "columns": ["intervention", "target", "effect_measure", "median_chemistry_minus_control"],
    },
    "hoa_conditions": {
        "names": ["heat_adsorption_condition_results.csv"],
        "columns": ["intervention", "target", "effect_measure", "spearman_rho_heat_vs_adsorption_separation"],
    },
    "hoa_pressure": {
        "names": ["heat_adsorption_pressure_results.csv"],
        "columns": ["intervention", "target", "effect_measure", "median_heat_low", "median_heat_high"],
    },
    "guest_results": {
        "names": ["05_results.csv"],
        "columns": ["quantity", "intervention", "comparison", "regime", "median_paired_difference_CO2_minus_coguest"],
        "path_hints": ["guest_specificity"],
    },
    "guest_summary": {
        "names": ["05_summary.csv"],
        "columns": ["quantity", "intervention", "measure"],
        "path_hints": ["guest_specificity"],
    },
    "adjustment_results": {
        "names": ["03_results.csv"],
        "columns": ["target", "effect_measure", "unadjusted_linker_minus_control", "adjusted_linker_minus_control"],
        "path_hints": ["residual_adjustment"],
    },
    "adjustment_summary": {
        "names": ["03_summary.csv"],
        "columns": ["effect_measure", "conditions", "adjusted_positive"],
        "path_hints": ["residual_adjustment"],
    },
    "balance": {
        "names": ["04_balance.csv"],
        "columns": ["intervention", "geometry_variable", "absolute_global_smd"],
        "path_hints": ["balance_family_dominance"],
    },
    "family_results": {
        "names": ["04_family_exclusion_results.csv"],
        "columns": ["intervention", "target", "effect_measure", "scenario", "median_effect"],
    },
    "family_summary": {
        "names": ["04_family_exclusion_summary.csv"],
        "columns": ["intervention", "effect_measure", "conditions"],
    },
    "reciprocal_summary": {
        "names": ["reciprocal_covariance_matching_summary.csv"],
        "columns": ["intervention"],
    },
    "topology_summary": {
        "names": ["step1_topology_robustness_summary.csv"],
        "columns": ["intervention"],
    },
    "process_summary": {
        "names": ["process_translation_summary_final.csv"],
        "columns": ["intervention", "process", "metric", "estimate"],
    },
    "final_cases": {
        "names": ["02_final_case_set.csv"],
        "columns": ["selection_category", "pair_key", "id_a", "id_b"],
    },
    "case_frameworks": {
        "names": ["02_final_case_frameworks.csv"],
        "columns": ["framework_id", "pair_key", "selection_category"],
    },
    "charge_elements": {
        "names": ["03_element_charge_summaries.csv"],
        "columns": ["mof_id", "element", "is_metal", "charge_mean"],
        "path_hints": ["case_chemistry"],
    },
    "charge_pairs": {
        "names": ["03_pair_charge_contrasts.csv"],
        "columns": ["selection_category", "pair_key", "id_a", "id_b"],
        "path_hints": ["case_chemistry"],
    },
    "case_review": {
        "names": ["final_case_review_sheet.csv"],
        "columns": ["selection_category", "case_rank", "pair_key", "renderable"],
    },
    "effect_run_summary": {
        "names": ["corrected_effect_run_summary.csv"],
        "columns": [],
    },
    "inspection_manifest": {
        "names": ["inspection_manifest.json"],
        "columns": [],
    },
    # The following are deliberately broad discovery targets. Their absence
    # blocks only the SI item that needs them.
    "coordination_classification": {
        "names": [
            "metal_coordination_pair_classification.csv",
            "coordination_pair_classification.csv",
            "metal_coordination_pair_classification.parquet",
            "coordination_pair_classification.parquet",
        ],
        "columns_any": [
            ["coordination_class"], ["coordination_status"], ["pair_class"]
        ],
    },
    "cohort_attrition": {
        "names": [
            "cohort_attrition.csv", "cohort_counts.csv", "cohort_summary.csv",
            "step1_cohort_counts.csv", "framework_cohort_counts.csv",
        ],
        "columns_any": [["cohort"], ["stage"], ["status"]],
    },
    "intervention_rejections": {
        "names": [
            "pair_rejection_summary.csv", "chemistry_rejection_summary.csv",
            "intervention_rejection_summary.csv", "classification_rejection_summary.csv",
        ],
        "columns_any": [["reason"], ["status"], ["rejection_reason"]],
    },
    "condition_scales": {
        "names": ["adsorption_condition_scales.csv"],
        "columns": ["target", "T/K", "p/bar"],
    },
    "hoa_pair_coverage": {
        "names": ["7B2_heat_pair_coverage.csv"],
        "columns": ["intervention", "target", "T/K", "p/bar", "hoa_pair_coverage"],
    },
    "hoa_source_coverage": {
        "names": ["7B2_heat_source_coverage.csv"],
        "columns": ["raw_file", "target", "rows", "hoa_numeric"],
    },
}

ITEMS = [
    # Figures
    ("Figure S01", "figure", "Coordination classification and setting sensitivity",
     "Why only the coordination-compatible metal subset enters the primary analysis",
     True, ["coordination_classification"]),
    ("Figure S02", "figure", "Cohort construction and analysis-specific attrition",
     "Distinguishes geometry, adsorption, CIF-supported, chemistry-supported, and pair cohorts",
     True, ["primary_counts", "effect_run_summary", "inspection_manifest", "cohort_attrition"]),
    ("Figure S03", "figure", "Geometry-tier support and pressure-direction stability",
     "Shows the support-versus-stringency trade-off without selecting a favorable tier",
     True, ["caliper_support"]),
    ("Figure S04", "figure", "Residual geometry, balance, and adjusted linker sensitivity",
     "Exposes the main limitation and whether the linker contrast persists after adjustment",
     True, ["residual_summary", "balance", "adjustment_results", "adjustment_summary"]),
    ("Figure S05", "figure", "Reciprocal matching, topology restriction, and localized disagreements",
     "Tests dependence on matching architecture and topology provenance",
     True, ["reciprocal_summary", "topology_summary"]),
    ("Figure S06", "figure", "Complete primary and symmetric same-chemistry controls",
     "Expands the reduced main-text control result to all measures and conditions",
     True, ["primary_controls", "symmetric_controls"]),
    ("Figure S07", "figure", "Complete condition-level HOA associations",
     "Shows all linker and metal correlations and uncertainty, not only summary counts",
     True, ["hoa_conditions"]),
    ("Figure S08", "figure", "Complete guest- and pressure-specific energetic and adsorption contrasts",
     "Shows all process regimes, measures, interventions, and the CO2/H2 boundary",
     True, ["hoa_pressure", "guest_results", "guest_summary"]),
    ("Figure S09", "figure", "Complete process translation",
     "Shows all supported linker and metal working-capacity and selectivity results",
     True, ["process_summary"]),
    ("Figure S10", "figure", "Selected-case charge fingerprints",
     "Optional case-level context; retained only if visually informative without implying mechanism",
     False, ["final_cases", "charge_elements", "charge_pairs"]),

    # Tables
    ("Table S01", "table", "Input inventory, hashes, software, and licences",
     "Reproducibility inventory", True, ["inspection_manifest"]),
    ("Table S02", "table", "Identifier rules and reconciliation summary",
     "Documents canonicalization and unmatched-source handling", True, ["effect_run_summary"]),
    ("Table S03", "table", "Cohort, adsorption, and HOA attrition",
     "Combines cohort counts with near-complete uptake and HOA coverage", True,
     ["cohort_attrition", "hoa_pair_coverage", "hoa_source_coverage"]),
    ("Table S04", "table", "CIF, charge, and coordination audit",
     "Documents parsing integrity and conservative metal classification", True,
     ["inspection_manifest", "coordination_classification"]),
    ("Table S05", "table", "Intervention eligibility and rejection summary",
     "Explains why candidate comparisons reduce to the primary classes", True,
     ["intervention_rejections", "primary_counts"]),
    ("Table S06", "table", "Primary catalogue support",
     "Pairs, groups, frameworks, exact changes, and support breadth", True,
     ["primary_counts", "caliper_support"]),
    ("Table S07", "table", "Adsorption-condition definitions, scales, and completeness",
     "Defines targets, temperatures, pressures, offsets, robust scales, uptake and HOA coverage", True,
     ["condition_scales", "hoa_pair_coverage"]),
    ("Table S08", "table", "Fixed tiers and residual-geometry summary",
     "Reproducible matching limits, support, and residual associations", True,
     ["caliper_support", "residual_summary"]),
    ("Table S09", "table", "Reciprocal and topology robustness",
     "Summarizes agreement and localized disagreements", True,
     ["reciprocal_summary", "topology_summary"]),
    ("Table S10", "table", "Primary and symmetric control summary",
     "Compact inferential summary; exhaustive rows remain machine-readable", True,
     ["primary_controls", "symmetric_controls"]),
    ("Table S11", "table", "HOA association and guest-specificity summary",
     "Compact energetic and guest-specificity evidence", True,
     ["hoa_conditions", "guest_results", "guest_summary"]),
    ("Table S12", "table", "Residual adjustment and SMD balance",
     "Defines attenuation and geometry imbalance", True,
     ["adjustment_results", "adjustment_summary", "balance"]),
    ("Table S13", "table", "Family exclusion and process translation",
     "Shows non-dominance by large families and practical translation", True,
     ["family_results", "family_summary", "process_summary"]),
    ("Table S14", "table", "Frozen cases, CIF provenance, and charge fingerprints",
     "Documents final examples without printing all atom rows", True,
     ["final_cases", "case_frameworks", "case_review", "charge_elements", "charge_pairs"]),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def iter_active_files():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d.lower() not in EXCLUDE_DIRS and not d.startswith(".")]
        for name in files:
            p = Path(base) / name
            if p.resolve() == Path(__file__).resolve():
                continue
            yield p


def priority(path: Path) -> tuple:
    rel = str(path.relative_to(ROOT)).lower()
    if "step 3 results" in rel:
        rank = 0
    elif "step 2 results" in rel:
        rank = 1
    elif "analysis" in rel:
        rank = 2
    elif "step 1" in rel:
        rank = 3
    else:
        rank = 4
    return rank, len(path.parts), rel


def read_columns(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return list(pd.read_csv(path, nrows=0, low_memory=False).columns), None
    if suffix in {".parquet", ".pq"}:
        return list(pd.read_parquet(path).columns), None
    if suffix == ".json":
        return [], None
    return [], f"unsupported source extension {suffix}"


def row_count(path: Path):
    try:
        if path.suffix.lower() == ".csv":
            return sum(1 for _ in path.open("rb")) - 1
        if path.suffix.lower() in {".parquet", ".pq"}:
            try:
                import pyarrow.parquet as pq
                return pq.ParquetFile(path).metadata.num_rows
            except Exception:
                return len(pd.read_parquet(path))
        if path.suffix.lower() == ".json":
            return 1
    except Exception:
        return None
    return None


def validate_columns(cols, spec):
    required = spec.get("columns", [])
    missing = [c for c in required if c not in cols]
    if missing:
        return False, "missing required columns: " + ", ".join(missing)
    alternatives = spec.get("columns_any", [])
    if alternatives and not any(all(c in cols for c in alt) for alt in alternatives):
        return False, "none of the alternative column sets found: " + repr(alternatives)
    return True, "OK"


def resolve_source(key, files):
    spec = SOURCE_SPECS[key]
    candidates = [p for p in files if p.name in spec["names"]]
    hints = [x.lower() for x in spec.get("path_hints", [])]
    if hints:
        hinted = [p for p in candidates if all(h in str(p).lower() for h in hints)]
        if hinted:
            candidates = hinted
    candidates.sort(key=priority)
    valid = []
    rejected = []
    for p in candidates:
        cols, error = read_columns(p)
        if error:
            rejected.append((p, error))
            continue
        ok, reason = validate_columns(cols, spec)
        if ok:
            valid.append((p, cols))
        else:
            rejected.append((p, reason))
    if not valid:
        detail = "; ".join(f"{p}: {reason}" for p, reason in rejected)
        status = "NOT_FOUND" if not candidates else "FOUND_BUT_SCHEMA_MISMATCH"
        return None, [], status, detail
    best_priority = priority(valid[0][0])[0]
    peers = [(p, c) for p, c in valid if priority(p)[0] == best_priority]
    if len(peers) > 1:
        hashes = {sha256(p) for p, _ in peers}
        if len(hashes) > 1:
            return None, [], "AMBIGUOUS_CONFLICTING_SOURCES", "; ".join(str(p) for p, _ in peers)
    return peers[0][0], peers[0][1], "RESOLVED", ""


def main():
    files = list(iter_active_files())
    source_rows = []
    resolved = {}
    for key in SOURCE_SPECS:
        path, cols, status, detail = resolve_source(key, files)
        resolved[key] = path
        source_rows.append({
            "source_key": key,
            "status": status,
            "resolved_path": str(path) if path else "",
            "basename": path.name if path else "",
            "rows": row_count(path) if path else None,
            "columns": ";".join(cols),
            "sha256": sha256(path) if path else "",
            "detail": detail,
        })
    source_df = pd.DataFrame(source_rows)
    source_df.to_csv(OUT / "09_source_file_registry.csv", index=False)

    item_rows = []
    for item_id, item_type, title, value, essential, keys in ITEMS:
        missing = [k for k in keys if resolved.get(k) is None]
        if not missing:
            status = "READY"
            decision = "BUILD"
        elif essential:
            status = "BLOCKED_REQUIRED_SOURCE"
            decision = "DO_NOT_BUILD_YET"
        else:
            status = "OPTIONAL_BLOCKED"
            decision = "OMIT_UNLESS_RESOLVED"
        item_rows.append({
            "item_id": item_id,
            "item_type": item_type,
            "title": title,
            "information_added": value,
            "essential": essential,
            "source_keys": ";".join(keys),
            "missing_source_keys": ";".join(missing),
            "status": status,
            "decision": decision,
        })
    item_df = pd.DataFrame(item_rows)
    item_df.to_csv(OUT / "09_si_item_registry.csv", index=False)
    blocked = item_df[item_df.status.ne("READY")].copy()
    blocked.to_csv(OUT / "09_blocked_items.csv", index=False)

    ready_figures = item_df[(item_df.item_type == "figure") & item_df.status.eq("READY")]
    ready_tables = item_df[(item_df.item_type == "table") & item_df.status.eq("READY")]
    blocked_required = item_df[item_df.status.eq("BLOCKED_REQUIRED_SOURCE")]
    optional_blocked = item_df[item_df.status.eq("OPTIONAL_BLOCKED")]

    report = [
        "PROJECT 7B2 LEAN SI SOURCE REGISTRY", "=" * 72,
        f"Active project files scanned: {len(files)}",
        f"Sources resolved: {int(source_df.status.eq('RESOLVED').sum())}/{len(source_df)}",
        f"Essential SI figures ready: {len(ready_figures)}/9",
        f"Optional SI figures ready: {int(((item_df.item_type=='figure') & (~item_df.essential) & item_df.status.eq('READY')).sum())}/1",
        f"Core SI tables ready: {len(ready_tables)}/14",
        f"Required items blocked: {len(blocked_required)}",
        f"Optional items blocked: {len(optional_blocked)}",
        "",
        "READY FIGURES",
    ]
    report.extend(f"- {r.item_id}: {r.title}" for _, r in ready_figures.iterrows())
    report.append("")
    report.append("READY TABLES")
    report.extend(f"- {r.item_id}: {r.title}" for _, r in ready_tables.iterrows())
    if len(blocked):
        report.extend(["", "BLOCKED ITEMS"])
        report.extend(
            f"- {r.item_id}: missing [{r.missing_source_keys}]"
            for _, r in blocked.iterrows()
        )
    report.extend([
        "",
        "Decision rule:",
        "- render only READY items",
        "- resolve authoritative frozen sources for blocked essential items",
        "- omit optional charge figure if it does not add a readable pattern",
        "- do not reconstruct missing scientific values from manuscript prose",
        "- do not create exhaustive PDF tables when machine-readable CSV is better",
    ])
    (OUT / "09_report.txt").write_text("\n".join(report), encoding="utf-8", newline="\n")

    manifest = {
        "stage": "Project 7B2 lean SI source registry",
        "created": datetime.now().isoformat(timespec="seconds"),
        "script": "09_build_si_source_registry.py",
        "project_root": str(ROOT),
        "files_scanned": len(files),
        "source_specs": SOURCE_SPECS,
        "si_items": [
            {
                "item_id": x[0], "item_type": x[1], "title": x[2],
                "information_added": x[3], "essential": x[4], "source_keys": x[5]
            } for x in ITEMS
        ],
        "new_scientific_analysis": False,
        "figures_rendered": False,
        "tables_typeset": False,
        "outputs": [
            "09_si_item_registry.csv", "09_source_file_registry.csv",
            "09_blocked_items.csv", "09_report.txt"
        ],
        "python": sys.version,
        "pandas": pd.__version__,
    }
    (OUT / "09_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8", newline="\n"
    )
    print("\n".join(report))
    print(f"\nOutputs: {OUT}")


if __name__ == "__main__":
    main()
