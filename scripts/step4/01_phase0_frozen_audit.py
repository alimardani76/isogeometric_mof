#!/usr/bin/env python3
r"""Project 7B Step 4, Phase 0: read-only frozen-input audit.

Place the `Step 4 extension` and `Step 4 results` folders inside the 7B2 root,
then run from the 7B2 root:

    py ".\Step 4 extension\01_phase0_frozen_audit.py"

This script NEVER modifies Steps 1-3 or analysis/. It only inventories candidate
frozen inputs and writes hashes/schema/counts under Step 4 results/00_governance/.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "Step 4 results" / "00_governance"
OUT.mkdir(parents=True, exist_ok=True)

# Basenames are intentionally used because the frozen handoff may coexist with
# the original production tree. Phase 0 records every match and checks hashes.
SOURCES = [
    ("primary_pairs", "final_primary_pairs.parquet", True),
    ("pair_effects", "final_primary_pair_effect_magnitudes.parquet", True),
    ("group_effects", "corrected_group_effect_magnitudes.parquet", True),
    ("primary_pair_counts", "final_primary_pair_counts.csv", True),
    ("condition_scales", "adsorption_condition_scales.csv", True),
    ("primary_control_results", "step3_same_chemistry_control_results.csv", True),
    ("symmetric_control_results", "step5b_symmetric_control_results.csv", True),
    ("hoa_condition", "heat_adsorption_condition_results.csv", True),
    ("hoa_pressure", "heat_adsorption_pressure_results.csv", True),
    ("guest_specificity", "05_results.csv", True),
    ("residual_adjustment", "03_results.csv", True),
    ("balance", "04_balance.csv", True),
    ("family_exclusion", "04_family_exclusion_results.csv", True),
    ("family_exclusion_summary", "04_family_exclusion_summary.csv", True),
    ("reciprocal_matching", "reciprocal_covariance_matching_summary.csv", True),
    ("topology_robustness", "step1_topology_robustness_summary.csv", True),
    ("process_summary", "process_translation_summary_final.csv", True),
    ("process_pair_results", "process_translation_pair_results_final.parquet", False),
    ("case_set", "02_final_case_set.csv", True),
    ("case_frameworks", "02_final_case_frameworks.csv", True),
    ("case_pair_audit", "candidate_pair_audit.csv", True),
    ("case_adsorption", "candidate_adsorption_conditions.csv", True),
    ("case_process", "candidate_process_results.csv", True),
    ("charge_mapping_audit", "03_charge_mapping_audit.csv", True),
    ("atom_charge_rows", "03_atom_charge_rows.csv", True),
    ("framework_charge_summary", "03_framework_charge_summaries.csv", True),
    ("element_charge_summary", "03_element_charge_summaries.csv", True),
    ("pair_charge_contrasts", "03_pair_charge_contrasts.csv", True),
]

EXCLUDE_TOP = {"Step 4 extension", "Step 4 results"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def find_all(basename: str) -> list[Path]:
    out = []
    for p in ROOT.rglob(basename):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if rel.parts and rel.parts[0] in EXCLUDE_TOP:
            continue
        out.append(p)
    return sorted(out, key=lambda p: str(p).lower())


def inspect_table(path: Path):
    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            df = pd.read_csv(path, low_memory=False)
        elif suffix == ".parquet":
            df = pd.read_parquet(path)
        else:
            return None, None, None
        return int(len(df)), int(len(df.columns)), list(map(str, df.columns))
    except Exception as exc:
        return None, None, [f"READ_ERROR: {type(exc).__name__}: {exc}"]


def main():
    inventory = []
    object_summary = []

    for object_name, basename, required in SOURCES:
        matches = find_all(basename)
        hashes = {}
        for p in matches:
            digest = sha256(p)
            hashes.setdefault(digest, []).append(p)
            rows, ncols, columns = inspect_table(p)
            inventory.append({
                "object": object_name,
                "basename": basename,
                "required": required,
                "path": str(p.relative_to(ROOT)),
                "sha256": digest,
                "size_bytes": p.stat().st_size,
                "rows": rows,
                "columns_count": ncols,
                "columns": json.dumps(columns, ensure_ascii=False),
            })

        if not matches:
            status = "MISSING_REQUIRED" if required else "OPTIONAL_NOT_FOUND"
        elif len(hashes) == 1:
            status = "PASS_IDENTICAL_COPIES" if len(matches) > 1 else "PASS_UNIQUE"
        else:
            status = "CONFLICTING_COPIES"

        object_summary.append({
            "object": object_name,
            "basename": basename,
            "required": required,
            "matches": len(matches),
            "unique_hashes": len(hashes),
            "status": status,
        })

    inv = pd.DataFrame(inventory)
    summ = pd.DataFrame(object_summary)
    inv.to_csv(OUT / "phase0_frozen_input_inventory.csv", index=False)
    summ.to_csv(OUT / "phase0_object_status.csv", index=False)

    fatal = summ[summ.status.isin(["MISSING_REQUIRED", "CONFLICTING_COPIES"])]
    manifest = {
        "stage": "Project 7B Step 4 Phase 0 frozen-input audit",
        "created": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(ROOT),
        "objects_checked": int(len(summ)),
        "file_instances_hashed": int(len(inv)),
        "fatal_object_count": int(len(fatal)),
        "decision": "PASS" if fatal.empty else "STOP_AND_RESOLVE",
        "upstream_files_modified": False,
    }
    (OUT / "phase0_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    lines = [
        "PROJECT 7B STEP 4 - PHASE 0 FROZEN INPUT AUDIT",
        "=" * 72,
        f"Decision: {manifest['decision']}",
        f"Objects checked: {manifest['objects_checked']}",
        f"File instances hashed: {manifest['file_instances_hashed']}",
        f"Fatal objects: {manifest['fatal_object_count']}",
        "",
    ]
    if fatal.empty:
        lines += [
            "All mandatory basenames resolve to one scientific hash.",
            "Multiple identical copies are allowed and recorded.",
            "Proceed to Phase 1 only after reviewing the inventory paths.",
        ]
    else:
        lines += ["Resolve these objects before any Step 4 scientific analysis:"]
        for _, r in fatal.iterrows():
            lines.append(f"- {r['object']}: {r['status']} ({r['basename']})")
    report = "\n".join(lines)
    (OUT / "phase0_report.txt").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
