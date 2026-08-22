#!/usr/bin/env python3
"""Join observed adsorption outcomes to all best-matched Project 7 pairs.

The complete pair x condition grid is created before outcomes are joined. This
ensures that a missing condition for either endpoint remains visible instead of
silently removing the pair-condition row.
"""
from pathlib import Path
import gc
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
ANALYSIS = ROOT / "analysis"
PAIR_FILE = ANALYSIS / "stringent_pair_dependence_ledger.parquet"
OUTPUT_FILE = ANALYSIS / "stringent_pairs_with_adsorption.parquet"
SUMMARY_FILE = ANALYSIS / "stringent_pair_adsorption_merge_summary.csv"
MISSING_FILE = ANALYSIS / "stringent_pair_adsorption_missing.csv"

N_JOBS = 1
CHUNK_SIZE = 250_000

ADSORPTION_FILES = {
    "landfill-CH4.csv": "landfill_CH4",
    "landfill-CO2.csv": "landfill_CO2",
    "methane.csv": "methane_storage_CH4",
    "methane_purification-CH4.csv": "methane_purification_CH4",
    "methane_purification-CO2.csv": "methane_purification_CO2",
    "post_comb_vsa-CO2.csv": "post_combustion_CO2",
    "post_comb_vsa-N2.csv": "post_combustion_N2",
    "pre_comb_4040-CO2.csv": "pre_combustion_CO2",
    "pre_comb_4040-H2.csv": "pre_combustion_H2",
}


def canonical_id(series):
    return (series.astype("string").str.strip()
            .str.replace(r"(?i)\.cif$", "", regex=True)
            .str.replace(r"(?i)_repeat$", "", regex=True))


def load_relevant_adsorption(wanted_ids):
    parts=[]
    for filename,target in ADSORPTION_FILES.items():
        source_rows=retained_rows=0
        for chunk in pd.read_csv(
            RAW/filename,
            usecols=["filename","T/K","p/bar","mmol/g","stdev"],
            chunksize=CHUNK_SIZE,
        ):
            source_rows += len(chunk)
            chunk["mof_id"] = canonical_id(chunk["filename"])
            chunk = chunk.loc[chunk["mof_id"].isin(wanted_ids)].copy()
            if chunk.empty:
                continue
            for column in ["T/K","p/bar","mmol/g","stdev"]:
                chunk[column] = pd.to_numeric(chunk[column], errors="coerce")
            chunk["target"] = target
            retained_rows += len(chunk)
            parts.append(chunk[["mof_id","target","T/K","p/bar","mmol/g","stdev"]])
        print(f"{filename}: source_rows={source_rows:,}; retained_rows={retained_rows:,}")
        gc.collect()
    adsorption=pd.concat(parts,ignore_index=True)
    keys=["mof_id","target","T/K","p/bar"]
    duplicate=adsorption.duplicated(keys,keep=False)
    if duplicate.any():
        raise RuntimeError("Duplicate framework-condition adsorption records detected")
    return adsorption


def main():
    pairs=pd.read_parquet(PAIR_FILE)
    if not pairs["geometry_tier"].eq("stringent").all():
        raise RuntimeError("Non-stringent rows found in accepted pair table")
    if pairs[["intervention","pair_lo","pair_hi"]].duplicated().any():
        raise RuntimeError("Duplicate unordered pairs detected")

    wanted_ids=set(pairs["id_a"].astype(str)) | set(pairs["id_b"].astype(str))
    print(f"N_JOBS={N_JOBS}; raw_pairs={len(pairs):,}; unique_frameworks={len(wanted_ids):,}")
    adsorption=load_relevant_adsorption(wanted_ids)

    # The design contains exactly two conditions from each named adsorption file.
    conditions=(adsorption[["target","T/K","p/bar"]]
                .drop_duplicates().sort_values(["target","T/K","p/bar"])
                .reset_index(drop=True))
    expected_conditions=2*len(ADSORPTION_FILES)
    if len(conditions) != expected_conditions:
        raise RuntimeError(
            f"Expected {expected_conditions} adsorption conditions, found {len(conditions)}"
        )

    # Build the full grid first so absence at either endpoint cannot disappear.
    pair_grid=(pairs.assign(_join_key=1)
               .merge(conditions.assign(_join_key=1),on="_join_key",how="inner",validate="many_to_many")
               .drop(columns="_join_key"))

    left=adsorption.rename(columns={"mof_id":"id_a","mmol/g":"uptake_a","stdev":"stdev_a"})
    right=adsorption.rename(columns={"mof_id":"id_b","mmol/g":"uptake_b","stdev":"stdev_b"})
    merged=(pair_grid
            .merge(left,on=["id_a","target","T/K","p/bar"],how="left",validate="many_to_one")
            .merge(right,on=["id_b","target","T/K","p/bar"],how="left",validate="many_to_one"))

    expected_rows=len(pairs)*len(conditions)
    if len(merged) != expected_rows:
        raise RuntimeError(f"Grid loss: expected {expected_rows}, wrote {len(merged)}")

    merged["outcome_complete"]=merged["uptake_a"].notna() & merged["uptake_b"].notna()
    merged["reported_stdev_valid_a"]=merged["stdev_a"].notna() & merged["stdev_a"].gt(0)
    merged["reported_stdev_valid_b"]=merged["stdev_b"].notna() & merged["stdev_b"].gt(0)
    merged["both_stdev_valid"]=merged["reported_stdev_valid_a"] & merged["reported_stdev_valid_b"]
    merged["raw_delta_b_minus_a"]=merged["uptake_b"]-merged["uptake_a"]
    merged["absolute_pair_difference"]=merged["raw_delta_b_minus_a"].abs()

    missing=merged.loc[~merged["outcome_complete"],[
        "intervention","pair_lo","pair_hi","id_a","id_b","target","T/K","p/bar","uptake_a","uptake_b"
    ]].copy()
    summary=(merged.groupby(["intervention","target","T/K","p/bar"],as_index=False,dropna=False)
             .agg(raw_pair_rows=("pair_lo","size"),
                  complete_pair_rows=("outcome_complete","sum"),
                  distinct_comparisons=("evidence_unit_id","nunique"),
                  related_comparison_groups=("dependence_family_id","nunique"),
                  valid_stdev_pairs=("both_stdev_valid","sum")))
    summary["outcome_coverage"]=summary["complete_pair_rows"]/summary["raw_pair_rows"]

    merged.to_parquet(OUTPUT_FILE,index=False)
    summary.to_csv(SUMMARY_FILE,index=False)
    missing.to_csv(MISSING_FILE,index=False)

    print("\nADSORPTION MERGE SUMMARY")
    print(f"Adsorption conditions: {len(conditions)}")
    print(f"Expected pair-condition rows: {expected_rows:,}")
    print(f"Written pair-condition rows: {len(merged):,}")
    print(f"Complete paired outcomes: {int(merged['outcome_complete'].sum()):,}")
    print(f"Incomplete paired outcomes: {len(missing):,}")
    print("\nMISSING BY TARGET AND ENDPOINT:")
    if missing.empty:
        print("NONE")
    else:
        missing_report=(missing.assign(missing_a=missing["uptake_a"].isna(),missing_b=missing["uptake_b"].isna())
                        .groupby(["target","T/K","p/bar"],as_index=False)
                        .agg(pair_rows=("pair_lo","size"),missing_a=("missing_a","sum"),missing_b=("missing_b","sum")))
        print(missing_report.to_string(index=False))
    print("\nNo effect was pooled. No model was fitted. No missing value was filled.")

if __name__ == "__main__":
    main()

