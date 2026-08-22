#!/usr/bin/env python3
"""
Project 7B Step 4 - Phase 2B1
REPEAT charge-to-CIF site mapping provenance audit.

Purpose
-------
The Phase 2B selected-case chemistry run showed low element-label agreement
between the newly parsed pymatgen site order and the frozen atom-charge rows.
This audit DOES NOT remap charges. It recovers the ORIGINAL mapping provenance
and profiles the frozen charge tables so that any later remapping reproduces
the established convention exactly rather than guessing.

READ ONLY with respect to Steps 1-3.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

TITLE = "PROJECT 7B STEP 4 - PHASE 2B1 CHARGE-SITE MAPPING PROVENANCE AUDIT"


def find_root(start: Path) -> Path:
    p = start.resolve()
    for cand in [p] + list(p.parents):
        if (cand / "Step 3 results").exists() and (cand / "Step 4 extension").exists():
            return cand
    raise RuntimeError("Could not locate Project 7B root.")


def norm_id(x) -> str:
    s = str(x).strip()
    if s.lower().endswith(".cif"):
        s = s[:-4]
    return s


def resolve_col(df: pd.DataFrame, candidates):
    lower = {str(c).lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    for actual in df.columns:
        al = str(actual).lower()
        for c in candidates:
            if c.lower() in al:
                return actual
    return None


def safe_read_csv(path: Path):
    return pd.read_csv(path, low_memory=False)


def source_hits(path: Path, terms: list[str]):
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return None
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines, start=1):
        low = line.lower()
        matched = [t for t in terms if t.lower() in low]
        if matched:
            hits.append((i, line.rstrip(), matched))
    return text, lines, hits


def excerpt(lines, hit_lines, radius=7):
    keep = set()
    for n in hit_lines:
        for j in range(max(1, n-radius), min(len(lines), n+radius)+1):
            keep.add(j)
    out = []
    prev = None
    for j in sorted(keep):
        if prev is not None and j > prev + 1:
            out.append("\n...\n")
        out.append(f"{j:5d}: {lines[j-1]}\n")
        prev = j
    return "".join(out)


def main():
    print(TITLE)
    print("=" * 72)

    root = find_root(Path.cwd())
    frozen = root / "Step 3 results" / "Paper7B_Hosein_to_Shayan_Frozen_Source_Package"
    out = root / "Step 4 results" / "02_cif_chemistry" / "phase2b1_charge_mapping_provenance"
    out.mkdir(parents=True, exist_ok=True)

    atom_path = frozen / "06_cif_chemistry" / "03_atom_charge_rows.csv"
    audit_path = frozen / "06_cif_chemistry" / "03_charge_mapping_audit.csv"
    case_fw_path = frozen / "08_structures" / "02_final_case_frameworks.csv"

    mandatory = [atom_path, audit_path, case_fw_path]
    missing = [p for p in mandatory if not p.exists()]
    if missing:
        for p in missing:
            print(f"FATAL: missing {p}")
        sys.exit(2)

    atom = safe_read_csv(atom_path)
    audit = safe_read_csv(audit_path)
    case_fw = safe_read_csv(case_fw_path)

    mof_case_col = resolve_col(case_fw, ["mof_id", "framework_id", "framework", "mof"])
    if mof_case_col is None:
        raise RuntimeError("Could not resolve selected framework ID column.")
    selected = {norm_id(v) for v in case_fw[mof_case_col].dropna().astype(str)}

    atom_mof_col = resolve_col(atom, ["mof_id", "framework_id", "framework", "mof"])
    audit_mof_col = resolve_col(audit, ["mof_id", "framework_id", "framework", "mof"])

    # Candidate field inventory
    field_groups = {
        "site_index": ["site_index", "atom_index", "site_idx", "atom_idx", "index"],
        "element": ["element", "symbol", "atom_symbol", "species", "type_symbol"],
        "label": ["site_label", "atom_label", "label"],
        "charge": ["charge", "repeat_charge", "partial_charge", "q"],
        "fract_x": ["fract_x", "frac_x", "fractional_x", "x"],
        "fract_y": ["fract_y", "frac_y", "fractional_y", "y"],
        "fract_z": ["fract_z", "frac_z", "fractional_z", "z"],
        "occupancy": ["occupancy", "occ"],
        "mapping_status": ["mapping_status", "status", "aligned", "alignment"],
        "mapping_method": ["mapping_method", "method", "mode"],
    }

    atom_resolved = {k: resolve_col(atom, v) for k, v in field_groups.items()}
    audit_resolved = {k: resolve_col(audit, v) for k, v in field_groups.items()}

    pd.DataFrame(
        [{"logical_field": k, "atom_table_column": atom_resolved[k], "audit_table_column": audit_resolved[k]}
         for k in field_groups]
    ).to_csv(out / "phase2b1_resolved_mapping_columns.csv", index=False)

    # Full schema profiles
    schema_rows = []
    for table_name, df in [("atom_charge_rows", atom), ("charge_mapping_audit", audit)]:
        for c in df.columns:
            s = df[c]
            schema_rows.append({
                "table": table_name,
                "column": str(c),
                "dtype": str(s.dtype),
                "nonnull": int(s.notna().sum()),
                "nunique": int(s.nunique(dropna=True)),
                "sample_values": json.dumps([str(v) for v in s.dropna().head(8).tolist()], ensure_ascii=False),
            })
    pd.DataFrame(schema_rows).to_csv(out / "phase2b1_charge_table_schema.csv", index=False)

    # Selected-framework row profiles
    prof_rows = []
    for mid in sorted(selected):
        rec = {"mof_id": mid}

        if atom_mof_col:
            a = atom[atom[atom_mof_col].astype(str).map(norm_id).eq(mid)].copy()
            rec["atom_rows"] = len(a)
            for logical in ["site_index", "element", "label", "charge", "fract_x", "fract_y", "fract_z", "occupancy"]:
                c = atom_resolved.get(logical)
                rec[f"atom_{logical}_column"] = c
                rec[f"atom_{logical}_nonnull"] = int(a[c].notna().sum()) if c else 0
                rec[f"atom_{logical}_nunique"] = int(a[c].nunique(dropna=True)) if c else 0
        else:
            rec["atom_rows"] = 0

        if audit_mof_col:
            q = audit[audit[audit_mof_col].astype(str).map(norm_id).eq(mid)].copy()
            rec["audit_rows"] = len(q)
            for logical in ["mapping_status", "mapping_method", "site_index", "element", "label"]:
                c = audit_resolved.get(logical)
                rec[f"audit_{logical}_column"] = c
                if c and not q.empty:
                    rec[f"audit_{logical}_values"] = json.dumps(
                        [str(v) for v in q[c].dropna().astype(str).unique()[:12]], ensure_ascii=False
                    )
        else:
            rec["audit_rows"] = 0

        prof_rows.append(rec)

    prof = pd.DataFrame(prof_rows)
    prof.to_csv(out / "phase2b1_selected_framework_mapping_profile.csv", index=False)

    # Save selected rows for manual inspection
    if atom_mof_col:
        atom_sel = atom[atom[atom_mof_col].astype(str).map(norm_id).isin(selected)].copy()
        atom_sel.to_csv(out / "phase2b1_selected_atom_charge_rows.csv", index=False)
    else:
        atom_sel = pd.DataFrame()

    if audit_mof_col:
        audit_sel = audit[audit[audit_mof_col].astype(str).map(norm_id).isin(selected)].copy()
        audit_sel.to_csv(out / "phase2b1_selected_charge_mapping_audit.csv", index=False)
    else:
        audit_sel = pd.DataFrame()

    # Recover original implementation from code, using exact output filenames and mapping terms.
    search_terms = [
        "03_atom_charge_rows.csv",
        "03_charge_mapping_audit.csv",
        "atom_charge_rows",
        "charge_mapping_audit",
        "repeat",
        "site_index",
        "atom_site",
        "fract_x",
        "fractional",
        "occupancy",
    ]

    code_rows = []
    candidates = []

    search_dirs = [
        root / "Step 1 computation",
        root / "Step 2 calculation",
        root / "Step 3 production",
        root / "Step 3 computation",
        root / "analysis",
    ]

    seen = set()
    for d in search_dirs:
        if not d.exists():
            continue
        for p in d.rglob("*.py"):
            if p in seen:
                continue
            seen.add(p)
            got = source_hits(p, search_terms)
            if got is None:
                continue
            text, lines, hits = got
            if not hits:
                continue

            exact_filename_hits = sum(
                1 for _, line, _ in hits
                if "03_atom_charge_rows.csv" in line or "03_charge_mapping_audit.csv" in line
            )
            score = exact_filename_hits * 100 + len(hits)
            candidates.append((score, p, lines, hits))

            for n, line, terms in hits:
                code_rows.append({
                    "path": str(p.relative_to(root)),
                    "line": n,
                    "matched_terms": ";".join(terms),
                    "source_line": line,
                    "score": score,
                })

    code_df = pd.DataFrame(code_rows)
    if not code_df.empty:
        code_df.sort_values(["score", "path", "line"], ascending=[False, True, True]).to_csv(
            out / "phase2b1_mapping_code_search_hits.csv", index=False
        )
    else:
        pd.DataFrame(columns=["path", "line", "matched_terms", "source_line", "score"]).to_csv(
            out / "phase2b1_mapping_code_search_hits.csv", index=False
        )

    candidates.sort(key=lambda x: (-x[0], str(x[1])))
    top = candidates[:5]
    candidate_summary = []
    for rank, (score, p, lines, hits) in enumerate(top, start=1):
        hit_lines = [n for n, _, _ in hits]
        candidate_summary.append({
            "rank": rank,
            "score": score,
            "path": str(p.relative_to(root)),
            "n_hits": len(hits),
            "exact_output_filename_hits": sum(
                1 for _, line, _ in hits
                if "03_atom_charge_rows.csv" in line or "03_charge_mapping_audit.csv" in line
            ),
        })
        (out / f"phase2b1_candidate_{rank}_source_excerpt.txt").write_text(
            excerpt(lines, hit_lines, radius=9),
            encoding="utf-8"
        )

    pd.DataFrame(candidate_summary).to_csv(out / "phase2b1_candidate_mapping_scripts.csv", index=False)

    # Decision logic: do not claim a mapping method until provenance says so.
    fatal = []
    warnings = []

    if atom_mof_col is None:
        fatal.append("Could not resolve framework ID in atom-charge table.")
    if audit_mof_col is None:
        warnings.append("Could not resolve framework ID in charge-mapping audit table.")
    if not candidates:
        fatal.append("Could not locate any original Python implementation related to charge mapping.")
    if atom_resolved["charge"] is None:
        fatal.append("Could not resolve charge column in atom-charge table.")

    # This is deliberately NOT a failure: low new-script element agreement is the reason for this audit.
    has_coords = all(atom_resolved[k] is not None for k in ["fract_x", "fract_y", "fract_z"])
    has_index = atom_resolved["site_index"] is not None
    has_label = atom_resolved["label"] is not None
    has_element = atom_resolved["element"] is not None

    decision = "PASS" if not fatal else "FAIL"

    summary = {
        "decision": decision,
        "selected_frameworks": len(selected),
        "selected_atom_rows": int(len(atom_sel)),
        "selected_audit_rows": int(len(audit_sel)),
        "atom_table_columns": [str(c) for c in atom.columns],
        "audit_table_columns": [str(c) for c in audit.columns],
        "resolved_atom_fields": atom_resolved,
        "resolved_audit_fields": audit_resolved,
        "has_fractional_coordinates_in_atom_table": has_coords,
        "has_site_index_in_atom_table": has_index,
        "has_site_label_in_atom_table": has_label,
        "has_element_in_atom_table": has_element,
        "candidate_mapping_scripts_found": len(candidates),
        "fatal": fatal,
        "warnings": warnings,
        "next_step": (
            "RECOVER_EXACT_MAPPING_FROM_TOP_CANDIDATE_BEFORE_SITE_LEVEL_CHARGE_USE"
            if decision == "PASS"
            else "STOP"
        ),
    }
    (out / "phase2b1_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Decision: {decision}")
    print(f"Selected frameworks profiled: {len(selected)}")
    print(f"Selected atom-charge rows: {len(atom_sel)}")
    print(f"Selected mapping-audit rows: {len(audit_sel)}")
    print(f"Candidate original mapping scripts found: {len(candidates)}")

    print("\nFrozen atom-charge table resolved fields:")
    for k in ["site_index", "element", "label", "charge", "fract_x", "fract_y", "fract_z", "occupancy"]:
        print(f"  {k}: {atom_resolved.get(k)}")

    print("\nFrozen charge-mapping audit resolved fields:")
    for k in ["mapping_status", "mapping_method", "site_index", "element", "label"]:
        print(f"  {k}: {audit_resolved.get(k)}")

    if candidate_summary:
        print("\nTop candidate original mapping implementations:")
        for r in candidate_summary[:5]:
            print(f"  {r['rank']}. {r['path']} | score={r['score']} | hits={r['n_hits']}")

    if not audit_sel.empty:
        print("\nSelected-framework mapping audit columns:")
        print("  " + ", ".join(str(c) for c in audit_sel.columns))

    for w in warnings:
        print(f"WARN: {w}")
    for f in fatal:
        print(f"FATAL: {f}")

    print(
        "No charge was remapped, no local-charge contrast was interpreted, and no "
        "adsorption/matching/process result was recomputed."
    )
    print(f"Outputs: {out}")

    if decision != "PASS":
        sys.exit(2)


if __name__ == "__main__":
    main()
