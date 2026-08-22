#!/usr/bin/env python3
"""Step 4 of 5: identify boundary cases and audit CIF text/disorder quality.

Purpose
-------
Create a compact, reproducible record of the localized cases where:
1. full-support and reciprocal matching disagree on pressure direction;
2. the topology-agreement subset disagrees with the full analysis;
3. chemistry-change magnitudes fall below the same-chemistry control baseline;
4. CIF decoding or crystallographic disorder could limit interpretation.

This script does not change pairs, thresholds, outcomes, or claims. It reads no
raw adsorption CSV and fits no model.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path
import io
import tarfile

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
RAW = ROOT / "raw"

MATCHING_FILE = ANALYSIS / "matching_design_comparison.csv"
TOPOLOGY_FILE = ANALYSIS / "step1_topology_robustness_comparison.csv"
CONTROL_FILE = (
    ANALYSIS / "step5b_symmetric_control_results.csv"
)
DESIGN_FILE = (
    ANALYSIS / "step5b_symmetric_control_design.parquet"
)
CHEMISTRY_FILE = ANALYSIS / "cif_chemistry.parquet"
ARCHIVE_FILE = RAW / "ARCMOF_20241004.tar.gz"

MATCHING_OUT = ANALYSIS / "step4_matching_disagreements.csv"
TOPOLOGY_OUT = ANALYSIS / "step4_topology_disagreements.csv"
CONTROL_OUT = ANALYSIS / "step4_control_boundary_conditions.csv"
CIF_OUT = ANALYSIS / "step4_cif_quality_for_primary_pairs.csv"
SUMMARY_OUT = ANALYSIS / "step4_boundary_summary.csv"

N_JOBS = 6
MAX_PENDING = 12


def canonical_member_id(name: str) -> str:
    basename = Path(name).name.strip()
    if basename.lower().endswith(".cif"):
        basename = basename[:-4]
    if basename.lower().endswith("_repeat"):
        basename = basename[:-7]
    return basename


def disagreement_rows(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path, low_memory=False)
    agreement_columns = [
        column for column in frame.columns
        if column.lower().startswith("same_")
        or column.lower().endswith("_agreement")
        or "same_direction" in column.lower()
    ]
    if not agreement_columns:
        raise ValueError(
            f"No agreement columns found in {path.name}. "
            f"Available columns: {list(frame.columns)}"
        )
    mask = pd.Series(False, index=frame.index)
    for column in agreement_columns:
        values = frame[column]
        if values.dtype == bool:
            agreed = values
        else:
            agreed = (
                values.astype("string").str.strip().str.lower()
                .map({"true": True, "false": False, "1": True, "0": False})
            )
        mask |= agreed.eq(False)
    result = frame.loc[mask].copy()
    result["disagreement_columns"] = result.apply(
        lambda row: ";".join(
            column for column in agreement_columns
            if str(row[column]).strip().lower() in {"false", "0"}
        ),
        axis=1,
    )
    return result


def decode_cif(payload):
    mof_id, raw_bytes = payload
    try:
        raw_bytes.decode("utf-8", errors="strict")
        return {
            "mof_id": mof_id,
            "strict_utf8_decode_ok": True,
            "decode_error": "",
        }
    except UnicodeDecodeError as error:
        return {
            "mof_id": mof_id,
            "strict_utf8_decode_ok": False,
            "decode_error": (
                f"UnicodeDecodeError at byte {error.start}: {error.reason}"
            ),
        }


def audit_strict_decoding(wanted_ids: set[str]) -> pd.DataFrame:
    records = []
    found = set()
    with tarfile.open(ARCHIVE_FILE, "r:gz") as archive, ProcessPoolExecutor(
        max_workers=N_JOBS
    ) as executor:
        pending = {}

        def collect_done(block=False):
            nonlocal pending
            if not pending:
                return
            done, _ = wait(
                pending,
                return_when=None if block else FIRST_COMPLETED,
            )
            for future in done:
                records.append(future.result())
                pending.pop(future, None)

        for member in archive:
            if not member.isfile() or not member.name.lower().endswith(".cif"):
                continue
            mof_id = canonical_member_id(member.name)
            if mof_id not in wanted_ids:
                continue
            handle = archive.extractfile(member)
            if handle is None:
                continue
            found.add(mof_id)
            future = executor.submit(decode_cif, (mof_id, handle.read()))
            pending[future] = mof_id
            if len(pending) >= MAX_PENDING:
                collect_done(block=False)

        while pending:
            collect_done(block=False)

    missing = sorted(wanted_ids - found)
    records.extend(
        {
            "mof_id": mof_id,
            "strict_utf8_decode_ok": False,
            "decode_error": "archive_member_missing",
        }
        for mof_id in missing
    )
    return pd.DataFrame(records)


def main():
    required = [
        MATCHING_FILE, TOPOLOGY_FILE, CONTROL_FILE,
        DESIGN_FILE, CHEMISTRY_FILE, ARCHIVE_FILE,
    ]
    for path in required:
        if not path.exists():
            raise FileNotFoundError(path)

    matching = disagreement_rows(MATCHING_FILE)
    topology = disagreement_rows(TOPOLOGY_FILE)
    matching.to_csv(MATCHING_OUT, index=False)
    topology.to_csv(TOPOLOGY_OUT, index=False)

    controls = pd.read_csv(CONTROL_FILE, low_memory=False)
    required_control = [
        "intervention", "effect_measure", "target", "T/K", "p/bar",
        "median_chemistry_minus_control", "bootstrap_95_low", "bootstrap_95_high",
    ]
    missing = [column for column in required_control if column not in controls.columns]
    if missing:
        raise ValueError(f"Control result missing columns: {missing}")
    control_boundaries = controls.loc[
        (controls["bootstrap_95_high"] < 0)
        | (controls["bootstrap_95_low"] <= 0)
    ].copy()
    control_boundaries["control_status"] = "interval_crosses_zero"
    control_boundaries.loc[
        control_boundaries["bootstrap_95_high"] < 0,
        "control_status",
    ] = "interval_below_control"
    control_boundaries.to_csv(CONTROL_OUT, index=False)

    design = pd.read_parquet(DESIGN_FILE)
    primary = design.loc[design["design_type"].eq("chemistry_change")].copy()
    wanted_ids = set(primary["id_a"].astype(str)) | set(primary["id_b"].astype(str))

    chemistry_columns = [
        "mof_id", "parse_ok", "n_disordered_sites",
        "charge_length_aligned", "charge_numeric_fraction",
        "element_sets_match",
    ]
    available_columns = pd.read_parquet(CHEMISTRY_FILE, engine="pyarrow").columns
    selected_columns = [column for column in chemistry_columns if column in available_columns]
    chemistry = pd.read_parquet(CHEMISTRY_FILE, columns=selected_columns)
    chemistry = chemistry.loc[chemistry["mof_id"].astype(str).isin(wanted_ids)].copy()

    decoding = audit_strict_decoding(wanted_ids)
    cif_quality = pd.DataFrame({"mof_id": sorted(wanted_ids)}).merge(
        chemistry,
        on="mof_id",
        how="left",
        validate="one_to_one",
    ).merge(
        decoding,
        on="mof_id",
        how="left",
        validate="one_to_one",
    )

    if "n_disordered_sites" in cif_quality.columns:
        cif_quality["has_disordered_sites"] = (
            pd.to_numeric(cif_quality["n_disordered_sites"], errors="coerce") > 0
        )
    else:
        cif_quality["has_disordered_sites"] = pd.NA

    cif_quality.to_csv(CIF_OUT, index=False)

    summary = pd.DataFrame(
        [
            {
                "check": "matching_design_disagreements",
                "records": len(matching),
                "interpretation": "localized full-support versus reciprocal disagreements",
            },
            {
                "check": "topology_filter_disagreements",
                "records": len(topology),
                "interpretation": "localized full versus topology-agreement disagreements",
            },
            {
                "check": "control_intervals_below_baseline",
                "records": int((control_boundaries["control_status"] == "interval_below_control").sum()),
                "interpretation": "reciprocal chemistry-change magnitude reliably below reciprocal same-chemistry control",
            },
            {
                "check": "control_intervals_crossing_zero",
                "records": int((control_boundaries["control_status"] == "interval_crosses_zero").sum()),
                "interpretation": "control-relative result not clearly separated from zero",
            },
            {
                "check": "primary_pair_frameworks",
                "records": len(wanted_ids),
                "interpretation": "frameworks in primary common-support chemistry comparisons",
            },
            {
                "check": "strict_utf8_decode_failures",
                "records": int((~cif_quality["strict_utf8_decode_ok"].fillna(False)).sum()),
                "interpretation": "CIFs requiring non-strict text replacement or missing archive members",
            },
            {
                "check": "frameworks_with_disordered_sites",
                "records": int(cif_quality["has_disordered_sites"].fillna(False).sum()),
                "interpretation": "parsed structures containing partial/disordered sites",
            },
        ]
    )
    summary.to_csv(SUMMARY_OUT, index=False)

    print(
        f"N_JOBS={N_JOBS}; primary_pair_frameworks={len(wanted_ids):,}; "
        f"strict_decode_audit={len(cif_quality):,}"
    )
    print("\nSTEP 4 BOUNDARY SUMMARY")
    print(summary.to_string(index=False))

    print("\nMATCHING-DESIGN DISAGREEMENTS")
    print(matching.to_string(index=False) if len(matching) else "NONE")

    print("\nTOPOLOGY-FILTER DISAGREEMENTS")
    print(topology.to_string(index=False) if len(topology) else "NONE")

    below = control_boundaries.loc[
        control_boundaries["control_status"].eq("interval_below_control")
    ]
    print("\nCONTROL INTERVALS ENTIRELY BELOW BASELINE")
    print(below.to_string(index=False) if len(below) else "NONE")

    print("\nOutputs:")
    print(MATCHING_OUT)
    print(TOPOLOGY_OUT)
    print(CONTROL_OUT)
    print(CIF_OUT)
    print(SUMMARY_OUT)
    print(
        "No pair, threshold, adsorption value, or claim was changed. "
        "No model or missing-value filling was used."
    )


if __name__ == "__main__":
    main()

