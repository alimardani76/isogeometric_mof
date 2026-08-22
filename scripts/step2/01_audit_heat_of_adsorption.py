#!/usr/bin/env python3
"""
Project 7B2 Step 2: heat-of-adsorption viability audit.

Run from the Project 7B2 main folder:
    python 26_audit_heat_of_adsorption.py

Reads only existing frozen data. Does not modify 7B1 outputs, impute values,
or estimate a heat/adsorption relationship.

Required:
    analysis/final_primary_pair_effect_magnitudes.parquet
    raw/*.csv adsorption files containing hoa/kcal/mol

Outputs under the project-root folder Step 2 results/heat_audit/:
    7B2_heat_source_coverage.csv
    7B2_heat_pair_coverage.csv
    7B2_heat_group_support.csv
    7B2_heat_unmatched_targets.csv
    7B2_heat_viability_report.txt
    7B2_heat_audit_manifest.json
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

STEP2 = Path(__file__).resolve().parent
ROOT = STEP2.parent
ANALYSIS = ROOT / "analysis"
RAW = ROOT / "raw"
EFFECTS = ANALYSIS / "final_primary_pair_effect_magnitudes.parquet"
RESULTS = ROOT / "Step 2 results"
OUT = RESULTS / "heat_audit"
OUT.mkdir(parents=True, exist_ok=True)

N_JOBS = 1  # Chunked sequential I/O avoids disk contention across ~100 MB CSV files.
CHUNKSIZE = 200_000
REQ_RAW = ["filename", "T/K", "p/bar", "hoa/kcal/mol", "stdev.3"]
KEY = ["mof_id", "target", "T/K", "p/bar"]
PAIR_KEY = ["pair_key", "target", "T/K", "p/bar"]


def canonical_id(values: pd.Series) -> pd.Series:
    return (
        values.astype("string")
        .str.strip()
        .str.replace(r"(?i)\.cif$", "", regex=True)
        .str.replace(r"(?i)_repeat$", "", regex=True)
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


RAW_TARGET_MAP = {
    "landfill-CH4": "landfill_CH4",
    "landfill-CO2": "landfill_CO2",
    "methane_purification-CH4": "methane_purification_CH4",
    "methane_purification-CO2": "methane_purification_CO2",
    "methane": "methane_storage_CH4",
    "post_comb_vsa-CO2": "post_combustion_CO2",
    "post_comb_vsa-N2": "post_combustion_N2",
    "pre_comb_4040-CO2": "pre_combustion_CO2",
    "pre_comb_4040-H2": "pre_combustion_H2",
}


def raw_target(path: Path) -> str:
    try:
        return RAW_TARGET_MAP[path.stem]
    except KeyError as exc:
        raise KeyError(f"No frozen target mapping defined for raw file: {path.name}") from exc


def find_adsorption_files() -> list[Path]:
    files = []
    for p in sorted(RAW.glob("*.csv")):
        try:
            cols = pd.read_csv(p, nrows=0).columns.tolist()
        except Exception:
            continue
        if all(c in cols for c in REQ_RAW):
            files.append(p)
    return files


def main() -> None:
    if not EFFECTS.exists():
        raise FileNotFoundError(f"Missing frozen input: {EFFECTS}")
    if not RAW.exists():
        raise FileNotFoundError(f"Missing raw directory: {RAW}")

    effect_cols = [
        "id_a", "id_b", "intervention", "dependence_family_id",
        "target", "T/K", "p/bar", "outcome_complete"
    ]
    effects = pd.read_parquet(EFFECTS, columns=effect_cols)
    effects["id_a"] = canonical_id(effects["id_a"])
    effects["id_b"] = canonical_id(effects["id_b"])
    effects["target"] = effects["target"].astype("string")
    effects["T/K"] = pd.to_numeric(effects["T/K"], errors="coerce")
    effects["p/bar"] = pd.to_numeric(effects["p/bar"], errors="coerce")
    effects["pair_key"] = np.where(
        effects["id_a"] <= effects["id_b"],
        effects["id_a"] + " || " + effects["id_b"],
        effects["id_b"] + " || " + effects["id_a"],
    )

    endpoint_ids = set(effects["id_a"].dropna()) | set(effects["id_b"].dropna())
    frozen_targets = set(effects["target"].dropna().astype(str).unique())
    raw_files = find_adsorption_files()
    if not raw_files:
        raise RuntimeError("No raw adsorption CSV containing hoa/kcal/mol and stdev.3 was found")

    source_rows = []
    retained_parts = []
    unmatched = []

    for path in raw_files:
        target = raw_target(path)
        if target not in frozen_targets:
            unmatched.append({
                "raw_file": path.name,
                "derived_target": target,
                "reason": "filename stem not present in frozen effect target values",
            })

        total = observed = numeric = valid_sd = relevant = 0
        for chunk in pd.read_csv(path, usecols=REQ_RAW, chunksize=CHUNKSIZE, low_memory=False):
            total += len(chunk)
            hoa_num = pd.to_numeric(chunk["hoa/kcal/mol"], errors="coerce")
            sd_num = pd.to_numeric(chunk["stdev.3"], errors="coerce")
            observed += int(chunk["hoa/kcal/mol"].notna().sum())
            numeric += int(hoa_num.notna().sum())
            valid_sd += int((sd_num.notna() & (sd_num > 0)).sum())

            chunk["mof_id"] = canonical_id(chunk["filename"])
            chunk = chunk.loc[chunk["mof_id"].isin(endpoint_ids), ["mof_id", "T/K", "p/bar"]].copy()
            if chunk.empty:
                continue
            relevant += len(chunk)
            # Re-read selected values by index from original arrays.
            idx = chunk.index
            chunk["target"] = target
            chunk["hoa"] = hoa_num.loc[idx].to_numpy()
            chunk["hoa_stdev"] = sd_num.loc[idx].to_numpy()
            chunk["hoa_observed"] = chunk["hoa"].notna()
            chunk["hoa_stdev_valid"] = chunk["hoa_stdev"].notna() & (chunk["hoa_stdev"] > 0)
            chunk["T/K"] = pd.to_numeric(chunk["T/K"], errors="coerce")
            chunk["p/bar"] = pd.to_numeric(chunk["p/bar"], errors="coerce")
            retained_parts.append(chunk)

        source_rows.append({
            "raw_file": path.name,
            "target": target,
            "rows": total,
            "hoa_observed": observed,
            "hoa_numeric": numeric,
            "hoa_valid_stdev": valid_sd,
            "hoa_numeric_fraction": numeric / total if total else np.nan,
            "hoa_valid_stdev_fraction": valid_sd / total if total else np.nan,
            "rows_for_primary_pair_endpoints": relevant,
        })

    source_df = pd.DataFrame(source_rows)
    source_df.to_csv(OUT / "7B2_heat_source_coverage.csv", index=False)
    pd.DataFrame(unmatched, columns=["raw_file", "derived_target", "reason"]).to_csv(
        OUT / "7B2_heat_unmatched_targets.csv", index=False
    )

    heat = pd.concat(retained_parts, ignore_index=True) if retained_parts else pd.DataFrame()
    if heat.empty:
        raise RuntimeError("No raw heat rows matched primary-pair endpoint framework IDs")

    duplicate_mask = heat.duplicated(KEY, keep=False)
    duplicate_keys = int(heat.loc[duplicate_mask, KEY].drop_duplicates().shape[0])
    if duplicate_keys:
        # Never silently average duplicate scientific rows.
        dup_path = OUT / "7B2_heat_duplicate_keys.csv"
        heat.loc[duplicate_mask].sort_values(KEY).to_csv(dup_path, index=False)
        raise RuntimeError(
            f"Found {duplicate_keys} duplicate framework-condition heat keys. "
            f"Inspect {dup_path}; no aggregation was performed."
        )

    a = heat.rename(columns={
        "mof_id": "id_a", "hoa": "hoa_a", "hoa_stdev": "hoa_stdev_a",
        "hoa_observed": "hoa_observed_a", "hoa_stdev_valid": "hoa_stdev_valid_a"
    }).drop(columns=["filename"], errors="ignore")
    b = heat.rename(columns={
        "mof_id": "id_b", "hoa": "hoa_b", "hoa_stdev": "hoa_stdev_b",
        "hoa_observed": "hoa_observed_b", "hoa_stdev_valid": "hoa_stdev_valid_b"
    }).drop(columns=["filename"], errors="ignore")

    merged = effects.merge(a, on=["id_a", "target", "T/K", "p/bar"], how="left", validate="many_to_one")
    merged = merged.merge(b, on=["id_b", "target", "T/K", "p/bar"], how="left", validate="many_to_one")
    merged["hoa_pair_complete"] = merged["hoa_a"].notna() & merged["hoa_b"].notna()
    valid_a = merged["hoa_stdev_valid_a"].eq(True)
    valid_b = merged["hoa_stdev_valid_b"].eq(True)
    merged["hoa_both_stdev_valid"] = valid_a & valid_b
    merged["absolute_hoa_difference"] = np.where(
        merged["hoa_pair_complete"], (merged["hoa_b"] - merged["hoa_a"]).abs(), np.nan
    )

    pair_summary = (
        merged.groupby(["intervention", "target", "T/K", "p/bar"], dropna=False)
        .agg(
            expected_pair_rows=("pair_key", "size"),
            unique_pairs=("pair_key", "nunique"),
            hoa_complete_pair_rows=("hoa_pair_complete", "sum"),
            both_stdev_valid_pair_rows=("hoa_both_stdev_valid", "sum"),
            groups_expected=("dependence_family_id", "nunique"),
            groups_with_complete_hoa=("dependence_family_id", lambda s: s[merged.loc[s.index, "hoa_pair_complete"]].nunique()),
            hoa_a_min=("hoa_a", "min"),
            hoa_a_median=("hoa_a", "median"),
            hoa_a_max=("hoa_a", "max"),
            hoa_b_min=("hoa_b", "min"),
            hoa_b_median=("hoa_b", "median"),
            hoa_b_max=("hoa_b", "max"),
            median_absolute_hoa_difference=("absolute_hoa_difference", "median"),
        )
        .reset_index()
    )
    pair_summary["hoa_pair_coverage"] = (
        pair_summary["hoa_complete_pair_rows"] / pair_summary["expected_pair_rows"]
    )
    pair_summary["hoa_stdev_pair_coverage"] = (
        pair_summary["both_stdev_valid_pair_rows"] / pair_summary["expected_pair_rows"]
    )
    pair_summary.to_csv(OUT / "7B2_heat_pair_coverage.csv", index=False)

    group_support = (
        merged.loc[merged["hoa_pair_complete"]]
        .groupby(["intervention", "target", "T/K", "p/bar"], dropna=False)
        .agg(
            complete_pair_rows=("pair_key", "size"),
            unique_pairs=("pair_key", "nunique"),
            related_groups=("dependence_family_id", "nunique"),
            hoa_unique_values_a=("hoa_a", "nunique"),
            hoa_unique_values_b=("hoa_b", "nunique"),
            absolute_hoa_difference_q1=("absolute_hoa_difference", lambda x: x.quantile(0.25)),
            absolute_hoa_difference_median=("absolute_hoa_difference", "median"),
            absolute_hoa_difference_q3=("absolute_hoa_difference", lambda x: x.quantile(0.75)),
        )
        .reset_index()
    )
    group_support.to_csv(OUT / "7B2_heat_group_support.csv", index=False)

    # Conservative viability decision. This is a gate, not a scientific result.
    linker = pair_summary.loc[pair_summary["intervention"].eq("linker_family_change")]
    metal = pair_summary.loc[pair_summary["intervention"].eq("metal_substitution")]
    linker_good = linker.loc[(linker["hoa_pair_coverage"] >= 0.80) & (linker["groups_with_complete_hoa"] >= 100)]
    metal_good = metal.loc[(metal["hoa_pair_coverage"] >= 0.80) & (metal["groups_with_complete_hoa"] >= 30)]
    varied = group_support.loc[
        (group_support["hoa_unique_values_a"] > 20) &
        (group_support["hoa_unique_values_b"] > 20) &
        (group_support["absolute_hoa_difference_q3"] > group_support["absolute_hoa_difference_q1"])
    ]

    if unmatched:
        decision = "PARTIAL"
        reason = "One or more raw filename-derived targets did not match frozen target labels. Resolve mapping before analysis."
    elif len(linker_good) >= 6 and len(varied.loc[varied["intervention"].eq("linker_family_change")]) >= 6:
        decision = "PASS"
        reason = "Linker heat coverage, related-group support, and value variation are adequate in multiple conditions."
    elif pair_summary["hoa_complete_pair_rows"].sum() == 0:
        decision = "FAIL"
        reason = "No frozen pair-condition row has observed heat at both endpoints."
    else:
        decision = "PARTIAL"
        reason = "Observed paired heat exists, but coverage/support/variation does not meet the conservative linker gate broadly."

    report = []
    report.append("PROJECT 7B2 HEAT-OF-ADSORPTION VIABILITY AUDIT")
    report.append("=" * 72)
    report.append(f"Decision: {decision}")
    report.append(f"Reason: {reason}")
    report.append(f"Frozen effect rows: {len(effects):,}")
    report.append(f"Frozen unique pairs: {effects['pair_key'].nunique():,}")
    report.append(f"Raw adsorption files audited: {len(raw_files)}")
    report.append(f"Raw-to-frozen unmatched target files: {len(unmatched)}")
    report.append(f"Complete paired heat rows: {int(merged['hoa_pair_complete'].sum()):,}")
    report.append(f"Rows with valid heat uncertainty at both endpoints: {int(merged['hoa_both_stdev_valid'].sum()):,}")
    report.append("")
    report.append("Conditions meeting conservative coverage/support gate:")
    report.append(f"  Linker: {len(linker_good)}")
    report.append(f"  Metal: {len(metal_good)}")
    report.append(f"  Conditions with clear observed heat variation: {len(varied)}")
    report.append("")
    report.append("Interpretation boundary:")
    report.append("  This audit establishes only whether observed heat values can support a new matched analysis.")
    report.append("  It does not estimate mechanism, correlation, direction, or causality.")
    report.append("  No missing heat value was filled and no duplicate key was averaged.")
    report.append("")
    report.append("Next action:")
    if decision == "PASS":
        report.append("  Permit one prespecified matched heat-contrast analysis focused on linker pairs and H4.")
    elif decision == "PARTIAL":
        report.append("  Inspect 7B2_heat_pair_coverage.csv. Proceed only for explicitly supported conditions.")
    else:
        report.append("  Stop heat analysis and move to residual-geometry-adjusted sensitivity.")
    (OUT / "7B2_heat_viability_report.txt").write_text("\n".join(report), encoding="utf-8", newline="\n")

    manifest = {
        "stage": "7B2 heat-of-adsorption viability audit",
        "created": datetime.now().isoformat(timespec="seconds"),
        "root": str(ROOT),
        "n_jobs": N_JOBS,
        "chunksize": CHUNKSIZE,
        "frozen_effect_input": str(EFFECTS),
        "frozen_effect_sha256": sha256(EFFECTS),
        "raw_files": [{"file": str(p), "sha256": sha256(p)} for p in raw_files],
        "decision": decision,
        "missing_values_filled": False,
        "duplicate_scientific_rows_averaged": False,
        "new_effect_estimated": False,
        "outputs": [
            "7B2_heat_source_coverage.csv",
            "7B2_heat_pair_coverage.csv",
            "7B2_heat_group_support.csv",
            "7B2_heat_unmatched_targets.csv",
            "7B2_heat_viability_report.txt",
        ],
        "python": sys.version,
        "pandas": pd.__version__,
    }
    (OUT / "7B2_heat_audit_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8", newline="\n"
    )

    print("\n".join(report))
    print(f"\nOutputs: {OUT}")


if __name__ == "__main__":
    main()
