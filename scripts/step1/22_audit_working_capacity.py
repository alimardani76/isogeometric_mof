#!/usr/bin/env python3
"""Audit the provenance and algebra of ARC-MOF process working capacity.

Questions
---------
1. Is mmol/g_working_capacity constructed from mmol/g_uptake?
2. Does uptake - working_capacity define a nonnegative desorption loading?
3. Is the working-capacity result independent evidence, or persistence of a
   high-pressure uptake advantage after subtracting low-pressure loading?

The script combines a numerical identity audit with a text search for the
process-generation formula in local scripts and documentation. It changes no
scientific value and estimates no chemistry effect.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import platform
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
ANALYSIS = ROOT / "analysis"

PROCESS_INPUT = RAW / "overall_process.csv"
NUMERIC_OUTPUT = ANALYSIS / "working_capacity_provenance_numeric_audit.csv"
TEXT_OUTPUT = ANALYSIS / "working_capacity_provenance_text_hits.csv"
MANIFEST_OUTPUT = ANALYSIS / "working_capacity_provenance_manifest.json"

N_JOBS = 1
CHUNK_SIZE = 250_000
TEXT_EXTENSIONS = {".py", ".md", ".txt", ".tex", ".yaml", ".yml", ".json"}
SEARCH_TERMS = [
    "working capacity",
    "working_capacity",
    "mmol/g_working_capacity",
    "overall_process",
]
EXCLUDED_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "env", "node_modules",
    "analysis", "figures", "si_figures"
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def text_formula_hits() -> pd.DataFrame:
    hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.name == Path(__file__).name:
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(lines, start=1):
            lower = line.lower()
            if any(term in lower for term in SEARCH_TERMS):
                start = max(0, number - 3)
                end = min(len(lines), number + 2)
                context = "\n".join(
                    f"{i + 1}: {lines[i]}" for i in range(start, end)
                )
                hits.append({
                    "file": str(path.relative_to(ROOT)),
                    "line": number,
                    "matched_text": line.strip(),
                    "context": context,
                })
    return pd.DataFrame(hits)


def main() -> None:
    if not PROCESS_INPUT.exists():
        raise FileNotFoundError(PROCESS_INPUT)

    required = [
        "process",
        "mmol/g_uptake",
        "mmol/g_working_capacity",
    ]
    header = pd.read_csv(PROCESS_INPUT, nrows=0)
    missing = [column for column in required if column not in header.columns]
    if missing:
        raise ValueError(f"Process table lacks columns: {missing}")

    records = {}
    total_rows = 0

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            PROCESS_INPUT,
            usecols=required,
            chunksize=CHUNK_SIZE,
            low_memory=False,
        ),
        start=1,
    ):
        total_rows += len(chunk)
        chunk["mmol/g_uptake"] = pd.to_numeric(
            chunk["mmol/g_uptake"], errors="coerce"
        )
        chunk["mmol/g_working_capacity"] = pd.to_numeric(
            chunk["mmol/g_working_capacity"], errors="coerce"
        )
        chunk["inferred_desorption_loading"] = (
            chunk["mmol/g_uptake"] - chunk["mmol/g_working_capacity"]
        )

        for process, group in chunk.groupby("process", sort=False, dropna=False):
            process_name = "<MISSING>" if pd.isna(process) else str(process)
            rec = records.setdefault(process_name, {
                "rows": 0,
                "complete": 0,
                "valid_wc": 0,
                "negative_wc": 0,
                "wc_greater_than_uptake": 0,
                "negative_inferred_desorption": 0,
                "uptake": [],
                "working_capacity": [],
                "inferred_desorption": [],
            })
            rec["rows"] += len(group)
            complete = group[[
                "mmol/g_uptake", "mmol/g_working_capacity",
                "inferred_desorption_loading"
            ]].dropna()
            finite = complete.loc[np.isfinite(complete).all(axis=1)]
            rec["complete"] += len(finite)
            rec["valid_wc"] += int(finite["mmol/g_working_capacity"].ge(0).sum())
            rec["negative_wc"] += int(finite["mmol/g_working_capacity"].lt(0).sum())
            rec["wc_greater_than_uptake"] += int(
                finite["mmol/g_working_capacity"].gt(
                    finite["mmol/g_uptake"] + 1e-12
                ).sum()
            )
            rec["negative_inferred_desorption"] += int(
                finite["inferred_desorption_loading"].lt(-1e-12).sum()
            )

            if len(finite):
                step = max(1, len(finite) // 5000)
                sample = finite.iloc[::step].head(5000)
                rec["uptake"].extend(sample["mmol/g_uptake"].tolist())
                rec["working_capacity"].extend(
                    sample["mmol/g_working_capacity"].tolist()
                )
                rec["inferred_desorption"].extend(
                    sample["inferred_desorption_loading"].tolist()
                )
                for key in ["uptake", "working_capacity", "inferred_desorption"]:
                    if len(rec[key]) > 20000:
                        rec[key] = rec[key][::2]

        print(f"audited chunk={chunk_number}; cumulative_rows={total_rows:,}")

    rows = []
    for process, rec in sorted(records.items()):
        uptake = pd.Series(rec.pop("uptake"), dtype=float)
        wc = pd.Series(rec.pop("working_capacity"), dtype=float)
        des = pd.Series(rec.pop("inferred_desorption"), dtype=float)
        correlation = uptake.corr(wc, method="spearman") if len(uptake) > 1 else np.nan
        rows.append({
            "process": process,
            **rec,
            "fraction_wc_greater_than_uptake": (
                rec["wc_greater_than_uptake"] / rec["complete"]
                if rec["complete"] else np.nan
            ),
            "minimum_inferred_desorption_loading": des.min() if len(des) else np.nan,
            "median_inferred_desorption_loading": des.median() if len(des) else np.nan,
            "maximum_inferred_desorption_loading": des.max() if len(des) else np.nan,
            "spearman_uptake_vs_working_capacity": correlation,
            "identity_consistent_with_wc_equals_uptake_minus_low_loading": bool(
                rec["negative_inferred_desorption"] == 0
            ),
        })

    numeric = pd.DataFrame(rows)
    numeric.to_csv(NUMERIC_OUTPUT, index=False)

    text_hits = text_formula_hits()
    if text_hits.empty:
        text_hits = pd.DataFrame(
            columns=["file", "line", "matched_text", "context"]
        )
    text_hits.to_csv(TEXT_OUTPUT, index=False)

    all_identity_consistent = bool(
        numeric["identity_consistent_with_wc_equals_uptake_minus_low_loading"].all()
    )

    manifest = {
        "stage": "Working-capacity provenance audit",
        "process_input": str(PROCESS_INPUT),
        "process_input_sha256": sha256(PROCESS_INPUT),
        "rows": total_rows,
        "processes": numeric["process"].tolist(),
        "text_formula_hits": int(len(text_hits)),
        "all_processes_numerically_consistent_with_uptake_minus_low_loading": (
            all_identity_consistent
        ),
        "n_jobs": N_JOBS,
        "scientific_values_changed": False,
        "chemistry_effects_estimated": False,
        "missing_values_filled": False,
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
    }
    MANIFEST_OUTPUT.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

    print()
    print(
        f"N_JOBS={N_JOBS}; serial provenance audit; parallel processing would "
        "not improve a single-file scan"
    )
    print()
    print("WORKING-CAPACITY NUMERICAL PROVENANCE")
    print(numeric.to_string(index=False))
    print()
    print("LOCAL FORMULA EVIDENCE")
    if text_hits.empty:
        print("No formula-bearing text file was found locally.")
    else:
        print(text_hits[["file", "line", "matched_text"]].to_string(index=False))
    print()
    print("Outputs:")
    for path in [NUMERIC_OUTPUT, TEXT_OUTPUT, MANIFEST_OUTPUT]:
        print(path)
    print(
        "No process value or chemistry result was changed. Numerical identity "
        "evidence must be combined with any formula-bearing source text before "
        "the manuscript interpretation is frozen."
    )


if __name__ == "__main__":
    main()

