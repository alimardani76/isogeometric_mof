#!/usr/bin/env python3
"""
Project 7B2 Step 3, file 04: build figure-source package.

Place inside:
    Step 3 production/

Run from project root:
    python "Step 3 production/04_build_figure_source_package.py"

Purpose
-------
Create a figure-specific, provenance-preserving source-data package for the
six frozen main-figure messages. This script performs no new scientific
estimation. It copies small final tables and filters existing case-level tables
to the six frozen pair keys. Missing required sources stop the run; optional
sources are reported explicitly.

Outputs
-------
    Step 3 results/figure_source_data/
        Figure_01/ ... Figure_06/
        04_source_registry.csv
        04_missing_optional_sources.csv
        04_report.txt
        04_manifest.json
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

STEP3 = Path(__file__).resolve().parent
ROOT = STEP3.parent
OUT = ROOT / "Step 3 results" / "figure_source_data"
OUT.mkdir(parents=True, exist_ok=True)

CASES = ROOT / "Step 3 results" / "case_selection" / "02_final_case_set.csv"

# Each entry: (figure, basename, required, purpose).
# Basenames are resolved uniquely below the active project root. Archive and
# generated source-package directories are excluded.
SOURCES = [
    (1, "final_primary_pair_counts.csv", True, "Frozen primary pair counts by intervention"),
    (1, "caliper_sensitivity_support.csv", True, "Support across fixed geometry tiers"),
    (1, "corrected_effect_run_summary.csv", True, "Frozen adsorption integration summary"),
    (1, "inspection_manifest.json", True, "CIF and selected-case inspection provenance"),

    (2, "step3_same_chemistry_control_results.csv", True, "Primary same-chemistry controls"),
    (2, "step5b_symmetric_control_results.csv", True, "Symmetric same-chemistry controls"),
    (2, "heat_adsorption_condition_results.csv", True, "Condition-level energetic association"),
    (2, "03_results.csv", True, "Residual-geometry-adjusted linker sensitivity"),

    (3, "heat_adsorption_pressure_results.csv", True, "Pressure change in energetic and adsorption contrasts"),
    (3, "05_results.csv", True, "Paired guest-specificity results"),
    (3, "05_summary.csv", True, "Guest-specificity summary"),

    (4, "reciprocal_covariance_matching_summary.csv", True, "Reciprocal matching robustness"),
    (4, "step1_topology_robustness_summary.csv", True, "Topology-confidence robustness"),
    (4, "step2_residual_geometry_summary.csv", True, "Residual-geometry associations"),
    (4, "04_balance.csv", True, "Measured-geometry arm balance diagnostic"),
    (4, "04_family_exclusion_results.csv", True, "Largest-family exclusion estimates"),
    (4, "04_family_exclusion_summary.csv", True, "Family-dominance summary"),

    (5, "02_final_case_set.csv", True, "Frozen six-case definitions"),
    (5, "02_final_case_frameworks.csv", True, "Twelve selected framework endpoints"),
    (5, "03_framework_charge_summaries.csv", True, "Selected-case framework charge summaries"),
    (5, "03_element_charge_summaries.csv", True, "Selected-case element charge summaries"),
    (5, "03_pair_charge_contrasts.csv", True, "Selected-case pair charge audit"),
    (5, "candidate_adsorption_conditions.csv", True, "Condition-level adsorption results for shortlisted cases"),
    (5, "candidate_process_results.csv", True, "Process results for shortlisted cases"),
    (5, "candidate_pair_audit.csv", True, "Geometry and chemistry audit for shortlisted cases"),

    (6, "process_translation_summary_final.csv", True, "Class-level process translation"),
    (6, "candidate_process_results.csv", True, "Selected-case process consequences"),
    (6, "02_final_case_set.csv", True, "Case role and process-alignment labels"),
]

EXCLUDE_PARTS = {
    "archive", "full_pair_rules_work", "full_pair_rules", "pair_rules_work",
    "temp", "tmp", "cache", "figure_source_data"
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def active_matches(basename: str) -> list[Path]:
    out = []
    for p in ROOT.rglob(basename):
        rel_parts = {part.lower() for part in p.relative_to(ROOT).parts}
        if rel_parts & EXCLUDE_PARTS:
            continue
        if p.is_file():
            out.append(p)
    return sorted(out)


def resolve_unique(basename: str) -> Path | None:
    matches = active_matches(basename)
    if not matches:
        return None
    # Prefer Step 2/Step 3 outputs over duplicate project-root uploads; then
    # prefer analysis. Equal-priority duplicates with different hashes stop.
    def priority(p: Path):
        s = str(p.relative_to(ROOT)).lower()
        if "step 3 results" in s: return 0
        if "step 2 results" in s: return 1
        if "analysis" in s: return 2
        return 3
    matches.sort(key=lambda p: (priority(p), len(p.parts), str(p)))
    best_priority = priority(matches[0])
    peers = [p for p in matches if priority(p) == best_priority]
    if len(peers) > 1:
        hashes = {sha256(p) for p in peers}
        if len(hashes) > 1:
            raise RuntimeError(
                f"Ambiguous active sources for {basename}: " + ", ".join(map(str, peers))
            )
    return peers[0]


def safe_name(basename: str) -> str:
    return "04_" + basename


def pair_key_series(df: pd.DataFrame) -> pd.Series:
    if "pair_key" in df.columns:
        return df["pair_key"].astype(str)
    for a, b in [("id_a", "id_b"), ("pair_lo", "pair_hi")]:
        if a in df.columns and b in df.columns:
            x = df[a].astype(str); y = df[b].astype(str)
            return x.where(x <= y, y) + " || " + y.where(x <= y, x)
    raise KeyError("No pair_key or endpoint columns found")


def filter_case_csv(source: Path, case_keys: set[str], destination: Path) -> tuple[int, int]:
    df = pd.read_csv(source, low_memory=False)
    keys = pair_key_series(df)
    selected = df.loc[keys.isin(case_keys)].copy()
    selected.insert(0, "frozen_case_pair_key", keys.loc[selected.index].to_numpy())
    selected.to_csv(destination, index=False)
    return len(df), len(selected)


def main():
    if not CASES.exists():
        raise FileNotFoundError(CASES)
    cases = pd.read_csv(CASES)
    if len(cases) != 6 or cases["pair_key"].nunique() != 6:
        raise RuntimeError("The frozen final case set must contain six unique pair keys")
    case_keys = set(cases["pair_key"].astype(str))

    registry = []
    missing_optional = []
    copied_lookup = {}

    # Resolve all basenames once so repeated sources are copied independently
    # into each figure folder but retain one authoritative upstream path.
    resolved = {}
    for _, basename, required, purpose in SOURCES:
        if basename not in resolved:
            resolved[basename] = resolve_unique(basename)
        if resolved[basename] is None and required:
            raise FileNotFoundError(f"Required figure source not found: {basename} ({purpose})")

    for fig, basename, required, purpose in SOURCES:
        source = resolved[basename]
        fig_dir = OUT / f"Figure_{fig:02d}"
        fig_dir.mkdir(parents=True, exist_ok=True)
        if source is None:
            missing_optional.append({
                "figure": fig, "basename": basename, "purpose": purpose,
                "status": "MISSING_OPTIONAL"
            })
            continue

        destination = fig_dir / safe_name(basename)
        rows_source = rows_written = None
        filtered = False

        # Figure 5 and Figure 6 case-level candidate tables are filtered to the
        # six frozen pairs. Other summary tables are copied exactly.
        if basename in {
            "candidate_adsorption_conditions.csv",
            "candidate_process_results.csv",
            "candidate_pair_audit.csv",
        }:
            rows_source, rows_written = filter_case_csv(source, case_keys, destination)
            filtered = True
        else:
            shutil.copy2(source, destination)
            if source.suffix.lower() == ".csv":
                try:
                    rows_source = len(pd.read_csv(source, low_memory=False))
                    rows_written = rows_source
                except Exception:
                    pass

        registry.append({
            "figure": fig,
            "purpose": purpose,
            "source_basename": basename,
            "upstream_path": str(source),
            "upstream_sha256": sha256(source),
            "packaged_path": str(destination),
            "packaged_sha256": sha256(destination),
            "filtered_to_six_cases": filtered,
            "source_rows": rows_source,
            "packaged_rows": rows_written,
            "status": "PACKAGED",
        })
        copied_lookup[(fig, basename)] = destination

    registry_df = pd.DataFrame(registry).sort_values(["figure", "source_basename"])
    registry_df.to_csv(OUT / "04_source_registry.csv", index=False)
    pd.DataFrame(missing_optional).to_csv(OUT / "04_missing_optional_sources.csv", index=False)

    # Index file is deliberately plain and updateable. It records one question
    # per figure rather than prescribing visual aesthetics prematurely.
    figure_index = pd.DataFrame([
        [1, "How were chemistry-changing natural experiments constructed under measured structural control?", "Cohort, tiers, intervention support, CIF provenance"],
        [2, "Do chemistry-changing pairs exceed matched same-chemistry background variation?", "Primary/symmetric controls, heat association, adjusted linker sensitivity"],
        [3, "How do guest identity and pressure alter energetic and adsorption sensitivity to chemistry?", "Heat-pressure relationships, paired CO2/co-guest comparisons, high-pressure CO2/H2 boundary"],
        [4, "Which results survive alternative matching, topology, residual-geometry, balance, and family-dominance checks?", "Reciprocal, topology, residual geometry, SMD, family exclusion"],
        [5, "What do strong, null, exceptional, discordant, and exploratory matched cases look like chemically?", "Six structures, adsorption, heat, process, charge fingerprints"],
        [6, "When do adsorption differences persist into working capacity and selectivity?", "Class-level process translation and selected discordant cases"],
    ], columns=["figure", "scientific_question", "source_content"])
    figure_index.to_csv(OUT / "04_figure_index.csv", index=False)

    counts = registry_df.groupby("figure").size().to_dict()
    report = [
        "PROJECT 7B2 FIGURE-SOURCE PACKAGE", "=" * 72,
        "Decision: SOURCE DATA PACKAGED FOR FIGURES 1-6", "",
    ]
    for fig in range(1, 7):
        report.append(f"Figure {fig}: {counts.get(fig, 0)} source table(s) packaged")
    report.extend([
        "",
        f"Frozen cases represented: {len(case_keys)}",
        f"Missing optional sources: {len(missing_optional)}",
        "",
        "Boundaries:",
        "- no scientific estimate was recalculated",
        "- case-level candidate tables were filtered only by frozen pair_key",
        "- all other tables were copied byte-for-byte",
        "- every packaged file retains its upstream path and SHA-256 hash",
        "",
        "Next action:",
        "Use 04_figure_index.csv and the six figure folders to design and render Figures 1-6.",
    ])
    (OUT / "04_report.txt").write_text("\n".join(report), encoding="utf-8", newline="\n")

    manifest = {
        "stage": "Project 7B2 consolidated figure-source packaging",
        "created": datetime.now().isoformat(timespec="seconds"),
        "script": "04_build_figure_source_package.py",
        "frozen_case_input": {"path": str(CASES), "sha256": sha256(CASES)},
        "figure_count": 6,
        "packaged_source_count": len(registry_df),
        "missing_optional_count": len(missing_optional),
        "new_scientific_analysis": False,
        "scientific_values_changed": False,
        "case_filter": "exact frozen pair_key only",
        "outputs": [
            "04_source_registry.csv", "04_missing_optional_sources.csv",
            "04_figure_index.csv", "04_report.txt", "Figure_01/ ... Figure_06/"
        ],
        "python": sys.version,
        "pandas": pd.__version__,
    }
    (OUT / "04_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8", newline="\n"
    )
    print("\n".join(report))
    print(f"\nOutputs: {OUT}")


if __name__ == "__main__":
    main()
