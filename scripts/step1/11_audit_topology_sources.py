#!/usr/bin/env python3
"""Step 1 of 5: audit topology provenance for Project 7.

Purpose
-------
Determine whether the topology used in matching came from the source filename,
CrystalNets, or an agreement between both. This stage does not remove pairs,
read adsorption outcomes, calculate effects, or change the current main result.

The script reports facts first. Any later restriction to a high-confidence
topology subset will be predeclared and compared with the current result.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
MASTER_FILE = ANALYSIS / "framework_master.parquet"
PAIR_FILE = ANALYSIS / "stringent_pair_dependence_ledger.parquet"

FRAMEWORK_OUTPUT = ANALYSIS / "topology_provenance_frameworks.parquet"
PAIR_OUTPUT = ANALYSIS / "topology_provenance_pairs.parquet"
SUMMARY_OUTPUT = ANALYSIS / "topology_provenance_summary.csv"
CONFLICT_OUTPUT = ANALYSIS / "topology_provenance_conflicts.csv"

# Pandas joins and string comparisons are vectorized. Six processes would copy
# the same tables six times without accelerating the scientific calculation.
N_JOBS = 1

TOPOLOGY_COLUMNS = [
    "mof_id",
    "topology",
    "topology_source",
    "topology_crystalnet",
    "chemistry_verification_eligible",
]


def observed(series):
    """Mark genuinely populated labels without converting one label into another."""
    text = series.astype("string").str.strip()
    return series.notna() & text.ne("") & text.str.lower().ne("nan")


def normalized(series):
    """Normalize only whitespace and case for an equality audit."""
    return series.astype("string").str.strip().str.lower()


def classify_framework(frame):
    source_present = observed(frame["topology_source"])
    crystal_present = observed(frame["topology_crystalnet"])
    primary_present = observed(frame["topology"])

    source_norm = normalized(frame["topology_source"])
    crystal_norm = normalized(frame["topology_crystalnet"])
    primary_norm = normalized(frame["topology"])

    both_present = source_present & crystal_present
    source_crystal_agree = both_present & source_norm.eq(crystal_norm)
    source_crystal_conflict = both_present & ~source_norm.eq(crystal_norm)

    result = pd.Series("unavailable", index=frame.index, dtype="string")
    result.loc[source_crystal_agree] = "source_and_crystalnet_agree"
    result.loc[source_crystal_conflict] = "source_and_crystalnet_conflict"
    result.loc[source_present & ~crystal_present] = "source_only"
    result.loc[~source_present & crystal_present] = "crystalnet_only"
    result.loc[~primary_present] = "primary_topology_missing"

    frame = frame.copy()
    frame["source_topology_present"] = source_present
    frame["crystalnet_topology_present"] = crystal_present
    frame["primary_topology_present"] = primary_present
    frame["source_crystalnet_agree"] = source_crystal_agree
    frame["source_crystalnet_conflict"] = source_crystal_conflict
    frame["primary_matches_source"] = (
        primary_present & source_present & primary_norm.eq(source_norm)
    )
    frame["primary_matches_crystalnet"] = (
        primary_present & crystal_present & primary_norm.eq(crystal_norm)
    )
    frame["topology_provenance_class"] = result
    return frame


def main():
    if not MASTER_FILE.exists():
        raise FileNotFoundError(MASTER_FILE)
    if not PAIR_FILE.exists():
        raise FileNotFoundError(PAIR_FILE)

    master = pd.read_parquet(MASTER_FILE, columns=TOPOLOGY_COLUMNS)
    master = master.loc[master["chemistry_verification_eligible"]].copy()

    if master["mof_id"].duplicated().any():
        raise RuntimeError("Duplicate framework IDs in the master table")

    framework = classify_framework(master)
    framework.to_parquet(FRAMEWORK_OUTPUT, index=False)

    conflicts = framework.loc[
        framework["source_crystalnet_conflict"],
        [
            "mof_id",
            "topology",
            "topology_source",
            "topology_crystalnet",
            "primary_matches_source",
            "primary_matches_crystalnet",
        ],
    ].copy()
    conflicts.to_csv(CONFLICT_OUTPUT, index=False)

    pairs = pd.read_parquet(PAIR_FILE)
    if not pairs["geometry_tier"].eq("stringent").all():
        raise RuntimeError("Pair table contains non-stringent rows")

    endpoint_columns = [
        "mof_id",
        "topology",
        "topology_source",
        "topology_crystalnet",
        "topology_provenance_class",
        "source_crystalnet_agree",
        "source_crystalnet_conflict",
        "primary_matches_source",
        "primary_matches_crystalnet",
    ]

    left = framework[endpoint_columns].add_suffix("_a").rename(
        columns={"mof_id_a": "id_a"}
    )
    right = framework[endpoint_columns].add_suffix("_b").rename(
        columns={"mof_id_b": "id_b"}
    )

    pair_audit = (
        pairs.merge(left, on="id_a", how="left", validate="many_to_one")
        .merge(right, on="id_b", how="left", validate="many_to_one")
    )

    if pair_audit[
        ["topology_provenance_class_a", "topology_provenance_class_b"]
    ].isna().any().any():
        raise RuntimeError("Missing topology provenance after pair merge")

    pair_audit["both_endpoints_source_crystalnet_agree"] = (
        pair_audit["source_crystalnet_agree_a"]
        & pair_audit["source_crystalnet_agree_b"]
        & normalized(pair_audit["topology_source_a"]).eq(
            normalized(pair_audit["topology_source_b"])
        )
        & normalized(pair_audit["topology_crystalnet_a"]).eq(
            normalized(pair_audit["topology_crystalnet_b"])
        )
    )
    pair_audit["either_endpoint_source_crystalnet_conflict"] = (
        pair_audit["source_crystalnet_conflict_a"]
        | pair_audit["source_crystalnet_conflict_b"]
    )
    pair_audit["both_endpoints_have_source_topology"] = (
        pair_audit["topology_source_a"].notna()
        & pair_audit["topology_source_b"].notna()
    )
    pair_audit["both_endpoints_primary_match_source"] = (
        pair_audit["primary_matches_source_a"]
        & pair_audit["primary_matches_source_b"]
    )
    pair_audit.to_parquet(PAIR_OUTPUT, index=False)

    summary_rows = []

    framework_counts = (
        framework["topology_provenance_class"].value_counts(dropna=False)
    )
    for label, count in framework_counts.items():
        summary_rows.append(
            {
                "scope": "chemistry_supported_frameworks",
                "intervention": "all",
                "topology_category": str(label),
                "records": int(count),
            }
        )

    for intervention, group in pair_audit.groupby("intervention", sort=False):
        pair_categories = {
            "all_stringent_pairs": len(group),
            "both_endpoints_source_crystalnet_agree": int(
                group["both_endpoints_source_crystalnet_agree"].sum()
            ),
            "either_endpoint_source_crystalnet_conflict": int(
                group["either_endpoint_source_crystalnet_conflict"].sum()
            ),
            "both_endpoints_have_source_topology": int(
                group["both_endpoints_have_source_topology"].sum()
            ),
            "both_endpoints_primary_match_source": int(
                group["both_endpoints_primary_match_source"].sum()
            ),
        }
        for label, count in pair_categories.items():
            summary_rows.append(
                {
                    "scope": "stringent_pairs",
                    "intervention": intervention,
                    "topology_category": label,
                    "records": int(count),
                }
            )

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(SUMMARY_OUTPUT, index=False)

    print(f"N_JOBS={N_JOBS}; vectorized audit; no parallel processing required")
    print("\nFRAMEWORK TOPOLOGY PROVENANCE")
    print(framework_counts.to_string())

    print("\nSTRICT PAIR TOPOLOGY PROVENANCE")
    pair_summary = summary.loc[summary["scope"].eq("stringent_pairs")]
    print(
        pair_summary.pivot(
            index="intervention",
            columns="topology_category",
            values="records",
        ).fillna(0).astype(int).to_string()
    )

    print("\nCONFLICT RESOLUTION IN THE PRIMARY TOPOLOGY FIELD")
    if conflicts.empty:
        print("No source-versus-CrystalNet conflicts found.")
    else:
        print(
            conflicts[
                ["primary_matches_source", "primary_matches_crystalnet"]
            ].value_counts(dropna=False).to_string()
        )

    print("\nOutputs:")
    print(FRAMEWORK_OUTPUT)
    print(PAIR_OUTPUT)
    print(SUMMARY_OUTPUT)
    print(CONFLICT_OUTPUT)
    print(
        "No pair was removed or reclassified. Adsorption outcomes were not read. "
        "No missing value was filled."
    )


if __name__ == "__main__":
    main()

