#!/usr/bin/env python3
"""Build the verified full Project 7 ARC-MOF framework cohort.

Reference grain
---------------
One row per canonical ARC-MOF framework ID.

Scientific-data policy
----------------------
- No row-order joins.
- No missing-value imputation.
- No NaN-to-zero conversion.
- Observed zeros remain valid observations.
- Missing required values are handled through explicit eligibility flags.
- The 242,297 ARC-MOF=False geometry rows are outside Project 7's study cohort.
"""

from pathlib import Path
import gc
import tarfile

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
OUT = ROOT / "analysis"
OUT.mkdir(exist_ok=True)

EXPECTED_GEOMETRY_UNIVERSE = 521_316
EXPECTED_ARCMOF_GEOMETRY = 279_019
EXPECTED_ARCMOF_ADSORPTION_OVERLAP = 279_010
EXPECTED_ADSORPTION_ONLY = 600


def canonical_id(series: pd.Series) -> pd.Series:
    """Return the verified cross-table join ID without altering internal text."""
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"(?i)\.cif$", "", regex=True)
        .str.replace(r"(?i)_repeat$", "", regex=True)
        .str.replace(r"(?i)_sqe$", "", regex=True)
    )


def require_columns(frame: pd.DataFrame, columns: list[str], source: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{source} is missing required columns: {missing}")


def assert_unique_id(frame: pd.DataFrame, source: str) -> None:
    if frame["mof_id"].isna().any():
        raise RuntimeError(f"{source} contains missing canonical IDs")
    if frame["mof_id"].duplicated().any():
        examples = frame.loc[
            frame["mof_id"].duplicated(keep=False), "mof_id"
        ].head(10).tolist()
        raise RuntimeError(f"Duplicate canonical IDs in {source}: {examples}")


# -----------------------------------------------------------------------------
# 1. Geometry reference and ARC-MOF study boundary
# -----------------------------------------------------------------------------

geometry = pd.read_csv(RAW / "geometric_properties.csv", low_memory=False)
require_columns(
    geometry,
    [
        "filename",
        "ARC-MOF",
        "DB_num",
        "UC_volume",
        "Density",
        "ASA",
        "AVA",
        "AVAf",
        "POAVA",
        "POAVAf",
        "Di",
        "Df",
        "Dif",
    ],
    "geometric_properties.csv",
)

geometry["filename_raw"] = geometry["filename"]
geometry["mof_id"] = canonical_id(geometry["filename"])
assert_unique_id(geometry, "geometric_properties.csv")

if len(geometry) != EXPECTED_GEOMETRY_UNIVERSE:
    raise RuntimeError(
        f"Expected {EXPECTED_GEOMETRY_UNIVERSE} geometry rows, found {len(geometry)}"
    )

external_geometry_count = int((~geometry["ARC-MOF"].eq(True)).sum())
geometry = geometry.loc[geometry["ARC-MOF"].eq(True)].copy()

if len(geometry) != EXPECTED_ARCMOF_GEOMETRY:
    raise RuntimeError(
        f"Expected {EXPECTED_ARCMOF_GEOMETRY} ARC-MOF geometry rows, "
        f"found {len(geometry)}"
    )

geometry_columns = [
    "UC_volume",
    "Density",
    "ASA",
    "AVA",
    "AVAf",
    "POAVA",
    "POAVAf",
    "Di",
    "Df",
    "Dif",
]

for column in geometry_columns:
    geometry[column] = pd.to_numeric(geometry[column], errors="coerce")

master = geometry[
    ["mof_id", "filename_raw", "DB_num", *geometry_columns]
].copy()


# -----------------------------------------------------------------------------
# 2. Explicit dimensionality mapping
# -----------------------------------------------------------------------------

dimensionality = pd.read_csv(
    RAW / "ARC-MOF_Dim.csv",
    usecols=["Filename", "Dimensionality"],
    low_memory=False,
)
dimensionality["mof_id"] = canonical_id(dimensionality["Filename"])

conflicts = dimensionality.groupby("mof_id")["Dimensionality"].nunique(
    dropna=False
)
if (conflicts > 1).any():
    raise RuntimeError("Conflicting dimensionality assignments detected")

dimensionality = dimensionality.drop_duplicates("mof_id", keep="first")
assert_unique_id(dimensionality, "ARC-MOF_Dim.csv after exact deduplication")

if dimensionality["Dimensionality"].nunique(dropna=True) > 10:
    raise RuntimeError("Implausible dimensionality cardinality")

master = master.merge(
    dimensionality[["mof_id", "Dimensionality"]],
    on="mof_id",
    how="left",
    validate="one_to_one",
)


# -----------------------------------------------------------------------------
# 3. Explicit topology mapping
# -----------------------------------------------------------------------------

topology = pd.read_csv(
    RAW / "all_topology_lists.csv",
    usecols=["Name", "filename", "Crystalnet", "likely topology"],
    low_memory=False,
)
topology["mof_id"] = canonical_id(topology["Name"])
topology = topology.rename(
    columns={
        "filename": "topology_source",
        "Crystalnet": "topology_crystalnet",
        "likely topology": "topology",
    }
)
assert_unique_id(topology, "all_topology_lists.csv")

master = master.merge(
    topology[
        ["mof_id", "topology", "topology_source", "topology_crystalnet"]
    ],
    on="mof_id",
    how="left",
    validate="one_to_one",
)


# -----------------------------------------------------------------------------
# 4. Cluster layers; negative IDs remain distinct singleton assignments
# -----------------------------------------------------------------------------

cluster_sources = [
    ("geo-clusters.csv", "geo_cluster"),
    ("mc-clusters.csv", "metal_cluster"),
    ("func-clusters.csv", "functional_cluster"),
    ("flig-clusters.csv", "linker_cluster"),
]

for filename, output_column in cluster_sources:
    clusters = pd.read_csv(
        RAW / filename,
        usecols=["filename", "cluster_id"],
        low_memory=False,
    )
    clusters["mof_id"] = canonical_id(clusters["filename"])
    assert_unique_id(clusters, filename)

    master = master.merge(
        clusters[["mof_id", "cluster_id"]].rename(
            columns={"cluster_id": output_column}
        ),
        on="mof_id",
        how="left",
        validate="one_to_one",
    )


# -----------------------------------------------------------------------------
# 5. RAC descriptors; remove metadata and constant columns only
# -----------------------------------------------------------------------------

racs = pd.read_csv(RAW / "RACs.csv", low_memory=False)
require_columns(racs, ["filename"], "RACs.csv")
racs["mof_id"] = canonical_id(racs["filename"])
assert_unique_id(racs, "RACs.csv")

rac_metadata = {
    "Unnamed: 0",
    "filename",
    "mof_id",
    "ARC_MOF",
    "DB_num",
    "order_f-lig",
    "bool_f-lig",
    "order_mc",
    "bool_mc",
    "order_func",
    "bool_func",
    "order_lc",
    "bool_lc",
}

rac_candidates = [column for column in racs.columns if column not in rac_metadata]
for column in rac_candidates:
    racs[column] = pd.to_numeric(racs[column], errors="coerce")

rac_columns = [
    column
    for column in rac_candidates
    if racs[column].nunique(dropna=True) > 1
]

master = master.merge(
    racs[["mof_id", *rac_columns]],
    on="mof_id",
    how="left",
    validate="one_to_one",
)

# Release source tables before scanning multi-million-row outcome files.
del geometry, dimensionality, topology, racs
gc.collect()


# -----------------------------------------------------------------------------
# 6. CIF membership; membership does not imply validated chemistry values
# -----------------------------------------------------------------------------

cif_ids: set[str] = set()
with tarfile.open(RAW / "ARCMOF_20241004.tar.gz", "r:gz") as archive:
    for member in archive:
        if member.isfile() and member.name.lower().endswith(".cif"):
            value = canonical_id(pd.Series([Path(member.name).name])).iloc[0]
            cif_ids.add(str(value))

master["has_cif"] = master["mof_id"].isin(cif_ids)


# -----------------------------------------------------------------------------
# 7. Adsorption membership at framework grain
# -----------------------------------------------------------------------------

adsorption_files = [
    "landfill-CH4.csv",
    "landfill-CO2.csv",
    "methane.csv",
    "methane_purification-CH4.csv",
    "methane_purification-CO2.csv",
    "post_comb_vsa-CO2.csv",
    "post_comb_vsa-N2.csv",
    "pre_comb_4040-CO2.csv",
    "pre_comb_4040-H2.csv",
]

adsorption_ids: set[str] = set()
for filename in adsorption_files:
    for chunk in pd.read_csv(
        RAW / filename,
        usecols=["filename"],
        chunksize=250_000,
    ):
        adsorption_ids.update(canonical_id(chunk["filename"]).dropna())
    del chunk
    gc.collect()

arc_ids = set(master["mof_id"])
adsorption_overlap = arc_ids & adsorption_ids
adsorption_only_ids = adsorption_ids - arc_ids
geometry_only_ids = arc_ids - adsorption_ids

if len(adsorption_overlap) != EXPECTED_ARCMOF_ADSORPTION_OVERLAP:
    raise RuntimeError(
        f"Expected {EXPECTED_ARCMOF_ADSORPTION_OVERLAP} ARC-MOF adsorption "
        f"overlap, found {len(adsorption_overlap)}"
    )

if len(adsorption_only_ids) != EXPECTED_ADSORPTION_ONLY:
    raise RuntimeError(
        f"Expected {EXPECTED_ADSORPTION_ONLY} adsorption-only IDs, "
        f"found {len(adsorption_only_ids)}"
    )

master["has_adsorption"] = master["mof_id"].isin(adsorption_overlap)


# -----------------------------------------------------------------------------
# 8. Process membership at framework grain
# -----------------------------------------------------------------------------

process_ids: set[str] = set()
for chunk in pd.read_csv(
    RAW / "overall_process.csv",
    usecols=["filename"],
    chunksize=250_000,
):
    process_ids.update(canonical_id(chunk["filename"]).dropna())
del chunk
gc.collect()
master["has_process"] = master["mof_id"].isin(process_ids)


# -----------------------------------------------------------------------------
# 9. Observed-data eligibility; no filling
# -----------------------------------------------------------------------------

required_match_geometry = [
    "UC_volume",
    "Density",
    "AVAf",
    "POAVAf",
    "Di",
    "Df",
    "Dif",
]

master["geometry_complete"] = master[required_match_geometry].notna().all(axis=1)
master["porous_geometry"] = master["geometry_complete"] & master["Df"].gt(0)
master["structure_context_complete"] = master[
    ["topology", "Dimensionality"]
].notna().all(axis=1)
master["clusters_complete"] = master[
    ["geo_cluster", "metal_cluster", "functional_cluster", "linker_cluster"]
].notna().all(axis=1)
master["rac_complete"] = master[rac_columns].notna().all(axis=1)

master["primary_adsorption_eligible"] = (
    master["porous_geometry"]
    & master["has_adsorption"]
    & master["structure_context_complete"]
)

master["chemistry_verification_eligible"] = (
    master["primary_adsorption_eligible"]
    & master["has_cif"]
    & master["clusters_complete"]
    & master["rac_complete"]
)

if master["mof_id"].duplicated().any():
    raise RuntimeError("Master grain violated: duplicate framework IDs")
if len(master) != EXPECTED_ARCMOF_GEOMETRY:
    raise RuntimeError("Master grain violated: unexpected framework count")


# -----------------------------------------------------------------------------
# 10. Save master, attrition, and quarantined-ID ledgers
# -----------------------------------------------------------------------------

master_path = OUT / "framework_master.parquet"
master.to_parquet(master_path, index=False)

cohort_flow = pd.DataFrame(
    [
        ("combined_geometry_source", EXPECTED_GEOMETRY_UNIVERSE),
        ("excluded_ARC_MOF_false", external_geometry_count),
        ("ARC_MOF_geometry_reference", len(master)),
        ("ARC_MOF_with_adsorption", int(master["has_adsorption"].sum())),
        ("porous_geometry", int(master["porous_geometry"].sum())),
        (
            "structure_context_complete",
            int(master["structure_context_complete"].sum()),
        ),
        (
            "primary_adsorption_eligible",
            int(master["primary_adsorption_eligible"].sum()),
        ),
        ("has_cif", int(master["has_cif"].sum())),
        ("clusters_complete", int(master["clusters_complete"].sum())),
        ("rac_complete", int(master["rac_complete"].sum())),
        (
            "chemistry_verification_eligible",
            int(master["chemistry_verification_eligible"].sum()),
        ),
    ],
    columns=["cohort_stage", "frameworks"],
)

cohort_flow["fraction_of_ARC_MOF_geometry"] = (
    cohort_flow["frameworks"] / EXPECTED_ARCMOF_GEOMETRY
)
cohort_flow.to_csv(OUT / "cohort_flow.csv", index=False)

pd.DataFrame({"mof_id": sorted(adsorption_only_ids)}).to_csv(
    OUT / "quarantine_adsorption_without_geometry.csv",
    index=False,
)
pd.DataFrame({"mof_id": sorted(geometry_only_ids)}).to_csv(
    OUT / "ledger_geometry_without_adsorption.csv",
    index=False,
)

print(cohort_flow.to_string(index=False))
print()
print(f"Saved master: {master_path}")
print(f"Usable RAC descriptors: {len(rac_columns)}")
print(f"Adsorption-only IDs quarantined: {len(adsorption_only_ids)}")
print(f"Geometry-only IDs retained in ledger: {len(geometry_only_ids)}")
print("No missing scientific values were filled.")

