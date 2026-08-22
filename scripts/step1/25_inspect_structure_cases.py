#usr/bin/env python3
"""Inspect and package the final Project 7 structure-case candidates.

Purpose
-------
Turn the frozen quantitative shortlist into a chemistry-facing inspection
package. The script does not select a more favorable numerical result. It:

1. audits every rank-1-to-rank-8 shortlisted pair;
2. extracts the corresponding charged CIFs;
3. parses formulas, elements, metals, occupancies, and simple composition deltas;
4. joins topology, dimensionality, pore geometry, coordination, adsorption,
   and process summaries already produced by the frozen analysis;
5. creates a review sheet for choosing the final six to eight cases;
6. records any reason a candidate cannot be used in a structure-resolved figure.

The output is an inspection package, not an automatic final case choice.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import hashlib
import json
import platform
import re
import shutil
import tarfile

import numpy as np
import pandas as pd
from pymatgen.core import Element, Structure
from pymatgen.io.cif import CifParser

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"

SHORTLIST_INPUT = ANALYSIS / "final_structure_case_shortlist.csv"
PAIR_INPUT = ANALYSIS / "final_primary_pairs.parquet"
FRAMEWORK_INPUT = ANALYSIS / "framework_master.parquet"
CIF_CHEMISTRY_INPUT = ANALYSIS / "cif_chemistry.parquet"
COORDINATION_INPUT = ANALYSIS / "metal_coordination_signatures.parquet"
ADSORPTION_INPUT = ANALYSIS / "final_primary_pair_effect_magnitudes.parquet"
PROCESS_INPUT = ANALYSIS / "process_translation_pair_results_final.parquet"

OUTPUT_DIR = ANALYSIS / "final_structure_case_inspection"
CIF_OUTPUT_DIR = OUTPUT_DIR / "cifs"
PAIR_AUDIT_OUTPUT = OUTPUT_DIR / "candidate_pair_audit.csv"
FRAMEWORK_AUDIT_OUTPUT = OUTPUT_DIR / "candidate_framework_audit.csv"
CONDITION_OUTPUT = OUTPUT_DIR / "candidate_adsorption_conditions.csv"
PROCESS_OUTPUT = OUTPUT_DIR / "candidate_process_results.csv"
REVIEW_OUTPUT = OUTPUT_DIR / "final_case_review_sheet.csv"
FAILURE_OUTPUT = OUTPUT_DIR / "candidate_cif_failures.csv"
MANIFEST_OUTPUT = OUTPUT_DIR / "inspection_manifest.json"

N_JOBS = 6
MAX_PENDING = 12

ROLE_PRIORITY = {
    "strong_linker_process_aligned": 1,
    "strong_metal_process_aligned": 2,
    "cu_zn_pressure_exception": 3,
    "near_null_comparison": 4,
    "process_discordant_comparison": 5,
    "functional_motif_example": 6,
}

GEOMETRY_COLUMNS = [
    "Di", "Df", "Dif", "Density", "UC_volume", "AVAf", "POAVAf"
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_id(value: object) -> str:
    text = str(value).strip()
    text = re.sub(r"(?i)\.cif$", "", text)
    text = re.sub(r"(?i)_repeat$", "", text)
    return text


def find_archive() -> Path:
    preferred = list(ROOT.rglob("ARCMOF_20241004.tar.gz"))
    if preferred:
        return preferred[0]
    alternatives = list(ROOT.rglob("ARCMOF_*.tar.gz"))
    if len(alternatives) == 1:
        return alternatives[0]
    if not alternatives:
        raise FileNotFoundError("No ARC-MOF charged-CIF archive was found below the project root")
    raise RuntimeError(
        "Several ARC-MOF archives were found; retain only the intended v7 archive or "
        "set the archive path explicitly. Found: " + ", ".join(map(str, alternatives))
    )


def choose_id_column(frame: pd.DataFrame) -> str:
    for column in ["mof_id", "filename", "filename_raw", "Name", "name"]:
        if column in frame.columns:
            return column
    raise ValueError(f"No framework identifier column found. Columns: {list(frame.columns)}")


def is_metal(symbol: str) -> bool:
    try:
        element = Element(symbol)
        return bool(element.is_metal or element.is_metalloid)
    except Exception:
        return False


def parse_cif_task(task: tuple[str, bytes]) -> dict:
    mof_id, cif_bytes = task
    result = {
        "mof_id": mof_id,
        "parse_ok": False,
        "formula_reduced": None,
        "formula_full": None,
        "elements": None,
        "metals": None,
        "nonmetals": None,
        "heteroatoms_nonmetal": None,
        "n_sites": None,
        "n_disordered_sites": None,
        "minimum_occupancy": None,
        "error": None,
    }
    try:
        text = cif_bytes.decode("utf-8", errors="strict")
        parser = CifParser.from_str(text, occupancy_tolerance=1.0)
        structures = parser.parse_structures(primitive=False)
        if not structures:
            raise ValueError("CifParser returned no structures")
        structure = structures[0]
        composition = structure.composition
        symbols = sorted({element.symbol for element in composition.elements})
        metals = sorted(symbol for symbol in symbols if is_metal(symbol))
        nonmetals = sorted(symbol for symbol in symbols if symbol not in metals)
        hetero = sorted(symbol for symbol in nonmetals if symbol not in {"C", "H"})
        occupancies = []
        disordered = 0
        for site in structure.sites:
            if not site.is_ordered:
                disordered += 1
            occupancies.extend(float(value) for value in site.species.values())
        result.update({
            "parse_ok": True,
            "formula_reduced": composition.reduced_formula,
            "formula_full": composition.formula,
            "elements": ";".join(symbols),
            "metals": ";".join(metals),
            "nonmetals": ";".join(nonmetals),
            "heteroatoms_nonmetal": ";".join(hetero),
            "n_sites": len(structure),
            "n_disordered_sites": disordered,
            "minimum_occupancy": min(occupancies) if occupancies else np.nan,
        })
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def read_member_bytes(archive_path: Path, needed_ids: set[str]) -> tuple[dict[str, bytes], dict[str, str]]:
    extracted: dict[str, bytes] = {}
    member_names: dict[str, str] = {}
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive:
            if not member.isfile():
                continue
            base = Path(member.name).name
            mof_id = canonical_id(base)
            if mof_id not in needed_ids or mof_id in extracted:
                continue
            handle = archive.extractfile(member)
            if handle is None:
                continue
            extracted[mof_id] = handle.read()
            member_names[mof_id] = member.name
            if len(extracted) == len(needed_ids):
                break
    return extracted, member_names


def endpoint_columns(shortlist: pd.DataFrame) -> tuple[str, str]:
    for a, b in [("id_a", "id_b"), ("pair_lo", "pair_hi"), ("variant_a", "variant_b")]:
        if a in shortlist.columns and b in shortlist.columns:
            return a, b
    if "pair_key" in shortlist.columns:
        split = shortlist["pair_key"].astype(str).str.split(" || ", n=1, expand=True)
        if split.shape[1] == 2:
            shortlist["id_a"] = split[0]
            shortlist["id_b"] = split[1]
            return "id_a", "id_b"
    raise ValueError("Shortlist has no usable pair endpoint columns")


def add_endpoint_data(pair_rows: pd.DataFrame, framework: pd.DataFrame, suffix: str, id_col: str) -> pd.DataFrame:
    available = [column for column in GEOMETRY_COLUMNS if column in framework.columns]
    extras = [
        column for column in [
            "topology", "likely topology", "Dimensionality", "Database", "DB_num",
            "metal_cluster", "linker_cluster", "functional_cluster"
        ] if column in framework.columns
    ]
    selected = framework[["mof_id"] + available + extras].drop_duplicates("mof_id").copy()
    selected = selected.rename(
        columns={column: f"{column}_{suffix}" for column in selected.columns if column != "mof_id"}
    )
    selected = selected.rename(columns={"mof_id": id_col})
    return pair_rows.merge(selected, on=id_col, how="left", validate="many_to_one")


def main() -> None:
    for path in [SHORTLIST_INPUT, PAIR_INPUT, FRAMEWORK_INPUT, ADSORPTION_INPUT, PROCESS_INPUT]:
        if not path.exists():
            raise FileNotFoundError(path)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CIF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    shortlist = pd.read_csv(SHORTLIST_INPUT, low_memory=False)
    endpoint_a, endpoint_b = endpoint_columns(shortlist)
    shortlist[endpoint_a] = shortlist[endpoint_a].map(canonical_id)
    shortlist[endpoint_b] = shortlist[endpoint_b].map(canonical_id)
    shortlist["role_order"] = shortlist["selection_category"].map(ROLE_PRIORITY)
    if "rank_within_category" in shortlist.columns:
        rank_column = "rank_within_category"
    elif "rank" in shortlist.columns:
        rank_column = "rank"
    else:
        raise ValueError(
            "Final shortlist has no rank column. Expected "
            "'rank_within_category' or 'rank'. Available columns: "
            + ", ".join(map(str, shortlist.columns))
        )
    shortlist["case_rank"] = pd.to_numeric(shortlist[rank_column], errors="raise")
    shortlist = shortlist.sort_values(
        ["role_order", "case_rank"], na_position="last"
    ).reset_index(drop=True)

    needed_ids = set(shortlist[endpoint_a]) | set(shortlist[endpoint_b])
    archive_path = find_archive()
    cif_bytes, member_names = read_member_bytes(archive_path, needed_ids)

    tasks = [(mof_id, cif_bytes[mof_id]) for mof_id in sorted(cif_bytes)]
    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:
        parsed = list(executor.map(parse_cif_task, tasks, chunksize=1))
    parsed_frame = pd.DataFrame(parsed)
    parsed_frame["archive_member"] = parsed_frame["mof_id"].map(member_names)

    for mof_id, data in cif_bytes.items():
        (CIF_OUTPUT_DIR / f"{mof_id}.cif").write_bytes(data)

    missing_ids = sorted(needed_ids - set(cif_bytes))
    failures = parsed_frame.loc[~parsed_frame["parse_ok"]].copy()
    if missing_ids:
        failures = pd.concat([
            failures,
            pd.DataFrame({
                "mof_id": missing_ids,
                "parse_ok": False,
                "error": "Archive member not found",
            })
        ], ignore_index=True, sort=False)
    failures.to_csv(FAILURE_OUTPUT, index=False)

    framework = pd.read_parquet(FRAMEWORK_INPUT)
    framework_id = choose_id_column(framework)
    framework["mof_id"] = framework[framework_id].map(canonical_id)
    framework = framework.loc[framework["mof_id"].isin(needed_ids)].copy()

    framework_audit = parsed_frame.merge(framework, on="mof_id", how="left", suffixes=("_parsed", "_master"))
    if CIF_CHEMISTRY_INPUT.exists():
        chemistry = pd.read_parquet(CIF_CHEMISTRY_INPUT)
        chemistry_id = choose_id_column(chemistry)
        chemistry["mof_id"] = chemistry[chemistry_id].map(canonical_id)
        chemistry = chemistry.loc[chemistry["mof_id"].isin(needed_ids)].drop_duplicates("mof_id")
        keep = [column for column in chemistry.columns if column == "mof_id" or column not in framework_audit.columns]
        framework_audit = framework_audit.merge(chemistry[keep], on="mof_id", how="left", validate="one_to_one")
    if COORDINATION_INPUT.exists():
        coordination = pd.read_parquet(COORDINATION_INPUT)
        coordination_id = choose_id_column(coordination)
        coordination["mof_id"] = coordination[coordination_id].map(canonical_id)
        coordination = coordination.loc[coordination["mof_id"].isin(needed_ids)].drop_duplicates("mof_id")
        keep = [column for column in coordination.columns if column == "mof_id" or column not in framework_audit.columns]
        framework_audit = framework_audit.merge(coordination[keep], on="mof_id", how="left", validate="one_to_one")
    framework_audit.to_csv(FRAMEWORK_AUDIT_OUTPUT, index=False)

    pair_audit = shortlist.copy()
    pair_audit = add_endpoint_data(pair_audit, framework, "a", endpoint_a)
    pair_audit = add_endpoint_data(pair_audit, framework, "b", endpoint_b)
    # Prefix parsed-CIF fields before endpoint suffixing. The shortlist already
    # contains fields such as metals_a/metals_b, so a plain merge would create
    # pandas _x/_y collision columns and make the parsed chemistry ambiguous.
    parsed_core = parsed_frame.rename(
        columns={column: f"parsed_{column}" for column in parsed_frame.columns if column != "mof_id"}
    )
    parsed_a = parsed_core.rename(
        columns={
            "mof_id": endpoint_a,
            **{
                column: f"{column}_a"
                for column in parsed_core.columns
                if column != "mof_id"
            },
        }
    )
    parsed_b = parsed_core.rename(
        columns={
            "mof_id": endpoint_b,
            **{
                column: f"{column}_b"
                for column in parsed_core.columns
                if column != "mof_id"
            },
        }
    )
    pair_audit = pair_audit.merge(parsed_a, on=endpoint_a, how="left", validate="many_to_one")
    pair_audit = pair_audit.merge(parsed_b, on=endpoint_b, how="left", validate="many_to_one")

    pair_audit["composition_same"] = pair_audit["parsed_formula_reduced_a"].eq(
        pair_audit["parsed_formula_reduced_b"]
    )
    pair_audit["metal_set_same"] = pair_audit["parsed_metals_a"].eq(
        pair_audit["parsed_metals_b"]
    )
    pair_audit["heteroatom_set_same"] = pair_audit[
        "parsed_heteroatoms_nonmetal_a"
    ].eq(pair_audit["parsed_heteroatoms_nonmetal_b"])
    pair_audit["formula_contrast"] = (
        pair_audit["parsed_formula_reduced_a"].astype("string")
        + "  <->  "
        + pair_audit["parsed_formula_reduced_b"].astype("string")
    )
    pair_audit["metal_contrast"] = (
        pair_audit["parsed_metals_a"].astype("string")
        + "  <->  "
        + pair_audit["parsed_metals_b"].astype("string")
    )
    pair_audit["renderable"] = (
        pair_audit["parsed_parse_ok_a"].fillna(False).astype(bool)
        & pair_audit["parsed_parse_ok_b"].fillna(False).astype(bool)
        & pair_audit["parsed_n_disordered_sites_a"].fillna(1).eq(0)
        & pair_audit["parsed_n_disordered_sites_b"].fillna(1).eq(0)
    )
    pair_audit["production_note"] = ""
    pair_audit["final_case_decision"] = "REVIEW"
    pair_audit.to_csv(PAIR_AUDIT_OUTPUT, index=False)

    shortlist_keys = set(shortlist["pair_key"])

    adsorption = pd.read_parquet(ADSORPTION_INPUT)
    if "pair_key" not in adsorption.columns:
        if "id_a" not in adsorption.columns or "id_b" not in adsorption.columns:
            raise KeyError(
                "Adsorption table has no pair_key and no id_a/id_b columns. "
                f"Available columns: {adsorption.columns.tolist()}"
            )
        adsorption["id_a"] = adsorption["id_a"].map(canonical_id)
        adsorption["id_b"] = adsorption["id_b"].map(canonical_id)
        adsorption["pair_key"] = np.where(
            adsorption["id_a"] <= adsorption["id_b"],
            adsorption["id_a"] + " || " + adsorption["id_b"],
            adsorption["id_b"] + " || " + adsorption["id_a"],
        )
    adsorption = adsorption.loc[
        adsorption["pair_key"].isin(shortlist_keys)
    ].copy()
    adsorption.to_csv(CONDITION_OUTPUT, index=False)

    process = pd.read_parquet(PROCESS_INPUT)
    if "pair_key" in process.columns:
        process = process.loc[
            process["pair_key"].isin(shortlist_keys)
        ].copy()
    process.to_csv(PROCESS_OUTPUT, index=False)

    review_columns = [
        column for column in [
            "selection_category", "case_rank", "pair_key", "intervention", "transition",
            endpoint_a, endpoint_b, "formula_contrast", "metal_contrast",
            "parsed_heteroatoms_nonmetal_a", "parsed_heteroatoms_nonmetal_b", "renderable",
            "median_absolute_log_difference", "mean_wc_concordance",
            "mean_selectivity_concordance", "rationale", "production_note",
            "final_case_decision"
        ] if column in pair_audit.columns
    ]
    pair_audit[review_columns].to_csv(REVIEW_OUTPUT, index=False)

    manifest = {
        "stage": "Final structure-case chemistry and renderability inspection",
        "shortlist_input": str(SHORTLIST_INPUT),
        "shortlist_sha256": sha256(SHORTLIST_INPUT),
        "archive": str(archive_path),
        "archive_sha256": sha256(archive_path),
        "candidate_pairs": int(len(shortlist)),
        "candidate_frameworks": int(len(needed_ids)),
        "cifs_found": int(len(cif_bytes)),
        "cifs_parsed": int(parsed_frame["parse_ok"].sum()),
        "parse_or_archive_failures": int(len(failures)),
        "renderable_pairs": int(pair_audit["renderable"].sum()),
        "n_jobs": N_JOBS,
        "automatic_final_selection": False,
        "pair_membership_changed": False,
        "scientific_values_imputed": False,
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
    }
    MANIFEST_OUTPUT.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    print(
        f"N_JOBS={N_JOBS}; candidate_pairs={len(shortlist):,}; "
        f"candidate_frameworks={len(needed_ids):,}"
    )
    print()
    print("CASE INSPECTION COVERAGE")
    print(f"cifs_found={len(cif_bytes):,}")
    print(f"cifs_parsed={int(parsed_frame['parse_ok'].sum()):,}")
    print(f"failures={len(failures):,}")
    print(f"renderable_pairs={int(pair_audit['renderable'].sum()):,}")
    print()
    print("TOP CANDIDATE CHEMISTRY")
    top = pair_audit.sort_values(["role_order", "case_rank"]).groupby("selection_category", as_index=False).first()
    display = [
        column for column in [
            "selection_category", "case_rank", "pair_key", "intervention", "transition",
            "formula_contrast", "metal_contrast", "parsed_heteroatoms_nonmetal_a",
            "parsed_heteroatoms_nonmetal_b", "renderable"
        ] if column in top.columns
    ]
    print(top[display].to_string(index=False))
    print()
    print("Outputs:")
    for path in [
        PAIR_AUDIT_OUTPUT, FRAMEWORK_AUDIT_OUTPUT, CONDITION_OUTPUT,
        PROCESS_OUTPUT, REVIEW_OUTPUT, FAILURE_OUTPUT, MANIFEST_OUTPUT
    ]:
        print(path)
    print(f"Candidate CIF directory: {CIF_OUTPUT_DIR}")
    print(
        "No final case was selected automatically. The review sheet records the "
        "chemistry, renderability, quantitative role, and final human decision."
    )


if __name__ == "__main__":
    main()

