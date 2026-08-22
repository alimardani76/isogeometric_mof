#!/usr/bin/env python3
"""
Project 7B2 Step 3, file 01: prepare final structure-case selection.

Place inside:
    Step 3 production/

Run from project root:
    python "Step 3 production/01_prepare_final_case_selection.py"

Purpose
-------
Build a compact, auditable human-review package for selecting one final case
from each of the six frozen scientific roles. The script does not change pair
membership, rerank from adsorption outcomes, assign chemistry direction, or
make final decisions automatically.

Inputs
------
The script locates exactly one final_case_review_sheet.csv and optionally reads:
    Step 2 results/heat_analysis/matched_heat_group_data.parquet
    Step 2 results/guest_specificity/05_results.csv

Outputs
-------
    Step 3 results/case_selection/
        01_role_candidates.csv
        01_recommended_review_set.csv
        01_framework_reuse_audit.csv
        01_report.txt
        01_manifest.json

Selection logic
---------------
- Preserve the frozen role-specific ranking.
- Require renderable=True.
- Recommend the highest-ranked candidate in each role that does not reuse a
  pair or framework already recommended for another role.
- Retain up to two role-specific alternates.
- Leave final_case_decision as REVIEW. Human review remains mandatory.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

STEP3 = Path(__file__).resolve().parent
ROOT = STEP3.parent
OUT = ROOT / "Step 3 results" / "case_selection"
OUT.mkdir(parents=True, exist_ok=True)

HEAT = ROOT / "Step 2 results" / "heat_analysis" / "matched_heat_group_data.parquet"
GUEST = ROOT / "Step 2 results" / "guest_specificity" / "05_results.csv"

ROLE_ORDER = [
    "strong_linker_process_aligned",
    "strong_metal_process_aligned",
    "cu_zn_pressure_exception",
    "near_null_comparison",
    "process_discordant_comparison",
    "functional_motif_example",
]

ROLE_LABELS = {
    "strong_linker_process_aligned": "Strong linker / process aligned",
    "strong_metal_process_aligned": "Strong metal / process aligned",
    "cu_zn_pressure_exception": "Cu-Zn pressure exception",
    "near_null_comparison": "Near-null comparison",
    "process_discordant_comparison": "Process-discordant comparison",
    "functional_motif_example": "Functional-motif example",
}

REQUIRED = {
    "selection_category", "case_rank", "pair_key", "intervention", "transition",
    "id_a", "id_b", "renderable", "median_absolute_log_difference",
    "mean_wc_concordance", "mean_selectivity_concordance", "final_case_decision"
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def locate_review_sheet() -> Path:
    matches = []
    for p in ROOT.rglob("final_case_review_sheet.csv"):
        low_parts = {x.lower() for x in p.parts}
        if "archive" in low_parts:
            continue
        matches.append(p)
    if len(matches) != 1:
        raise RuntimeError(
            "Expected exactly one active final_case_review_sheet.csv; found: "
            + ", ".join(map(str, matches))
        )
    return matches[0]


def parse_bool(x) -> bool:
    if isinstance(x, bool):
        return x
    return str(x).strip().lower() in {"true", "1", "yes", "y"}


def add_heat_summary(cases: pd.DataFrame) -> pd.DataFrame:
    if not HEAT.exists():
        cases["heat_data_available"] = False
        return cases

    heat = pd.read_parquet(HEAT)
    required = {
        "intervention", "dependence_family_id", "target", "T/K", "p/bar",
        "absolute_hoa_difference", "absolute_log_difference"
    }
    if not required.issubset(heat.columns):
        cases["heat_data_available"] = False
        return cases

    # Case sheets do not necessarily contain dependence-family IDs. Therefore
    # no family-level heat value is assigned unless an exact pair-level bridge
    # exists. We record availability without inventing a join.
    cases["heat_data_available"] = True
    cases["case_heat_summary_status"] = "PENDING_EXACT_PAIR_TO_GROUP_BRIDGE"
    return cases


def add_guest_context(cases: pd.DataFrame) -> pd.DataFrame:
    if not GUEST.exists():
        cases["guest_specificity_context_available"] = False
        return cases
    guest = pd.read_csv(GUEST)
    cases["guest_specificity_context_available"] = not guest.empty
    cases["guest_specificity_context_note"] = (
        "Class-level paired-process result only; not assigned to an individual case."
    )
    return cases


def recommend(cases: pd.DataFrame):
    used_pairs = set()
    used_frameworks = set()
    selected_rows = []
    candidate_rows = []

    for role in ROLE_ORDER:
        role_df = cases.loc[
            cases["selection_category"].eq(role) & cases["renderable_bool"]
        ].sort_values(["case_rank", "pair_key"], kind="stable").copy()

        chosen_index = None
        reason = None
        for idx, row in role_df.iterrows():
            pair = str(row["pair_key"])
            frameworks = {str(row["id_a"]), str(row["id_b"])}
            if pair in used_pairs:
                continue
            if frameworks & used_frameworks:
                continue
            chosen_index = idx
            reason = "highest frozen role rank without pair or framework reuse"
            break

        if chosen_index is None and not role_df.empty:
            # Do not silently drop a role. Recommend its highest-ranked case and
            # flag the reuse conflict for human decision.
            chosen_index = role_df.index[0]
            row = role_df.loc[chosen_index]
            pair = str(row["pair_key"])
            frameworks = {str(row["id_a"]), str(row["id_b"])}
            conflicts = []
            if pair in used_pairs:
                conflicts.append("pair reuse")
            if frameworks & used_frameworks:
                conflicts.append("framework reuse")
            reason = "highest frozen role rank; human review required because of " + ", ".join(conflicts)

        if chosen_index is None:
            selected_rows.append({
                "selection_category": role,
                "role_label": ROLE_LABELS[role],
                "recommendation_status": "NO_RENDERABLE_CANDIDATE",
                "recommendation_reason": "No renderable frozen candidate",
                "final_case_decision": "REVIEW",
            })
            continue

        chosen = role_df.loc[chosen_index].copy()
        pair = str(chosen["pair_key"])
        frameworks = {str(chosen["id_a"]), str(chosen["id_b"])}
        reused_pair = pair in used_pairs
        reused_frameworks = sorted(frameworks & used_frameworks)

        chosen["role_label"] = ROLE_LABELS[role]
        chosen["recommendation_status"] = "RECOMMENDED_FOR_HUMAN_REVIEW"
        chosen["recommendation_reason"] = reason
        chosen["pair_reuse_conflict"] = reused_pair
        chosen["framework_reuse_conflict"] = bool(reused_frameworks)
        chosen["reused_framework_ids"] = ";".join(reused_frameworks)
        chosen["final_case_decision"] = "REVIEW"
        selected_rows.append(chosen.to_dict())

        used_pairs.add(pair)
        used_frameworks.update(frameworks)

        # Produce a compact role package: recommended case plus up to two
        # frozen-rank alternates. No new score is created.
        ordered = pd.concat([
            role_df.loc[[chosen_index]],
            role_df.drop(index=chosen_index)
        ]).head(3)
        for review_order, (_, row) in enumerate(ordered.iterrows(), 1):
            rec = row.to_dict()
            rec["role_label"] = ROLE_LABELS[role]
            rec["review_order"] = review_order
            rec["candidate_status"] = "RECOMMENDED" if review_order == 1 else "ALTERNATE"
            rec["pair_used_elsewhere"] = str(row["pair_key"]) in (used_pairs - {pair})
            rec["framework_used_elsewhere"] = bool(
                {str(row["id_a"]), str(row["id_b"])} & (used_frameworks - frameworks)
            )
            rec["final_case_decision"] = "REVIEW"
            candidate_rows.append(rec)

    return pd.DataFrame(selected_rows), pd.DataFrame(candidate_rows)


def framework_audit(recommended: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in recommended.iterrows():
        if row.get("recommendation_status") != "RECOMMENDED_FOR_HUMAN_REVIEW":
            continue
        for side in ["a", "b"]:
            rows.append({
                "framework_id": row[f"id_{side}"],
                "pair_key": row["pair_key"],
                "selection_category": row["selection_category"],
                "role_label": row["role_label"],
                "endpoint": side,
            })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    counts = out.groupby("framework_id")["pair_key"].nunique().rename("recommended_pair_count")
    out = out.merge(counts, on="framework_id", how="left", validate="many_to_one")
    out["framework_reused"] = out["recommended_pair_count"] > 1
    return out.sort_values(["framework_reused", "framework_id"], ascending=[False, True])


def main():
    review_path = locate_review_sheet()
    cases = pd.read_csv(review_path)
    missing = REQUIRED - set(cases.columns)
    if missing:
        raise RuntimeError(f"Review sheet missing columns: {sorted(missing)}")

    cases["renderable_bool"] = cases["renderable"].map(parse_bool)
    unknown_roles = sorted(set(cases["selection_category"].dropna()) - set(ROLE_ORDER))
    missing_roles = sorted(set(ROLE_ORDER) - set(cases["selection_category"].dropna()))
    if unknown_roles or missing_roles:
        raise RuntimeError(f"Role mismatch. Unknown={unknown_roles}; missing={missing_roles}")

    cases = add_heat_summary(cases)
    cases = add_guest_context(cases)

    recommended, role_candidates = recommend(cases)
    reuse = framework_audit(recommended)

    # Stable column order for human review.
    front = [
        "selection_category", "role_label", "recommendation_status",
        "recommendation_reason", "case_rank", "pair_key", "intervention",
        "transition", "id_a", "id_b", "formula_contrast", "metal_contrast",
        "renderable", "median_absolute_log_difference", "mean_wc_concordance",
        "mean_selectivity_concordance", "pair_reuse_conflict",
        "framework_reuse_conflict", "reused_framework_ids",
        "production_note", "final_case_decision"
    ]
    for c in front:
        if c not in recommended.columns:
            recommended[c] = np.nan
    recommended = recommended[front + [c for c in recommended.columns if c not in front]]

    candidate_front = [
        "selection_category", "role_label", "review_order", "candidate_status",
        "case_rank", "pair_key", "intervention", "transition", "id_a", "id_b",
        "formula_contrast", "metal_contrast", "renderable",
        "median_absolute_log_difference", "mean_wc_concordance",
        "mean_selectivity_concordance", "pair_used_elsewhere",
        "framework_used_elsewhere", "production_note", "final_case_decision"
    ]
    for c in candidate_front:
        if c not in role_candidates.columns:
            role_candidates[c] = np.nan
    role_candidates = role_candidates[candidate_front + [c for c in role_candidates.columns if c not in candidate_front]]

    recommended.to_csv(OUT / "01_recommended_review_set.csv", index=False)
    role_candidates.to_csv(OUT / "01_role_candidates.csv", index=False)
    reuse.to_csv(OUT / "01_framework_reuse_audit.csv", index=False)

    n_recommended = int((recommended["recommendation_status"] == "RECOMMENDED_FOR_HUMAN_REVIEW").sum())
    pair_conflicts = int(recommended["pair_reuse_conflict"].fillna(False).sum())
    framework_conflicts = int(recommended["framework_reuse_conflict"].fillna(False).sum())

    report = [
        "PROJECT 7B2 STEP 3 CASE-SELECTION PREPARATION",
        "=" * 72,
        f"Frozen review sheet: {review_path}",
        f"Frozen candidates: {len(cases)}",
        f"Scientific roles: {len(ROLE_ORDER)}",
        f"Recommended for human review: {n_recommended}",
        f"Pair-reuse conflicts: {pair_conflicts}",
        f"Framework-reuse conflicts: {framework_conflicts}",
        "",
        "RECOMMENDED REVIEW SET",
    ]
    for _, row in recommended.iterrows():
        report.append(
            f"- {row['role_label']}: rank {row.get('case_rank', np.nan)} | "
            f"{row.get('pair_key', '')} | {row.get('transition', '')} | "
            f"median |Delta log q|={row.get('median_absolute_log_difference', np.nan):.6g}"
        )
    report.extend([
        "",
        "Interpretation boundary:",
        "  Recommendations preserve the frozen role ranking.",
        "  No case is final until final_case_decision is changed manually.",
        "  No charge, mechanism, or directional substitution interpretation was added.",
        "  Case-level heat values were not joined without an exact pair-to-group bridge.",
        "",
        "Next action:",
        "  Review 01_recommended_review_set.csv and mark KEEP or REPLACE.",
        "  Use 01_role_candidates.csv only when replacing a recommended case.",
    ])
    (OUT / "01_report.txt").write_text("\n".join(report), encoding="utf-8", newline="\n")

    manifest = {
        "stage": "Project 7B2 Step 3 case-selection preparation",
        "created": datetime.now().isoformat(timespec="seconds"),
        "script": "01_prepare_final_case_selection.py",
        "input": {"path": str(review_path), "sha256": sha256(review_path)},
        "optional_inputs": {
            "heat_group_data": {"path": str(HEAT), "exists": HEAT.exists(), "sha256": sha256(HEAT) if HEAT.exists() else None},
            "guest_results": {"path": str(GUEST), "exists": GUEST.exists(), "sha256": sha256(GUEST) if GUEST.exists() else None},
        },
        "selection_roles": ROLE_ORDER,
        "automatic_final_selection": False,
        "pair_membership_changed": False,
        "scientific_values_changed": False,
        "directional_chemistry_assigned": False,
        "outputs": [
            "01_recommended_review_set.csv",
            "01_role_candidates.csv",
            "01_framework_reuse_audit.csv",
            "01_report.txt",
        ],
        "python": sys.version,
        "pandas": pd.__version__,
    }
    (OUT / "01_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")

    print("\n".join(report))
    print(f"\nOutputs: {OUT}")


if __name__ == "__main__":
    main()
