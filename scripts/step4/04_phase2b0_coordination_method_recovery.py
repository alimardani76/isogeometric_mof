#!/usr/bin/env python3
"""
Project 7B Step 4 - Phase 2B0
Recover and audit the exact existing metal-coordination implementation before
any new selected-case local-chemistry calculation is allowed.

READ ONLY with respect to Steps 1-3.

Outputs:
  Step 4 results/02_cif_chemistry/phase2b0_method_recovery/
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd

TITLE = "PROJECT 7B STEP 4 - PHASE 2B0 COORDINATION METHOD RECOVERY AUDIT"


def find_project_root(start: Path) -> Path:
    p = start.resolve()
    for cand in [p] + list(p.parents):
        if (cand / "Step 3 results").exists() and (cand / "Step 4 extension").exists():
            return cand
    raise RuntimeError("Could not locate Project 7B root.")


def sha256(path: Path, block: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(block)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def normalize_id(x) -> str:
    s = str(x).strip()
    if s.lower().endswith(".cif"):
        s = s[:-4]
    return s


def resolve_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
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


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path, low_memory=False)


def ast_text(node) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return "<unparse-failed>"


def recover_crystalnn_calls(source: str) -> list[dict]:
    tree = ast.parse(source)
    rows = []
    parent = {}

    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent[child] = node

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        fn = ast_text(node.func)
        if not (fn == "CrystalNN" or fn.endswith(".CrystalNN")):
            continue

        assigned_to = ""
        par = parent.get(node)
        if isinstance(par, ast.Assign):
            assigned_to = ",".join(ast_text(t) for t in par.targets)
        elif isinstance(par, ast.AnnAssign):
            assigned_to = ast_text(par.target)

        args = [ast_text(a) for a in node.args]
        kwargs = {kw.arg if kw.arg is not None else "**": ast_text(kw.value) for kw in node.keywords}

        literal_kwargs = {}
        literal_ok = True
        for k, kw in zip(kwargs.keys(), node.keywords):
            if kw.arg is None:
                literal_ok = False
                literal_kwargs[k] = "<**kwargs>"
                continue
            try:
                literal_kwargs[k] = ast.literal_eval(kw.value)
            except Exception:
                literal_ok = False
                literal_kwargs[k] = ast_text(kw.value)

        rows.append({
            "line": getattr(node, "lineno", None),
            "assigned_to": assigned_to,
            "constructor": ast_text(node),
            "positional_args": json.dumps(args),
            "keyword_expressions": json.dumps(kwargs, sort_keys=True),
            "literal_kwargs": json.dumps(literal_kwargs, sort_keys=True, default=str),
            "all_keywords_literal": literal_ok,
        })

    return rows


def recover_method_calls(source: str) -> pd.DataFrame:
    tree = ast.parse(source)
    wanted = {
        "get_nn_info",
        "get_cn",
        "get_nn_shell_info",
        "get_bonded_structure",
    }
    rows = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = ast_text(node.func)
        last = fn.split(".")[-1]
        if last in wanted:
            rows.append({
                "line": getattr(node, "lineno", None),
                "method": last,
                "call": ast_text(node),
            })
    return pd.DataFrame(rows)


def source_excerpt(source_lines: list[str], line_numbers: list[int], radius: int = 8) -> str:
    keep = set()
    for ln in line_numbers:
        for j in range(max(1, ln-radius), min(len(source_lines), ln+radius)+1):
            keep.add(j)
    out = []
    previous = None
    for j in sorted(keep):
        if previous is not None and j > previous + 1:
            out.append("\n...\n")
        out.append(f"{j:5d}: {source_lines[j-1]}\n")
        previous = j
    return "".join(out)


def main():
    print(TITLE)
    print("=" * 72)

    root = find_project_root(Path.cwd())
    out = root / "Step 4 results" / "02_cif_chemistry" / "phase2b0_method_recovery"
    out.mkdir(parents=True, exist_ok=True)

    source_script = root / "Step 1 computation" / "04_check_metal_coordination.py"
    if not source_script.exists():
        raise RuntimeError(f"Missing original coordination script: {source_script}")

    source = source_script.read_text(encoding="utf-8-sig", errors="replace")
    source_lines = source.splitlines()

    calls = recover_crystalnn_calls(source)
    calls_df = pd.DataFrame(calls)
    calls_df.to_csv(out / "phase2b0_crystalnn_constructors.csv", index=False)

    method_df = recover_method_calls(source)
    method_df.to_csv(out / "phase2b0_neighbor_method_calls.csv", index=False)

    line_numbers = []
    if not calls_df.empty:
        line_numbers.extend(pd.to_numeric(calls_df["line"], errors="coerce").dropna().astype(int).tolist())
    if not method_df.empty:
        line_numbers.extend(pd.to_numeric(method_df["line"], errors="coerce").dropna().astype(int).tolist())

    (out / "phase2b0_coordination_source_excerpt.txt").write_text(
        source_excerpt(source_lines, line_numbers, radius=10),
        encoding="utf-8"
    )

    # Selected case IDs
    frozen = root / "Step 3 results" / "Paper7B_Hosein_to_Shayan_Frozen_Source_Package"
    case_framework_file = frozen / "08_structures" / "02_final_case_frameworks.csv"
    case_set_file = frozen / "08_structures" / "02_final_case_set.csv"

    selected_ids: set[str] = set()
    case_df = pd.DataFrame()
    if case_framework_file.exists():
        case_df = pd.read_csv(case_framework_file, low_memory=False)
        id_col = resolve_col(case_df, ["mof_id", "framework_id", "mof", "framework"])
        if id_col:
            selected_ids = {normalize_id(v) for v in case_df[id_col].dropna().astype(str)}

    pair_ids: set[str] = set()
    case_set_df = pd.DataFrame()
    if case_set_file.exists():
        case_set_df = pd.read_csv(case_set_file, low_memory=False)
        pair_col = resolve_col(case_set_df, ["pair_id", "pair"])
        if pair_col:
            pair_ids = set(case_set_df[pair_col].dropna().astype(str))

    outputs = [
        root / "analysis" / "metal_coordination_failures.csv",
        root / "analysis" / "metal_coordination_signatures.parquet",
        root / "analysis" / "metal_pairs_coordination_classified.parquet",
        root / "analysis" / "metal_pair_coordination_summary.csv",
        root / "analysis" / "metal_coordination_work" / "coordination_signatures_checkpoint.csv",
    ]

    schema_rows = []
    coverage_rows = []
    readable_count = 0

    for p in outputs:
        rec = {
            "path": str(p.relative_to(root)) if p.exists() else str(p),
            "exists": p.exists(),
            "sha256": sha256(p) if p.exists() else None,
            "rows": None,
            "columns": None,
            "id_column": None,
            "pair_column": None,
            "selected_framework_rows": 0,
            "selected_framework_ids": 0,
            "selected_pair_rows": 0,
            "selected_pair_ids": 0,
            "read_error": None,
        }

        if not p.exists():
            schema_rows.append(rec)
            continue

        try:
            df = read_table(p)
            readable_count += 1
            rec["rows"] = len(df)
            rec["columns"] = json.dumps([str(c) for c in df.columns])

            id_col = resolve_col(df, ["mof_id", "framework_id", "mof", "framework", "name"])
            pair_col = resolve_col(df, ["pair_id", "pair"])

            rec["id_column"] = id_col
            rec["pair_column"] = pair_col

            if id_col and selected_ids:
                ids = df[id_col].astype(str).map(normalize_id)
                mask = ids.isin(selected_ids)
                sub = df.loc[mask].copy()
                rec["selected_framework_rows"] = int(mask.sum())
                rec["selected_framework_ids"] = int(ids[mask].nunique())
                if not sub.empty:
                    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", p.stem)
                    sub.to_csv(out / f"selected_rows__{safe_name}.csv", index=False)

            if pair_col and pair_ids:
                vals = df[pair_col].astype(str)
                maskp = vals.isin(pair_ids)
                subp = df.loc[maskp].copy()
                rec["selected_pair_rows"] = int(maskp.sum())
                rec["selected_pair_ids"] = int(vals[maskp].nunique())
                if not subp.empty:
                    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", p.stem)
                    subp.to_csv(out / f"selected_pairs__{safe_name}.csv", index=False)

            # Column-level schema
            for c in df.columns:
                s = df[c]
                schema_rows.append({
                    "path": str(p.relative_to(root)),
                    "exists": True,
                    "sha256": sha256(p),
                    "rows": len(df),
                    "column": str(c),
                    "dtype": str(s.dtype),
                    "nonnull": int(s.notna().sum()),
                    "nunique": int(s.nunique(dropna=True)),
                    "sample_values": json.dumps(
                        [str(v) for v in s.dropna().astype(str).head(5).tolist()],
                        ensure_ascii=False
                    ),
                })

            coverage_rows.append(rec)

        except Exception as exc:
            rec["read_error"] = f"{type(exc).__name__}: {exc}"
            coverage_rows.append(rec)

    pd.DataFrame(schema_rows).to_csv(out / "phase2b0_existing_output_schema.csv", index=False)
    coverage_df = pd.DataFrame(coverage_rows)
    coverage_df.to_csv(out / "phase2b0_existing_output_coverage.csv", index=False)

    # Recover exact constructor interpretation, but do not silently "correct" it.
    interpreted = []
    for _, r in calls_df.iterrows():
        try:
            kw = json.loads(r["literal_kwargs"])
        except Exception:
            kw = {}
        interpreted.append({
            "line": int(r["line"]) if pd.notna(r["line"]) else None,
            "assigned_to": r["assigned_to"],
            "constructor": r["constructor"],
            "all_keywords_literal": bool(r["all_keywords_literal"]),
            "x_diff_weight_explicit": kw.get("x_diff_weight", "<default>"),
            "porous_adjustment_explicit": kw.get("porous_adjustment", "<default>"),
            "weighted_cn_explicit": kw.get("weighted_cn", "<default>"),
            "cation_anion_explicit": kw.get("cation_anion", "<default>"),
            "distance_cutoffs_explicit": kw.get("distance_cutoffs", "<default>"),
            "search_cutoff_explicit": kw.get("search_cutoff", "<default>"),
        })
    interpreted_df = pd.DataFrame(interpreted)
    interpreted_df.to_csv(out / "phase2b0_recovered_crystalnn_settings.csv", index=False)

    # Evidence boundary for Phase 2B proper.
    boundary = pd.DataFrame([
        {
            "object": "CrystalNN neighbor shell",
            "allowed_claim": "algorithmic local coordination / neighbor identity under the recovered setting",
            "not_allowed": "experimental bond assignment, oxidation state, adsorption site",
        },
        {
            "object": "agreement across two CrystalNN settings",
            "allowed_claim": "method robustness of the coordination classification",
            "not_allowed": "proof that the local environment is chemically invariant in every representation",
        },
        {
            "object": "ChemEnv geometry cross-check",
            "allowed_claim": "independent algorithmic coordination-environment description",
            "not_allowed": "adsorption mechanism or guest-binding geometry",
        },
        {
            "object": "REPEAT charge on aligned CIF sites",
            "allowed_claim": "case-level electrostatic partial-charge fingerprint",
            "not_allowed": "oxidation state, charge transfer, causal electrostatic mechanism",
        },
        {
            "object": "first-shell element and distance summary",
            "allowed_claim": "descriptive local chemical environment",
            "not_allowed": "pore accessibility or preferred binding site without separate geometric/simulation evidence",
        },
    ])
    boundary.to_csv(out / "phase2b0_evidence_boundaries.csv", index=False)

    fatal = []
    warnings = []

    if len(calls_df) == 0:
        fatal.append("No CrystalNN constructor was recovered from the original coordination script.")
    if readable_count == 0:
        fatal.append("None of the existing coordination outputs could be read.")
    if any(not bool(v) for v in calls_df.get("all_keywords_literal", pd.Series(dtype=bool)).tolist()):
        warnings.append("At least one CrystalNN constructor contains non-literal configuration; Phase 2B must not guess its value.")
    if len(calls_df) < 2:
        warnings.append("Fewer than two CrystalNN constructor calls were recovered; verify how the second sensitivity setting is created.")
    if len(selected_ids) != 12:
        warnings.append(f"Selected framework ID count is {len(selected_ids)}, expected 12.")
    if coverage_df.empty:
        warnings.append("No existing-output coverage table was produced.")

    decision = "PASS" if not fatal else "FAIL"

    summary = {
        "decision": decision,
        "project_root": str(root),
        "source_script": str(source_script.relative_to(root)),
        "source_script_sha256": sha256(source_script),
        "crystalnn_constructor_calls": int(len(calls_df)),
        "neighbor_method_calls": int(len(method_df)),
        "existing_outputs_readable": int(readable_count),
        "selected_framework_ids": int(len(selected_ids)),
        "selected_pair_ids": int(len(pair_ids)),
        "fatal": fatal,
        "warnings": warnings,
        "phase2b_permission": (
            "MAY_PROCEED_TO_SELECTED_CASE_COORDINATION_EXTENSION"
            if decision == "PASS"
            else "STOP"
        ),
    }
    (out / "phase2b0_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Decision: {decision}")
    print(f"Original coordination script: {source_script.relative_to(root)}")
    print(f"CrystalNN constructor calls recovered: {len(calls_df)}")
    print(f"Neighbor-method calls recovered: {len(method_df)}")
    print(f"Existing coordination tables readable: {readable_count}")
    print(f"Selected framework IDs: {len(selected_ids)}")
    print(f"Selected pair IDs: {len(pair_ids)}")

    if not interpreted_df.empty:
        print("\nRecovered CrystalNN constructors:")
        for _, r in interpreted_df.iterrows():
            print(f"  line {r['line']}: {r['constructor']}")

    if not coverage_df.empty:
        print("\nSelected-case coverage in existing coordination outputs:")
        for _, r in coverage_df.iterrows():
            if r.get("read_error"):
                print(f"  {r['path']}: READ ERROR {r['read_error']}")
            else:
                print(
                    f"  {r['path']}: rows={r.get('rows')} | "
                    f"selected frameworks={r.get('selected_framework_ids', 0)} | "
                    f"selected pairs={r.get('selected_pair_ids', 0)}"
                )

    for w in warnings:
        print(f"WARN: {w}")
    for f in fatal:
        print(f"FATAL: {f}")

    print("No new coordination classification, adsorption effect, matching, bootstrap, or process result was computed.")
    print(f"Outputs: {out}")

    if decision != "PASS":
        sys.exit(2)


if __name__ == "__main__":
    main()
