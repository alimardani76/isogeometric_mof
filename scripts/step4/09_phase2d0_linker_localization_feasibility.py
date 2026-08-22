#!/usr/bin/env python3
"""
Project 7B Step 4 - Phase 2D0
Linker-localization feasibility audit.

Purpose
-------
Phase 2C showed that the strong linker case has a substantially larger descriptive
electrostatic separation than the near-null linker case. Before attributing that
difference to the changed linker, this audit asks a narrower provenance question:

Does Project 7B already contain an explicit framework->linker / ligand / fragment /
building-block / atom-mapping object that can identify the changed linker atoms in
the six FROZEN structure cases?

This script does NOT assign linker atoms, does NOT compare adsorption outcomes,
and does NOT create a mechanism. It inventories existing candidate objects and
extracts selected-case rows when possible.

READ ONLY with respect to Steps 1-3.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

TITLE = "PROJECT 7B STEP 4 - PHASE 2D0 LINKER-LOCALIZATION FEASIBILITY AUDIT"

FILE_TERMS = [
    "linker", "ligand", "fragment", "building", "block", "sbu",
    "smiles", "graph", "rac", "chemistry", "atom", "mapping",
    "motif", "organic", "node", "structure", "pair"
]

STRONG_TERMS = [
    "linker", "ligand", "fragment", "building_block", "building block",
    "smiles", "atom_map", "atom mapping", "linker_id", "ligand_id"
]

COLUMN_TERMS = [
    "linker", "ligand", "fragment", "building", "block", "sbu",
    "smiles", "graph", "rac", "atom", "mapping", "motif",
    "element", "mof", "framework", "pair"
]

SKIP_DIR_PARTS = {
    ".git", "__pycache__", ".venv", "venv", "env",
    "Step 4 results", "Step 4 extension"
}


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


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return any(x in parts for x in SKIP_DIR_PARTS)


def filename_score(path: Path) -> int:
    low = path.name.lower()
    score = 0
    for t in FILE_TERMS:
        if t in low:
            score += 2
    for t in STRONG_TERMS:
        if t in low:
            score += 5
    return score


def column_score(cols) -> tuple[int, list[str]]:
    hits = []
    score = 0
    for c in cols:
        low = str(c).lower()
        for t in COLUMN_TERMS:
            if t in low:
                hits.append(str(c))
                score += 1
        for t in STRONG_TERMS:
            if t in low:
                score += 4
    return score, sorted(set(hits))


def read_table(path: Path):
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, low_memory=False)
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return None


def main():
    print(TITLE)
    print("=" * 72)

    root = find_root(Path.cwd())
    frozen = root / "Step 3 results" / "Paper7B_Hosein_to_Shayan_Frozen_Source_Package"
    out = root / "Step 4 results" / "02_cif_chemistry" / "phase2d0_linker_localization_feasibility"
    out.mkdir(parents=True, exist_ok=True)

    case_set_path = frozen / "08_structures" / "02_final_case_set.csv"
    case_fw_path = frozen / "08_structures" / "02_final_case_frameworks.csv"
    if not case_set_path.exists() or not case_fw_path.exists():
        raise RuntimeError("Frozen selected-case files are missing.")

    case_set = pd.read_csv(case_set_path, low_memory=False)
    case_fw = pd.read_csv(case_fw_path, low_memory=False)

    mof_col = resolve_col(case_fw, ["mof_id", "framework_id", "framework", "mof"])
    if mof_col is None:
        raise RuntimeError("Could not resolve selected framework ID column.")
    selected_ids = {norm_id(v) for v in case_fw[mof_col].dropna().astype(str)}

    pair_col = resolve_col(case_set, ["pair_id", "pair_key", "pair"])
    selected_pairs = set(case_set[pair_col].dropna().astype(str)) if pair_col else set()

    scan_roots = [
        root / "analysis",
        root / "Step 1 results",
        root / "Step 2 results",
        root / "Step 3 results",
        root / "Step 1 computation",
        root / "Step 2 calculation",
        root / "Step 3 production",
    ]

    table_candidates = []
    selected_extracts = []

    seen = set()
    for base in scan_roots:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p in seen or should_skip(p) or not p.is_file():
                continue
            seen.add(p)
            if p.suffix.lower() not in {".csv", ".parquet"}:
                continue

            fs = filename_score(p)
            # Avoid reading every huge table unless filename already suggests relevance.
            if fs == 0 and p.stat().st_size > 100 * 1024 * 1024:
                continue

            try:
                df = read_table(p)
            except Exception as exc:
                table_candidates.append({
                    "path": str(p.relative_to(root)),
                    "size_bytes": p.stat().st_size,
                    "filename_score": fs,
                    "read_error": f"{type(exc).__name__}: {exc}",
                })
                continue

            cs, hitcols = column_score(df.columns)
            total = fs + cs
            if total <= 0:
                continue

            id_col = resolve_col(df, ["mof_id", "framework_id", "framework", "mof", "id_a", "id_b"])
            p_col = resolve_col(df, ["pair_id", "pair_key", "pair"])

            selected_rows = 0
            selected_framework_hits = 0
            selected_pair_hits = 0

            masks = []
            if id_col:
                ids = df[id_col].astype(str).map(norm_id)
                m = ids.isin(selected_ids)
                masks.append(m)
                selected_framework_hits = int(ids[m].nunique())
            if p_col and selected_pairs:
                vals = df[p_col].astype(str)
                mp = vals.isin(selected_pairs)
                masks.append(mp)
                selected_pair_hits = int(vals[mp].nunique())

            if masks:
                mask = masks[0].copy()
                for m in masks[1:]:
                    mask = mask | m
                sub = df.loc[mask].copy()
                selected_rows = len(sub)
                if selected_rows:
                    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", p.stem)
                    dest = out / f"selected_rows__{safe}.csv"
                    # avoid collisions
                    k = 2
                    while dest.exists():
                        dest = out / f"selected_rows__{safe}_{k}.csv"
                        k += 1
                    sub.to_csv(dest, index=False)
                    selected_extracts.append({
                        "source": str(p.relative_to(root)),
                        "extract": dest.name,
                        "rows": len(sub),
                    })

            table_candidates.append({
                "path": str(p.relative_to(root)),
                "size_bytes": p.stat().st_size,
                "rows": len(df),
                "columns": json.dumps([str(c) for c in df.columns]),
                "filename_score": fs,
                "column_score": cs,
                "total_score": total,
                "relevant_columns": json.dumps(hitcols),
                "id_column": id_col,
                "pair_column": p_col,
                "selected_rows": selected_rows,
                "selected_framework_hits": selected_framework_hits,
                "selected_pair_hits": selected_pair_hits,
                "read_error": "",
            })

    tables = pd.DataFrame(table_candidates)
    if not tables.empty:
        tables = tables.sort_values(
            ["selected_rows", "total_score", "size_bytes"],
            ascending=[False, False, True]
        )
    tables.to_csv(out / "phase2d0_candidate_tables.csv", index=False)
    pd.DataFrame(selected_extracts).to_csv(out / "phase2d0_selected_extract_manifest.csv", index=False)

    # Search source code for explicit linker/fragment/atom mapping logic.
    code_rows = []
    code_terms = [
        "linker", "ligand", "fragment", "building_block", "building block",
        "smiles", "atom_map", "atom mapping", "substructure", "organic node"
    ]
    for base in scan_roots:
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if should_skip(p):
                continue
            try:
                text = p.read_text(encoding="utf-8-sig", errors="replace")
            except Exception:
                continue
            for i, line in enumerate(text.splitlines(), start=1):
                low = line.lower()
                hits = [t for t in code_terms if t in low]
                if hits:
                    score = sum(5 if t in STRONG_TERMS else 1 for t in hits)
                    code_rows.append({
                        "path": str(p.relative_to(root)),
                        "line": i,
                        "score": score,
                        "matched_terms": ";".join(hits),
                        "source_line": line.strip(),
                    })

    code = pd.DataFrame(code_rows)
    if not code.empty:
        code = code.sort_values(["score", "path", "line"], ascending=[False, True, True])
    code.to_csv(out / "phase2d0_linker_mapping_code_hits.csv", index=False)

    # Decision is feasibility, not scientific success.
    top_tables = tables[
        (tables.get("selected_rows", 0) > 0)
        & (
            tables.get("relevant_columns", pd.Series(index=tables.index, dtype=str))
            .astype(str)
            .str.lower()
            .str.contains("linker|ligand|fragment|smiles|building")
        )
    ] if not tables.empty else pd.DataFrame()

    strong_code = code[code["score"] >= 5] if not code.empty else pd.DataFrame()

    if len(top_tables) > 0:
        decision = "PASS_EXISTING_LINKER_OBJECT_CANDIDATES"
        next_step = "INSPECT_TOP_SELECTED_CASE_TABLES_BEFORE_ANY_NEW_ATOM_MAPPING"
    elif len(strong_code) > 0:
        decision = "CONDITIONAL_CODE_LOGIC_EXISTS"
        next_step = "RECOVER_EXACT_LINKER_DEFINITION_FROM_SOURCE_CODE"
    else:
        decision = "NO_EXISTING_EXPLICIT_LINKER_MAPPING_FOUND"
        next_step = "DO_NOT_INVENT_MAPPING_YET; DECIDE WHETHER A NEW GRAPH-BASED MAPPING IS WORTH THE SCOPE"

    summary = {
        "decision": decision,
        "selected_frameworks": len(selected_ids),
        "selected_pairs": len(selected_pairs),
        "candidate_tables": len(tables),
        "candidate_tables_with_selected_rows": int((tables["selected_rows"] > 0).sum()) if not tables.empty else 0,
        "strong_selected_linker_tables": len(top_tables),
        "linker_mapping_code_hits": len(code),
        "strong_code_hits": len(strong_code),
        "next_step": next_step,
    }
    (out / "phase2d0_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Decision: {decision}")
    print(f"Selected frameworks: {len(selected_ids)}")
    print(f"Selected pairs: {len(selected_pairs)}")
    print(f"Candidate relevant tables: {len(tables)}")
    print(f"Candidate tables with selected-case rows: {summary['candidate_tables_with_selected_rows']}")
    print(f"Strong selected-case linker/ligand/fragment tables: {len(top_tables)}")
    print(f"Source-code linker/mapping hits: {len(code)}")
    print(f"Strong source-code hits: {len(strong_code)}")

    if not tables.empty:
        print("\nTop candidate tables:")
        for _, r in tables.head(10).iterrows():
            print(
                f"  {r['path']} | selected_rows={int(r.get('selected_rows', 0))} "
                f"| score={int(r.get('total_score', 0))}"
            )

    if not code.empty:
        print("\nTop source-code hits:")
        for _, r in code.head(10).iterrows():
            print(f"  {r['path']}:{int(r['line'])} | {r['matched_terms']}")

    print(f"\nNext: {next_step}")
    print("No linker atom assignment or new scientific effect was computed.")
    print(f"Outputs: {out}")


if __name__ == "__main__":
    main()
