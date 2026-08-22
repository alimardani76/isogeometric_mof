#!/usr/bin/env python3
"""
Project 7B Step 4 - Phase 2D1
Targeted linker-definition and atom-mapping recovery audit.

Why this exists
---------------
Phase 2D0 was intentionally broad and therefore over-inclusive: thousands of
tables matched generic words such as "pair", "atom", "structure", or "linker".
This phase narrows the question to the only thing that matters now:

What EXACT linker object did Project 7B use, and does any existing object map
that linker identity onto explicit atom rows/sites for the six frozen cases?

This script does NOT create a new linker assignment and does NOT compute any new
adsorption/chemistry effect.

READ ONLY with respect to Steps 1-3.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

TITLE = "PROJECT 7B STEP 4 - PHASE 2D1 LINKER DEFINITION RECOVERY AUDIT"

EXACT_LINKER_COLUMN_PATTERNS = [
    r"(^|_)linker($|_)",
    r"linker_id",
    r"linker_family",
    r"linker_key",
    r"linker_hash",
    r"linker_smiles",
    r"linker_formula",
    r"linker_atom",
    r"ligand_id",
    r"ligand_family",
    r"ligand_smiles",
    r"fragment_id",
    r"fragment_smiles",
    r"organic_component",
]

ATOM_MAPPING_PATTERNS = [
    r"linker_atom",
    r"ligand_atom",
    r"fragment_atom",
    r"atom_indices",
    r"atom_index",
    r"site_indices",
    r"site_index",
    r"atom_labels",
    r"site_labels",
    r"mapped_atoms",
    r"atom_map",
]

PAIR_ID_CANDIDATES = ["pair_id", "pair_key", "pair"]
A_CANDIDATES = ["id_a", "mof_a", "framework_a", "mof_id_a", "framework_id_a"]
B_CANDIDATES = ["id_b", "mof_b", "framework_b", "mof_id_b", "framework_id_b"]
MOF_CANDIDATES = ["mof_id", "framework_id", "framework", "mof"]


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


def resolve_exactish(df: pd.DataFrame, candidates: list[str]):
    lower = {str(c).lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None


def matching_columns(columns, patterns):
    out = []
    for c in columns:
        low = str(c).lower()
        if any(re.search(p, low) for p in patterns):
            out.append(str(c))
    return sorted(set(out))


def read_table(path: Path):
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, low_memory=False)
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    raise ValueError("Unsupported table type")


def source_excerpt(path: Path, patterns, radius=10):
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = text.splitlines()
    hit_lines = []
    hits = []
    for i, line in enumerate(lines, start=1):
        low = line.lower()
        matched = [p for p in patterns if p.lower() in low]
        if matched:
            hit_lines.append(i)
            hits.append((i, line.rstrip(), matched))

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

    return hits, "".join(out)


def selected_mask(df, selected_ids, selected_pairs):
    masks = []

    mof_col = resolve_exactish(df, MOF_CANDIDATES)
    if mof_col:
        vals = df[mof_col].astype(str).map(norm_id)
        masks.append(vals.isin(selected_ids))

    a_col = resolve_exactish(df, A_CANDIDATES)
    b_col = resolve_exactish(df, B_CANDIDATES)
    if a_col:
        vals = df[a_col].astype(str).map(norm_id)
        masks.append(vals.isin(selected_ids))
    if b_col:
        vals = df[b_col].astype(str).map(norm_id)
        masks.append(vals.isin(selected_ids))

    pair_col = resolve_exactish(df, PAIR_ID_CANDIDATES)
    if pair_col and selected_pairs:
        vals = df[pair_col].astype(str)
        masks.append(vals.isin(selected_pairs))

    if not masks:
        return pd.Series(False, index=df.index)

    m = masks[0].copy()
    for x in masks[1:]:
        m = m | x
    return m


def main():
    print(TITLE)
    print("=" * 72)

    root = find_root(Path.cwd())
    frozen = root / "Step 3 results" / "Paper7B_Hosein_to_Shayan_Frozen_Source_Package"
    out = root / "Step 4 results" / "02_cif_chemistry" / "phase2d1_linker_definition_recovery"
    out.mkdir(parents=True, exist_ok=True)

    case_set_path = frozen / "08_structures" / "02_final_case_set.csv"
    case_fw_path = frozen / "08_structures" / "02_final_case_frameworks.csv"

    case_set = pd.read_csv(case_set_path, low_memory=False)
    case_fw = pd.read_csv(case_fw_path, low_memory=False)

    mof_col = resolve_exactish(case_fw, MOF_CANDIDATES)
    if mof_col is None:
        raise RuntimeError("Could not resolve selected framework ID column.")
    selected_ids = {norm_id(v) for v in case_fw[mof_col].dropna().astype(str)}

    pair_col = resolve_exactish(case_set, PAIR_ID_CANDIDATES)
    selected_pairs = set(case_set[pair_col].dropna().astype(str)) if pair_col else set()

    # 1. Recover original source-code definition first.
    source_candidates = [
        root / "Step 1 computation" / "01_build_cohort.py",
        root / "Step 1 computation" / "03_build_candidate_pairs.py",
        root / "Step 1 computation" / "04_check_metal_coordination.py",
    ]
    source_terms = [
        "linker", "linker_family", "linker family", "ligand", "fragment",
        "functional_motif", "functional motif", "pair_rule", "pair rule",
        "same_geometry", "same geometry", "chemistry"
    ]

    source_summary = []
    for p in source_candidates:
        if not p.exists():
            source_summary.append({
                "path": str(p.relative_to(root)),
                "exists": False,
                "hits": 0,
            })
            continue

        hits, excerpt = source_excerpt(p, source_terms, radius=12)
        dest = out / f"source_excerpt__{p.stem}.txt"
        dest.write_text(excerpt, encoding="utf-8")

        source_summary.append({
            "path": str(p.relative_to(root)),
            "exists": True,
            "hits": len(hits),
            "excerpt_file": dest.name,
        })

    pd.DataFrame(source_summary).to_csv(out / "phase2d1_source_definition_files.csv", index=False)

    # 2. Target only tables whose SCHEMA contains explicit linker/ligand/fragment fields.
    search_dirs = [
        root / "analysis",
        root / "Step 1 results",
        root / "Step 2 results",
        root / "Step 3 results",
    ]

    table_rows = []
    extract_rows = []
    seen = set()

    for base in search_dirs:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p in seen:
                continue
            seen.add(p)

            if "Step 4 results" in p.parts:
                continue
            if p.suffix.lower() not in {".csv", ".parquet"}:
                continue

            # Strong filename cue or known key table. This avoids the 16k-table broad scan.
            name_low = p.name.lower()
            strong_filename = any(
                t in name_low
                for t in ["linker", "ligand", "fragment", "cohort", "candidate_pair",
                          "primary_pair", "pair_rules", "pair_rule"]
            )
            if not strong_filename:
                continue

            try:
                df = read_table(p)
            except Exception as exc:
                table_rows.append({
                    "path": str(p.relative_to(root)),
                    "read_error": f"{type(exc).__name__}: {exc}",
                })
                continue

            linker_cols = matching_columns(df.columns, EXACT_LINKER_COLUMN_PATTERNS)
            atom_cols = matching_columns(df.columns, ATOM_MAPPING_PATTERNS)

            if not linker_cols and not atom_cols:
                continue

            mask = selected_mask(df, selected_ids, selected_pairs)
            sub = df.loc[mask].copy()
            selected_rows = len(sub)

            classification = "FRAMEWORK_OR_PAIR_LINKER_METADATA"
            if atom_cols:
                classification = "ATOM_MAPPING_CANDIDATE"
            elif any("smiles" in c.lower() for c in linker_cols):
                classification = "MOLECULAR_LINKER_IDENTITY"
            elif any("family" in c.lower() or "id" in c.lower() or "key" in c.lower() for c in linker_cols):
                classification = "LINKER_IDENTITY_OR_FAMILY"

            rec = {
                "path": str(p.relative_to(root)),
                "rows": len(df),
                "selected_rows": selected_rows,
                "linker_columns": json.dumps(linker_cols),
                "atom_mapping_columns": json.dumps(atom_cols),
                "classification": classification,
                "columns": json.dumps([str(c) for c in df.columns]),
                "read_error": "",
            }
            table_rows.append(rec)

            if selected_rows:
                safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", p.stem)
                dest = out / f"selected__{safe}.csv"
                k = 2
                while dest.exists():
                    dest = out / f"selected__{safe}_{k}.csv"
                    k += 1

                # Save selected rows, but keep only a manageable set of useful columns.
                key_cols = []
                for candidates in [MOF_CANDIDATES, A_CANDIDATES, B_CANDIDATES, PAIR_ID_CANDIDATES]:
                    c = resolve_exactish(sub, candidates)
                    if c and c not in key_cols:
                        key_cols.append(c)
                keep = key_cols + [c for c in linker_cols + atom_cols if c not in key_cols]
                keep = [c for c in keep if c in sub.columns]
                if keep:
                    sub[keep].to_csv(dest, index=False)
                else:
                    sub.head(200).to_csv(dest, index=False)

                extract_rows.append({
                    "source": str(p.relative_to(root)),
                    "extract": dest.name,
                    "rows": selected_rows,
                    "classification": classification,
                    "linker_columns": json.dumps(linker_cols),
                    "atom_mapping_columns": json.dumps(atom_cols),
                })

    tables = pd.DataFrame(table_rows)
    if not tables.empty:
        priority = {
            "ATOM_MAPPING_CANDIDATE": 0,
            "MOLECULAR_LINKER_IDENTITY": 1,
            "LINKER_IDENTITY_OR_FAMILY": 2,
            "FRAMEWORK_OR_PAIR_LINKER_METADATA": 3,
        }
        tables["_priority"] = tables["classification"].map(priority).fillna(9)
        tables = tables.sort_values(
            ["selected_rows", "_priority", "rows"],
            ascending=[False, True, True]
        ).drop(columns="_priority")

    tables.to_csv(out / "phase2d1_targeted_linker_tables.csv", index=False)
    pd.DataFrame(extract_rows).to_csv(out / "phase2d1_selected_extract_manifest.csv", index=False)

    # 3. Explicit evidence decision.
    atom_candidates = tables[
        (tables["classification"] == "ATOM_MAPPING_CANDIDATE")
        & (tables["selected_rows"] > 0)
    ] if not tables.empty else pd.DataFrame()

    molecular_candidates = tables[
        (tables["classification"] == "MOLECULAR_LINKER_IDENTITY")
        & (tables["selected_rows"] > 0)
    ] if not tables.empty else pd.DataFrame()

    identity_candidates = tables[
        tables["classification"].isin(["LINKER_IDENTITY_OR_FAMILY", "FRAMEWORK_OR_PAIR_LINKER_METADATA"])
        & (tables["selected_rows"] > 0)
    ] if not tables.empty else pd.DataFrame()

    if len(atom_candidates):
        decision = "EXPLICIT_ATOM_MAPPING_CANDIDATE_EXISTS"
        next_step = "INSPECT_ATOM_MAPPING_CANDIDATE_BEFORE REUSING IT"
    elif len(molecular_candidates):
        decision = "LINKER_MOLECULAR_IDENTITY_EXISTS_BUT_NO_ATOM_MAPPING"
        next_step = "RECOVER HOW MOLECULAR LINKER IDENTITY WAS DERIVED; DO NOT MAP ATOMS YET"
    elif len(identity_candidates):
        decision = "LINKER_FAMILY_OR_PAIR_RULE_EXISTS_BUT_NO_ATOM_MAPPING"
        next_step = "USE EXISTING LINKER FAMILY ONLY FOR PAIR CLASSIFICATION; NEW ATOM LOCALIZATION WOULD BE A NEW METHOD"
    else:
        decision = "NO_EXPLICIT_LINKER_OBJECT_RECOVERED"
        next_step = "STOP LINKER-LOCAL CHARGE ATTRIBUTION UNLESS A NEW METHOD IS JUSTIFIED"

    summary = {
        "decision": decision,
        "selected_frameworks": len(selected_ids),
        "selected_pairs": len(selected_pairs),
        "targeted_tables_found": len(tables),
        "targeted_tables_with_selected_rows": int((tables["selected_rows"] > 0).sum()) if not tables.empty else 0,
        "atom_mapping_candidates": len(atom_candidates),
        "molecular_linker_identity_candidates": len(molecular_candidates),
        "linker_family_or_pair_metadata_candidates": len(identity_candidates),
        "next_step": next_step,
    }
    (out / "phase2d1_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Decision: {decision}")
    print(f"Selected frameworks: {len(selected_ids)}")
    print(f"Selected pairs: {len(selected_pairs)}")
    print(f"Targeted linker tables found: {len(tables)}")
    print(f"Targeted tables with selected rows: {summary['targeted_tables_with_selected_rows']}")
    print(f"Explicit atom-mapping candidates: {len(atom_candidates)}")
    print(f"Molecular linker-identity candidates: {len(molecular_candidates)}")
    print(f"Linker family/pair-rule candidates: {len(identity_candidates)}")

    if not tables.empty:
        print("\nHighest-priority selected-case tables:")
        for _, r in tables[tables["selected_rows"] > 0].head(12).iterrows():
            print(
                f"  {r['path']} | {r['classification']} | "
                f"selected_rows={int(r['selected_rows'])} | "
                f"linker_cols={r['linker_columns']} | "
                f"atom_cols={r['atom_mapping_columns']}"
            )

    print("\nOriginal-definition excerpts written for:")
    for r in source_summary:
        if r.get("exists"):
            print(f"  {r['path']} -> {r.get('excerpt_file')}")

    print(f"\nNext: {next_step}")
    print("No linker atom assignment or new scientific effect was computed.")
    print(f"Outputs: {out}")


if __name__ == "__main__":
    main()
