#!/usr/bin/env python3
"""Step 5A: freeze one numerically consistent primary pair catalogue.

Purpose
-------
Promote the already calculated primary tier from the fixed-caliper sensitivity
run into one publication source of truth. This script does not search for new
pairs, change chemistry rules, inspect adsorption outcomes, or recalculate
CrystalNN. It validates the expected counts and writes a frozen catalogue plus
an explicit count dictionary and manifest.

Required input
--------------
analysis/caliper_sensitivity_pair_assignments.parquet

Expected primary raw counts
---------------------------
metal_substitution          674
linker_family_change      12,392
functional_motif_change       6

Outputs
-------
analysis/final_primary_pairs.parquet
analysis/final_primary_pair_counts.csv
analysis/final_primary_pair_manifest.json
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import platform

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"

INPUT = ANALYSIS / "caliper_sensitivity_pair_assignments.parquet"
DEPENDENCE_LEDGER_INPUT = (
    ANALYSIS / "stringent_pair_dependence_ledger.parquet"
)

OUTPUT = ANALYSIS / "final_primary_pairs.parquet"
COUNT_OUTPUT = ANALYSIS / "final_primary_pair_counts.csv"
MANIFEST_OUTPUT = ANALYSIS / "final_primary_pair_manifest.json"

N_JOBS = 1
NUMERICAL_TOLERANCE = 1e-12

EXPECTED = {
    "metal_substitution": 674,
    "linker_family_change": 12392,
    "functional_motif_change": 6,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def choose_column(columns, candidates, purpose):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    raise ValueError(
        f"Could not identify {purpose}. Available columns:\n"
        + "\n".join(map(str, columns))
    )


def canonical_pair_key(frame: pd.DataFrame) -> pd.Series:
    lo = frame[["id_a", "id_b"]].min(axis=1).astype("string")
    hi = frame[["id_a", "id_b"]].max(axis=1).astype("string")
    return lo + " || " + hi


def main() -> None:
    if not INPUT.exists():
        raise FileNotFoundError(INPUT)

    if not DEPENDENCE_LEDGER_INPUT.exists():
        raise FileNotFoundError(DEPENDENCE_LEDGER_INPUT)

    pairs = pd.read_parquet(INPUT)

    tier_column = choose_column(
        pairs.columns,
        ["tier", "geometry_tier", "match_tier"],
        "geometry-tier column",
    )

    required = {"id_a", "id_b", "intervention", tier_column}
    missing = sorted(required - set(pairs.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    primary = pairs.loc[
        pairs[tier_column].astype("string").str.lower().eq("primary")
    ].copy()

    if primary.empty:
        raise RuntimeError("No rows were labelled as the primary tier")

    if primary[["id_a", "id_b", "intervention"]].isna().any().any():
        raise RuntimeError("Primary catalogue contains missing pair identifiers")

    primary["pair_key"] = canonical_pair_key(primary)

    duplicated = primary.duplicated(
        ["pair_key", "intervention"], keep=False
    )
    if duplicated.any():
        example = primary.loc[
            duplicated,
            ["id_a", "id_b", "intervention", "pair_key"],
        ].head(20)
        raise RuntimeError(
            "Duplicate unordered raw pairs detected in the primary catalogue:\n"
            + example.to_string(index=False)
        )

    counts = (
        primary.groupby("intervention", dropna=False)
        .agg(
            raw_pairs=("pair_key", "size"),
            unique_pair_keys=("pair_key", "nunique"),
            unique_frameworks_a=("id_a", "nunique"),
            unique_frameworks_b=("id_b", "nunique"),
        )
        .reset_index()
    )

    observed = dict(zip(counts["intervention"], counts["raw_pairs"]))

    if observed != EXPECTED:
        raise RuntimeError(
            "Primary counts do not match the frozen expected counts.\n"
            f"Expected: {EXPECTED}\nObserved: {observed}\n"
            "Do not continue to adsorption summaries until this is resolved."
        )

    if len(primary) != sum(EXPECTED.values()):
        raise RuntimeError(
            f"Expected {sum(EXPECTED.values()):,} total rows; "
            f"found {len(primary):,}"
        )

    dependence = pd.read_parquet(
        DEPENDENCE_LEDGER_INPUT,
        columns=[
            "id_a",
            "id_b",
            "intervention",
            "geometry_tier",
        ],
    )

    dependence = dependence.loc[
        dependence["geometry_tier"].astype("string").str.lower().eq(
            "stringent"
        )
    ].copy()

    dependence["pair_key"] = canonical_pair_key(dependence)

    primary_keys = set(
        zip(
            primary["intervention"].astype(str),
            primary["pair_key"].astype(str),
        )
    )

    dependence_keys = set(
        zip(
            dependence["intervention"].astype(str),
            dependence["pair_key"].astype(str),
        )
    )

    only_in_primary = sorted(primary_keys - dependence_keys)
    only_in_dependence = sorted(dependence_keys - primary_keys)

    if only_in_primary or only_in_dependence:
        raise RuntimeError(
            "The primary caliper catalogue and stringent dependence "
            "ledger contain different pair keys.\n"
            f"Only in primary catalogue: {len(only_in_primary)}\n"
            f"Only in dependence ledger: {len(only_in_dependence)}\n"
            f"Primary-only examples: {only_in_primary[:10]}\n"
            f"Dependence-only examples: {only_in_dependence[:10]}"
        )

    primary = primary.sort_values(
        ["intervention", "pair_key"], kind="mergesort"
    ).reset_index(drop=True)

    primary.to_parquet(OUTPUT, index=False)
    counts.to_csv(COUNT_OUTPUT, index=False)

    manifest = {
        "stage": "Step 5A - frozen primary pair catalogue",
        "input": str(INPUT),
        "input_sha256": sha256(INPUT),
        "dependence_ledger_input": str(DEPENDENCE_LEDGER_INPUT),
        "dependence_ledger_sha256": sha256(
            DEPENDENCE_LEDGER_INPUT
        ),
        "primary_and_dependence_pair_keys_identical": True,
        "output": str(OUTPUT),
        "output_sha256": sha256(OUTPUT),
        "count_output": str(COUNT_OUTPUT),
        "tier_column": tier_column,
        "tier_value": "primary",
        "numerical_tolerance": NUMERICAL_TOLERANCE,
        "expected_raw_counts": EXPECTED,
        "observed_raw_counts": observed,
        "total_raw_pairs": int(len(primary)),
        "adsorption_outcomes_read": False,
        "chemistry_rules_changed": False,
        "geometry_limits_changed": False,
        "crystalnn_rerun": False,
        "missing_values_filled": False,
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "n_jobs": N_JOBS,
    }

    MANIFEST_OUTPUT.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(
        f"N_JOBS={N_JOBS}; vectorized validation; "
        "parallel processing would not help"
    )
    print()
    print("FINAL PRIMARY PAIR CATALOGUE")
    print(counts.to_string(index=False))
    print()
    print("Total raw pairs:", f"{len(primary):,}")
    print("Saved catalogue:", OUTPUT)
    print("Saved counts:", COUNT_OUTPUT)
    print("Saved manifest:", MANIFEST_OUTPUT)
    print(
        "Adsorption outcomes were not read. No pair was searched, added from "
        "outcomes, or removed for its result. No missing value was filled."
    )


if __name__ == "__main__":
    main()

