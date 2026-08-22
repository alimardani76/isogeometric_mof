#!/usr/bin/env python3
"""Audit ARC-MOF process fields separately for each process.

Purpose
-------
Separate three states before any matched process analysis:
1. observed and physically valid;
2. observed but nonphysical;
3. missing or not applicable.

The script does not estimate chemistry-associated process differences, alter
matched pairs, repair negative values, or fill missing values.
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
ANALYSIS = ROOT / "analysis"
RAW = ROOT / "raw"

PROCESS_INPUT = RAW / "overall_process.csv"
PRIMARY_PAIRS_INPUT = ANALYSIS / "final_primary_pairs.parquet"

VALIDITY_OUTPUT = ANALYSIS / "process_by_process_validity.csv"
COVERAGE_OUTPUT = ANALYSIS / "process_endpoint_coverage.csv"
INVALID_OUTPUT = ANALYSIS / "process_invalid_observed_rows.csv"
MISSING_PRIMARY_OUTPUT = ANALYSIS / "primary_pair_frameworks_without_process.csv"
MANIFEST_OUTPUT = ANALYSIS / "process_by_process_manifest.json"

N_JOBS = 1
CHUNK_SIZE = 250_000
MAX_INVALID_ROWS_PER_PROCESS_FIELD = 100

ENDPOINTS = {
    "mmol/g_uptake": "uptake",
    "mmol/g_working_capacity": "working_capacity",
    "v/v_uptake": "uptake",
    "v/v_working_capacity": "working_capacity",
    "wt%_uptake": "uptake",
    "wt%_working_capacity": "working_capacity",
    "selectivity": "selectivity",
    "purity": "purity",
    "ssp": "ssp",
    "afm": "afm",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_id(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"(?i)\.cif$", "", regex=True)
        .str.replace(r"(?i)_repeat$", "", regex=True)
    )


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def choose_column(columns, candidates, purpose):
    normalized = {normalize_name(column): column for column in columns}
    for candidate in candidates:
        key = normalize_name(candidate)
        if key in normalized:
            return normalized[key]
    raise ValueError(
        f"Could not identify {purpose}. Available columns:\n"
        + "\n".join(map(str, columns))
    )


def classify_values(values: pd.Series, endpoint_class: str):
    numeric = pd.to_numeric(values, errors="coerce")
    observed = numeric.notna()
    finite = observed & np.isfinite(numeric)
    missing = ~observed
    invalid = observed & ~np.isfinite(numeric)

    if endpoint_class in {
        "uptake",
        "working_capacity",
        "selectivity",
        "ssp",
        "afm",
    }:
        invalid = invalid | (finite & numeric.lt(0))

    if endpoint_class == "selectivity":
        invalid = invalid | (finite & numeric.le(0))

    if endpoint_class == "purity":
        invalid = invalid | (finite & (numeric.lt(0) | numeric.gt(1)))

    valid = observed & ~invalid
    return numeric, observed, missing, valid, invalid


def main() -> None:
    for path in [PROCESS_INPUT, PRIMARY_PAIRS_INPUT]:
        if not path.exists():
            raise FileNotFoundError(path)

    header = pd.read_csv(PROCESS_INPUT, nrows=0)
    columns = list(header.columns)
    id_column = choose_column(
        columns,
        ["filename", "mof_id", "name", "structure"],
        "framework identifier",
    )
    process_column = choose_column(
        columns,
        ["process", "process_name", "process condition", "application"],
        "process label",
    )

    endpoint_columns = [column for column in ENDPOINTS if column in columns]
    missing_expected = sorted(set(ENDPOINTS) - set(endpoint_columns))
    if missing_expected:
        raise ValueError(
            "Expected process endpoint columns are absent: "
            f"{missing_expected}\nAvailable columns:\n" + "\n".join(columns)
        )

    primary_pairs = pd.read_parquet(
        PRIMARY_PAIRS_INPUT,
        columns=["id_a", "id_b"],
    )
    primary_ids = set(canonical_id(primary_pairs["id_a"])) | set(
        canonical_id(primary_pairs["id_b"])
    )

    aggregate = {}
    process_ids = set()
    primary_ids_with_process = set()
    invalid_samples = []
    invalid_sample_counts = {}
    total_rows = 0

    usecols = [id_column, process_column] + endpoint_columns

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            PROCESS_INPUT,
            usecols=usecols,
            chunksize=CHUNK_SIZE,
            low_memory=False,
        ),
        start=1,
    ):
        total_rows += len(chunk)
        chunk["mof_id"] = canonical_id(chunk[id_column])
        chunk[process_column] = chunk[process_column].astype("string").str.strip()

        ids = set(chunk["mof_id"].dropna())
        process_ids.update(ids)
        primary_ids_with_process.update(ids & primary_ids)

        for process, group in chunk.groupby(process_column, dropna=False, sort=False):
            process_name = "<MISSING>" if pd.isna(process) else str(process)

            row_key = (process_name, "__rows__")
            row_record = aggregate.setdefault(
                row_key,
                {
                    "process": process_name,
                    "endpoint": "__rows__",
                    "endpoint_class": "row_count",
                    "rows": 0,
                    "unique_frameworks": set(),
                    "observed": 0,
                    "missing": 0,
                    "valid": 0,
                    "invalid": 0,
                    "negative": 0,
                    "zero": 0,
                    "minimum": np.inf,
                    "maximum": -np.inf,
                    "values": [],
                },
            )
            row_record["rows"] += len(group)
            row_record["unique_frameworks"].update(group["mof_id"].dropna())

            for endpoint in endpoint_columns:
                endpoint_class = ENDPOINTS[endpoint]
                numeric, observed, missing, valid, invalid = classify_values(
                    group[endpoint], endpoint_class
                )

                key = (process_name, endpoint)
                record = aggregate.setdefault(
                    key,
                    {
                        "process": process_name,
                        "endpoint": endpoint,
                        "endpoint_class": endpoint_class,
                        "rows": 0,
                        "unique_frameworks": set(),
                        "observed": 0,
                        "missing": 0,
                        "valid": 0,
                        "invalid": 0,
                        "negative": 0,
                        "zero": 0,
                        "minimum": np.inf,
                        "maximum": -np.inf,
                        "values": [],
                    },
                )
                record["rows"] += len(group)
                record["unique_frameworks"].update(group["mof_id"].dropna())
                record["observed"] += int(observed.sum())
                record["missing"] += int(missing.sum())
                record["valid"] += int(valid.sum())
                record["invalid"] += int(invalid.sum())
                record["negative"] += int((observed & numeric.lt(0)).sum())
                record["zero"] += int((observed & numeric.eq(0)).sum())

                valid_values = numeric.loc[valid]
                if not valid_values.empty:
                    record["minimum"] = min(
                        record["minimum"], float(valid_values.min())
                    )
                    record["maximum"] = max(
                        record["maximum"], float(valid_values.max())
                    )
                    step = max(1, len(valid_values) // 2000)
                    record["values"].extend(
                        valid_values.iloc[::step].head(2000).astype(float).tolist()
                    )
                    if len(record["values"]) > 10000:
                        record["values"] = record["values"][::2]

                if invalid.any():
                    sample_key = (process_name, endpoint)
                    already = invalid_sample_counts.get(sample_key, 0)
                    remaining = MAX_INVALID_ROWS_PER_PROCESS_FIELD - already
                    if remaining > 0:
                        sample = group.loc[
                            invalid,
                            [id_column, "mof_id", process_column, endpoint],
                        ].head(remaining).copy()
                        sample["endpoint_class"] = endpoint_class
                        sample["invalid_reason"] = np.where(
                            pd.to_numeric(sample[endpoint], errors="coerce").lt(0),
                            "negative_observed_value",
                            "outside_physical_range_or_nonfinite",
                        )
                        invalid_samples.append(sample)
                        invalid_sample_counts[sample_key] = already + len(sample)

        print(f"audited chunk={chunk_number}; cumulative_rows={total_rows:,}")

    rows = []
    for (process_name, endpoint), record in aggregate.items():
        if endpoint == "__rows__":
            continue
        values = pd.Series(record.pop("values"), dtype=float)
        rows.append(
            {
                "process": process_name,
                "endpoint": endpoint,
                "endpoint_class": record["endpoint_class"],
                "rows": record["rows"],
                "unique_frameworks": len(record["unique_frameworks"]),
                "observed": record["observed"],
                "missing": record["missing"],
                "valid": record["valid"],
                "invalid_observed": record["invalid"],
                "negative_observed": record["negative"],
                "zero_observed": record["zero"],
                "valid_fraction_of_rows": (
                    record["valid"] / record["rows"] if record["rows"] else np.nan
                ),
                "minimum_valid": (
                    record["minimum"] if np.isfinite(record["minimum"]) else np.nan
                ),
                "median_valid_sample": values.median() if len(values) else np.nan,
                "maximum_valid": (
                    record["maximum"] if np.isfinite(record["maximum"]) else np.nan
                ),
            }
        )

    validity = pd.DataFrame(rows).sort_values(
        ["process", "endpoint_class", "endpoint"]
    )
    validity.to_csv(VALIDITY_OUTPUT, index=False)

    coverage = (
        validity.groupby(["process", "endpoint_class"], as_index=False)
        .agg(
            endpoint_columns=("endpoint", "nunique"),
            rows=("rows", "max"),
            minimum_observed=("observed", "min"),
            minimum_valid=("valid", "min"),
            maximum_invalid_observed=("invalid_observed", "max"),
            maximum_missing=("missing", "max"),
        )
    )
    coverage.to_csv(COVERAGE_OUTPUT, index=False)

    if invalid_samples:
        invalid_frame = pd.concat(invalid_samples, ignore_index=True, sort=False)
    else:
        invalid_frame = pd.DataFrame(
            columns=[id_column, "mof_id", process_column, "endpoint_class", "invalid_reason"]
        )
    invalid_frame.to_csv(INVALID_OUTPUT, index=False)

    missing_primary = pd.DataFrame(
        {
            "mof_id": sorted(primary_ids - primary_ids_with_process)
        }
    )
    missing_primary.to_csv(MISSING_PRIMARY_OUTPUT, index=False)

    manifest = {
        "stage": "Process fields audited by process",
        "input": str(PROCESS_INPUT),
        "input_sha256": sha256(PROCESS_INPUT),
        "primary_pairs_input": str(PRIMARY_PAIRS_INPUT),
        "primary_pairs_sha256": sha256(PRIMARY_PAIRS_INPUT),
        "source_rows": total_rows,
        "processes": sorted(validity["process"].unique().tolist()),
        "endpoint_columns": endpoint_columns,
        "primary_pair_frameworks": len(primary_ids),
        "primary_pair_frameworks_with_process": len(primary_ids_with_process),
        "primary_pair_frameworks_without_process": len(
            primary_ids - primary_ids_with_process
        ),
        "n_jobs": N_JOBS,
        "chunk_size": CHUNK_SIZE,
        "missing_values_filled": False,
        "nonphysical_values_repaired": False,
        "process_effects_estimated": False,
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
    }
    MANIFEST_OUTPUT.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print()
    print(
        f"N_JOBS={N_JOBS}; serial chunked audit; parallel reading would add "
        "disk contention without scientific benefit"
    )
    print()
    print("PROCESS-BY-PROCESS VALIDITY")
    print(
        validity[
            [
                "process",
                "endpoint",
                "observed",
                "missing",
                "valid",
                "invalid_observed",
                "negative_observed",
                "minimum_valid",
                "median_valid_sample",
                "maximum_valid",
            ]
        ].to_string(index=False)
    )

    print()
    print("PRIMARY-PAIR PROCESS COVERAGE")
    print(
        pd.DataFrame(
            [
                {
                    "metric": "primary_pair_frameworks",
                    "value": len(primary_ids),
                },
                {
                    "metric": "with_process_records",
                    "value": len(primary_ids_with_process),
                },
                {
                    "metric": "without_process_records",
                    "value": len(primary_ids - primary_ids_with_process),
                },
            ]
        ).to_string(index=False)
    )

    print()
    print("Outputs:")
    for path in [
        VALIDITY_OUTPUT,
        COVERAGE_OUTPUT,
        INVALID_OUTPUT,
        MISSING_PRIMARY_OUTPUT,
        MANIFEST_OUTPUT,
    ]:
        print(path)

    print(
        "Missing or nonapplicable values were counted separately from observed "
        "nonphysical values. No process value was filled or repaired."
    )


if __name__ == "__main__":
    main()

