#!/usr/bin/env python3
"""Parallel full-cohort CIF chemistry extraction for Project 7.

One process reads the compressed archive. A bounded process pool parses CIF text.
CrystalNN is not run. Missing scientific values are never filled.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path
import os
import re
import tarfile
import warnings

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
OUT = ROOT / "analysis"
OUT.mkdir(exist_ok=True)

ARCHIVE = RAW / "ARCMOF_20241004.tar.gz"
MASTER = OUT / "framework_master.parquet"
OUTPUT = OUT / "cif_chemistry.parquet"
FAILURES = OUT / "cif_chemistry_failures.csv"
SUMMARY = OUT / "cif_chemistry_summary.csv"
CHECKPOINT = OUT / "cif_chemistry_checkpoint.csv"

N_JOBS = 6
MAX_PENDING = 12
CHECKPOINT_EVERY = 5000


def canonical_id(value: str) -> str:
    name = Path(str(value).strip()).name
    if name.lower().endswith(".cif"):
        name = name[:-4]
    if name.lower().endswith("_repeat"):
        name = name[:-7]
    return name


def as_list(value):
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


def clean_number(value):
    if value is None:
        return np.nan
    text = str(value).strip().strip("'\"")
    if text in {"", ".", "?", "nan", "None"}:
        return np.nan
    text = re.sub(r"\([^)]*\)$", "", text)
    try:
        return float(text)
    except ValueError:
        return np.nan


def element_symbol(value):
    match = re.match(r"([A-Z][a-z]?)", str(value).strip())
    return match.group(1) if match else None


def parse_one(payload):
    """Worker: parse one CIF string. Imports pymatgen inside the worker."""
    mof_id, member_name, text = payload
    from pymatgen.core import Element
    from pymatgen.io.cif import CifParser

    def is_metal(symbol):
        try:
            return bool(Element(symbol).is_metal)
        except Exception:
            return False

    record = {
        "mof_id": mof_id,
        "cif_member_path": member_name,
        "parse_ok": False,
        "formula": pd.NA,
        "n_structure_sites": np.nan,
        "elements": pd.NA,
        "metals": pd.NA,
        "n_distinct_metals": np.nan,
        "single_metal": pd.NA,
        "metal_site_count": np.nan,
        "raw_atom_rows": np.nan,
        "raw_charge_rows": np.nan,
        "raw_occupancy_rows": np.nan,
        "charge_length_aligned": False,
        "charge_numeric_fraction": np.nan,
        "occupancy_weighted_charge_sum": np.nan,
        "element_sets_match": False,
        "n_disordered_sites": np.nan,
        "warning_count": 0,
        "error": pd.NA,
    }

    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            parser = CifParser.from_str(text)
            structures = parser.parse_structures(primitive=False)
        record["warning_count"] = len(caught)
        if not structures:
            raise ValueError("Pymatgen returned no structure")

        structure = structures[0]
        structure_elements = set()
        metal_counts = {}
        disordered_sites = 0
        for site in structure:
            if not site.is_ordered:
                disordered_sites += 1
            for specie, occupancy in site.species.items():
                symbol = specie.symbol
                structure_elements.add(symbol)
                if is_metal(symbol):
                    metal_counts[symbol] = metal_counts.get(symbol, 0.0) + float(occupancy)

        raw_dict = parser.as_dict()
        if not raw_dict:
            raise ValueError("Pymatgen returned no CIF data block")
        block = next(iter(raw_dict.values()))
        symbols = as_list(block.get("_atom_site_type_symbol") or block.get("_atom_site_label"))
        charges = []
        for key in ["_atom_site_charge", "_atom_site_partial_charge",
                    "_atom_type_partial_charge", "_atom_site_mulliken_charge"]:
            if key in block:
                charges = as_list(block[key])
                break
        occupancies = as_list(block.get("_atom_site_occupancy"))
        if not occupancies and symbols:
            occupancies = [1.0] * len(symbols)

        raw_elements = {element_symbol(v) for v in symbols if element_symbol(v) is not None}
        aligned = len(symbols) > 0 and len(symbols) == len(charges) == len(occupancies)
        numeric_charges = np.array([clean_number(v) for v in charges], dtype=float)
        numeric_occupancies = np.array([clean_number(v) for v in occupancies], dtype=float)
        charge_fraction = float(np.isfinite(numeric_charges).mean()) if len(numeric_charges) else np.nan
        charge_sum = np.nan
        if aligned and len(numeric_charges):
            valid = np.isfinite(numeric_charges) & np.isfinite(numeric_occupancies)
            if valid.any():
                charge_sum = float(np.sum(numeric_charges[valid] * numeric_occupancies[valid]))

        metals = sorted(metal_counts)
        record.update({
            "parse_ok": True,
            "formula": structure.composition.reduced_formula,
            "n_structure_sites": len(structure),
            "elements": ";".join(sorted(structure_elements)),
            "metals": ";".join(metals),
            "n_distinct_metals": len(metals),
            "single_metal": len(metals) == 1,
            "metal_site_count": float(sum(metal_counts.values())),
            "raw_atom_rows": len(symbols),
            "raw_charge_rows": len(charges),
            "raw_occupancy_rows": len(occupancies),
            "charge_length_aligned": aligned,
            "charge_numeric_fraction": charge_fraction,
            "occupancy_weighted_charge_sum": charge_sum,
            "element_sets_match": raw_elements == structure_elements,
            "n_disordered_sites": disordered_sites,
        })
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"[:1000]
    return record


def save_checkpoint(records):
    pd.DataFrame(records).to_csv(CHECKPOINT, index=False)


def collect_finished(pending, records):
    done, pending = wait(pending, return_when=FIRST_COMPLETED)
    for future in done:
        records.append(future.result())
    return pending


def main():
    if not ARCHIVE.exists() or not MASTER.exists():
        raise FileNotFoundError("Missing archive or framework master")

    master = pd.read_parquet(MASTER, columns=["mof_id", "has_cif"])
    master_ids = set(master["mof_id"].astype(str))
    expected_ids = set(master.loc[master["has_cif"], "mof_id"].astype(str))

    records = []
    pending = set()
    submitted = 0
    submitted_ids = set()

    print(f"N_JOBS={N_JOBS}; MAX_PENDING={MAX_PENDING}; expected={len(expected_ids):,}")

    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:
        with tarfile.open(ARCHIVE, "r:gz") as archive:
            for member in archive:
                if not member.isfile() or not member.name.lower().endswith(".cif"):
                    continue
                mof_id = canonical_id(member.name)

                if mof_id not in master_ids:
                    continue

                if mof_id in submitted_ids:
                    raise RuntimeError(
                        f"Duplicate canonical CIF identifier in archive: {mof_id}"
                    )

                submitted_ids.add(mof_id)

                handle = archive.extractfile(member)

                if handle is None:
                    continue

                raw_bytes = handle.read()

                try:
                    text = raw_bytes.decode("utf-8", errors="strict")
                except UnicodeDecodeError as error:
                    records.append({
                        "mof_id": mof_id,
                        "cif_member_path": member.name,
                        "parse_ok": False,
                        "formula": pd.NA,
                        "n_structure_sites": np.nan,
                        "elements": pd.NA,
                        "metals": pd.NA,
                        "n_distinct_metals": np.nan,
                        "single_metal": pd.NA,
                        "metal_site_count": np.nan,
                        "raw_atom_rows": np.nan,
                        "raw_charge_rows": np.nan,
                        "raw_occupancy_rows": np.nan,
                        "charge_length_aligned": False,
                        "charge_numeric_fraction": np.nan,
                        "occupancy_weighted_charge_sum": np.nan,
                        "element_sets_match": False,
                        "n_disordered_sites": np.nan,
                        "warning_count": 0,
                        "error": f"UnicodeDecodeError: {error}"[:1000],
                    })
                    continue

                pending.add(executor.submit(parse_one, (mof_id, member.name, text)))
                submitted += 1

                if len(pending) >= MAX_PENDING:
                    pending = collect_finished(pending, records)
                if records and len(records) % CHECKPOINT_EVERY == 0:
                    save_checkpoint(records)
                    print(f"checkpoint: completed={len(records):,}; submitted={submitted:,}")

        while pending:
            pending = collect_finished(pending, records)
            if records and len(records) % CHECKPOINT_EVERY == 0:
                save_checkpoint(records)
                print(f"checkpoint: completed={len(records):,}; submitted={submitted:,}")

    result = pd.DataFrame(records).sort_values("mof_id").reset_index(drop=True)
    if result["mof_id"].duplicated().any():
        raise RuntimeError("Duplicate chemistry records")

    save_checkpoint(result.to_dict("records"))
    result.to_parquet(OUTPUT, index=False)
    failures = result.loc[~result["parse_ok"].fillna(False), ["mof_id", "cif_member_path", "error"]]
    failures.to_csv(FAILURES, index=False)

    observed_ids = set(result["mof_id"].astype(str))
    summary = pd.DataFrame([
        ("n_jobs", N_JOBS),
        ("expected_ARC_MOF_CIF_records", len(expected_ids)),
        ("chemistry_records_written", len(result)),
        ("successful_parses", int(result["parse_ok"].fillna(False).sum())),
        ("failed_parses", int((~result["parse_ok"].fillna(False)).sum())),
        ("charge_length_aligned", int(result["charge_length_aligned"].fillna(False).sum())),
        ("fully_numeric_charge_arrays", int(result["charge_numeric_fraction"].eq(1.0).sum())),
        ("element_sets_match", int(result["element_sets_match"].fillna(False).sum())),
        ("single_metal_frameworks", int(result["single_metal"].fillna(False).sum())),
        ("mixed_metal_frameworks", int(result["n_distinct_metals"].gt(1).sum())),
        ("expected_CIF_IDs_not_written", len(expected_ids - observed_ids)),
        ("unexpected_written_IDs", len(observed_ids - expected_ids)),
    ], columns=["metric", "value"])
    summary.to_csv(SUMMARY, index=False)
    print(summary.to_string(index=False))
    print("CrystalNN was not run. No missing scientific values were filled.")


if __name__ == "__main__":
    main()

