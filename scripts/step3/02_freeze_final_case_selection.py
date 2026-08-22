#!/usr/bin/env python3
"""
Project 7B2 Step 3, file 02: freeze the six final structure cases.

Place inside:
    Step 3 production/

Run from project root:
    python "Step 3 production/02_freeze_final_case_selection.py"

This script freezes the six role-leading, renderable, non-overlapping cases
recommended by 01_prepare_final_case_selection.py. It does not rerank pairs,
change scientific values, assign chemical direction, or add mechanism claims.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

STEP3 = Path(__file__).resolve().parent
ROOT = STEP3.parent
IN_DIR = ROOT / "Step 3 results" / "case_selection"
OUT = IN_DIR
RECOMMENDED = IN_DIR / "01_recommended_review_set.csv"

EXPECTED_ROLES = [
    "strong_linker_process_aligned",
    "strong_metal_process_aligned",
    "cu_zn_pressure_exception",
    "near_null_comparison",
    "process_discordant_comparison",
    "functional_motif_example",
]

EXPECTED_PAIRS = {
    "strong_linker_process_aligned": "DB0-m3_o11_o17_f0_pcu.sym.32 || DB0-m3_o12_o20_f0_pcu.sym.24",
    "strong_metal_process_aligned": "DB0-m2_o7_o7_f0_nbo.sym.45 || DB0-m3_o7_o7_f0_nbo.sym.48",
    "cu_zn_pressure_exception": "DB0-m2_o6_o27_f0_nbo.sym.30 || DB0-m3_o6_o27_f0_nbo.sym.33",
    "near_null_comparison": "DB0-m2_o23_o28_f0_nbo.sym.21 || DB0-m2_o23_o28_f0_nbo.sym.4",
    "process_discordant_comparison": "DB0-m3_o152_o155_f0_fsc.sym.27 || DB0-m3_o440_o155_f0_fsc.sym.26",
    "functional_motif_example": "DB0-m9_o17_o27_f0_sra.sym.116 || DB0-m9_o17_o27_f0_sra.sym.117",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    if not RECOMMENDED.exists():
        raise FileNotFoundError(RECOMMENDED)
    df = pd.read_csv(RECOMMENDED)
    if len(df) != 6:
        raise RuntimeError(f"Expected six recommended roles, found {len(df)}")
    if set(df["selection_category"]) != set(EXPECTED_ROLES):
        raise RuntimeError("Recommended role set differs from the frozen six-role design")
    if not df["renderable"].astype(str).str.lower().isin(["true", "1"]).all():
        raise RuntimeError("At least one recommended case is not renderable")
    if df["pair_key"].duplicated().any():
        raise RuntimeError("Duplicate recommended pair")
    frameworks = pd.concat([df["id_a"], df["id_b"]], ignore_index=True)
    if frameworks.duplicated().any():
        raise RuntimeError("Framework reuse remains in recommended set")
    for role, expected in EXPECTED_PAIRS.items():
        observed = df.loc[df["selection_category"].eq(role), "pair_key"].iloc[0]
        if observed != expected:
            raise RuntimeError(f"Recommended pair changed for {role}: {observed}")

    df["final_case_decision"] = "KEEP"
    df["final_case_status"] = "FROZEN_FOR_PRODUCTION"
    df["selection_basis"] = (
        "Frozen role rank 1; renderable; no pair or framework reuse; retained for a distinct scientific role."
    )
    df["mechanism_claim_authorized"] = False
    df["directional_substitution_claim_authorized"] = False
    df.to_csv(OUT / "02_final_case_set.csv", index=False)

    framework_rows = []
    for _, row in df.iterrows():
        for side in ["a", "b"]:
            framework_rows.append({
                "framework_id": row[f"id_{side}"],
                "endpoint": side,
                "pair_key": row["pair_key"],
                "selection_category": row["selection_category"],
                "intervention": row["intervention"],
                "transition": row["transition"],
            })
    pd.DataFrame(framework_rows).to_csv(OUT / "02_final_case_frameworks.csv", index=False)

    report = [
        "PROJECT 7B2 FINAL STRUCTURE CASE SET", "=" * 72,
        "Decision: SIX CASES FROZEN FOR PRODUCTION", "",
    ]
    for role in EXPECTED_ROLES:
        row = df.loc[df["selection_category"].eq(role)].iloc[0]
        report.append(
            f"- {row['role_label']}: {row['pair_key']} | {row['transition']} | "
            f"median |Delta log q|={row['median_absolute_log_difference']:.6g}"
        )
    report.extend([
        "",
        "Boundaries:",
        "- cases communicate strong, null, exceptional, discordant, and exploratory outcomes",
        "- no case establishes a general mechanism or directional substitution rule",
        "- the functional-motif case remains illustrative because class support is insufficient",
        "- later visual inspection may change panel orientation or camera, not pair membership",
    ])
    (OUT / "02_report.txt").write_text("\n".join(report), encoding="utf-8", newline="\n")

    manifest = {
        "stage": "Project 7B2 final structure-case freeze",
        "created": datetime.now().isoformat(timespec="seconds"),
        "script": "02_freeze_final_case_selection.py",
        "input": {"path": str(RECOMMENDED), "sha256": sha256(RECOMMENDED)},
        "final_pairs": EXPECTED_PAIRS,
        "case_count": 6,
        "framework_count": 12,
        "pair_membership_changed": False,
        "scientific_values_changed": False,
        "mechanism_claim_authorized": False,
        "directional_chemistry_assigned": False,
        "outputs": ["02_final_case_set.csv", "02_final_case_frameworks.csv", "02_report.txt"],
        "python": sys.version,
        "pandas": pd.__version__,
    }
    (OUT / "02_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
    print("\n".join(report))
    print(f"\nOutputs: {OUT}")

if __name__ == "__main__":
    main()
