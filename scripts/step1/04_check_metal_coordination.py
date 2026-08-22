#!/usr/bin/env python3
"""Targeted CrystalNN check for geometry-accepted full-cohort metal pairs.

Uses the two CrystalNN settings validated in the pilot. Only frameworks appearing
in accepted metal pairs are parsed. No adsorption outcomes are used. No missing
values are filled. Pair classifications are:
- coordination_compatible: signatures agree between pair members under both settings
- coordination_changing: signatures differ under both settings
- coordination_ambiguous: one setting agrees and the other differs
- coordination_unavailable: parsing or site assignment is incomplete
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path
import json
import os
import tarfile
import warnings

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
ANALYSIS = ROOT / "analysis"
PAIR_FILE = ANALYSIS / "full_pair_rules" / "metal_substitution.parquet"
ARCHIVE = RAW / "ARCMOF_20241004.tar.gz"
WORK = ANALYSIS / "metal_coordination_work"
WORK.mkdir(parents=True, exist_ok=True)

CHECKPOINT = WORK / "coordination_signatures_checkpoint.csv"
SIGNATURE_FILE = ANALYSIS / "metal_coordination_signatures.parquet"
PAIR_OUTPUT = ANALYSIS / "metal_pairs_coordination_classified.parquet"
SUMMARY_OUTPUT = ANALYSIS / "metal_pair_coordination_summary.csv"
FAILURE_OUTPUT = ANALYSIS / "metal_coordination_failures.csv"

N_JOBS = 6
MAX_PENDING = 12
CHECKPOINT_EVERY = 500


def canonical_id(value: str) -> str:
    name = Path(str(value).strip()).name
    if name.lower().endswith(".cif"):
        name = name[:-4]
    if name.lower().endswith("_repeat"):
        name = name[:-7]
    return name


def parse_coordination(payload):
    mof_id, member_name, text = payload
    from pymatgen.core import Element
    from pymatgen.io.cif import CifParser
    from pymatgen.analysis.local_env import CrystalNN

    def is_metal(symbol):
        try:
            return bool(Element(symbol).is_metal)
        except Exception:
            return False

    record = {
        "mof_id": mof_id,
        "member_path": member_name,
        "status": "unavailable",
        "metal": pd.NA,
        "metal_site_count": 0,
        "default_signature": pd.NA,
        "geometry_signature": pd.NA,
        "within_framework_stable": False,
        "default_warning_count": 0,
        "geometry_warning_count": 0,
        "failed_site_count": 0,
        "error": pd.NA,
    }

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            structures = CifParser.from_str(text).parse_structures(primitive=False)
        if not structures:
            raise ValueError("Pymatgen returned no structure")
        structure = structures[0]

        metal_sites = []
        metal_symbols = set()
        for index, site in enumerate(structure):
            if not site.is_ordered:
                continue
            symbol = site.specie.symbol
            if is_metal(symbol):
                metal_sites.append(index)
                metal_symbols.add(symbol)

        if not metal_sites:
            raise ValueError("No ordered metal sites detected")
        if len(metal_symbols) != 1:
            raise ValueError(f"Expected one metal identity, found {sorted(metal_symbols)}")

        default_cnn = CrystalNN()
        geometry_cnn = CrystalNN(x_diff_weight=0, porous_adjustment=False)
        default_values = []
        geometry_values = []
        default_warning_count = 0
        geometry_warning_count = 0
        failed_sites = 0

        for index in metal_sites:
            try:
                with warnings.catch_warnings(record=True) as caught_default:
                    warnings.simplefilter("always")
                    default_values.append(len(default_cnn.get_nn_info(structure, index)))
                with warnings.catch_warnings(record=True) as caught_geometry:
                    warnings.simplefilter("always")
                    geometry_values.append(len(geometry_cnn.get_nn_info(structure, index)))
                default_warning_count += len(caught_default)
                geometry_warning_count += len(caught_geometry)
            except Exception:
                failed_sites += 1

        if failed_sites or len(default_values) != len(metal_sites) or len(geometry_values) != len(metal_sites):
            raise ValueError(f"Incomplete site assignments: failed={failed_sites}, total={len(metal_sites)}")

        default_signature = ";".join(map(str, sorted(default_values)))
        geometry_signature = ";".join(map(str, sorted(geometry_values)))
        record.update({
            "status": "ok",
            "metal": next(iter(metal_symbols)),
            "metal_site_count": len(metal_sites),
            "default_signature": default_signature,
            "geometry_signature": geometry_signature,
            "within_framework_stable": default_signature == geometry_signature,
            "default_warning_count": default_warning_count,
            "geometry_warning_count": geometry_warning_count,
            "failed_site_count": 0,
        })
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"[:1000]
    return record


def save_checkpoint(records):
    pd.DataFrame(records).sort_values("mof_id").to_csv(CHECKPOINT, index=False)


def collect_one(pending, records, done_ids):
    completed, pending = wait(pending, return_when=FIRST_COMPLETED)
    for future in completed:
        record = future.result()
        if record["mof_id"] not in done_ids:
            records.append(record)
            done_ids.add(record["mof_id"])
    return pending


def classify(row):
    if row["status_a"] != "ok" or row["status_b"] != "ok":
        return "coordination_unavailable"
    default_match = row["default_signature_a"] == row["default_signature_b"]
    geometry_match = row["geometry_signature_a"] == row["geometry_signature_b"]
    if default_match and geometry_match:
        return "coordination_compatible"
    if (not default_match) and (not geometry_match):
        return "coordination_changing"
    return "coordination_ambiguous"


def main():
    if not PAIR_FILE.exists() or not ARCHIVE.exists():
        raise FileNotFoundError("Missing accepted metal-pair table or CIF archive")

    pairs = pd.read_parquet(PAIR_FILE)
    if pairs[["pair_lo", "pair_hi"]].duplicated().any():
        raise RuntimeError("Duplicate unordered metal pairs")
    wanted_ids = set(pairs["id_a"].astype(str)) | set(pairs["id_b"].astype(str))

    if CHECKPOINT.exists():
        CHECKPOINT.unlink()

    records = []
    done_ids = set()

    pending_ids = wanted_ids - done_ids
    print(
        f"N_JOBS={N_JOBS}; accepted_metal_pairs={len(pairs):,}; "
        f"unique_frameworks={len(wanted_ids):,}; remaining_frameworks={len(pending_ids):,}"
    )

    pending = set()
    submitted = 0
    last_checkpoint = len(records)

    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:
        with tarfile.open(ARCHIVE, "r:gz") as archive:
            for member in archive:
                if not member.isfile() or not member.name.lower().endswith(".cif"):
                    continue
                mof_id = canonical_id(member.name)
                if mof_id not in pending_ids:
                    continue

                handle = archive.extractfile(member)
                if handle is None:
                    continue

                try:
                    text = handle.read().decode("utf-8", errors="strict")
                except UnicodeDecodeError as error:
                    records.append({
                        "mof_id": mof_id,
                        "member_path": member.name,
                        "status": "unavailable",
                        "metal": pd.NA,
                        "metal_site_count": 0,
                        "default_signature": pd.NA,
                        "geometry_signature": pd.NA,
                        "within_framework_stable": False,
                        "default_warning_count": 0,
                        "geometry_warning_count": 0,
                        "failed_site_count": 0,
                        "error": f"UnicodeDecodeError: {error}"[:1000],
                    })
                    done_ids.add(mof_id)
                    continue

                pending.add(
                    executor.submit(
                        parse_coordination,
                        (mof_id, member.name, text),
                    )
                )
                submitted += 1

                if len(pending) >= MAX_PENDING:
                    pending = collect_one(pending, records, done_ids)
                if len(records) - last_checkpoint >= CHECKPOINT_EVERY:
                    save_checkpoint(records)
                    last_checkpoint = len(records)
                    print(f"checkpoint: completed_frameworks={len(records):,}; submitted={submitted:,}")

        while pending:
            pending = collect_one(pending, records, done_ids)
            if len(records) - last_checkpoint >= CHECKPOINT_EVERY:
                save_checkpoint(records)
                last_checkpoint = len(records)
                print(f"checkpoint: completed_frameworks={len(records):,}; submitted={submitted:,}")

    save_checkpoint(records)
    signatures = pd.DataFrame(records).sort_values("mof_id").reset_index(drop=True)
    if signatures["mof_id"].duplicated().any():
        raise RuntimeError("Duplicate framework coordination signatures")
    signatures.to_parquet(SIGNATURE_FILE, index=False)

    left = signatures.add_suffix("_a").rename(columns={"mof_id_a": "id_a"})
    right = signatures.add_suffix("_b").rename(columns={"mof_id_b": "id_b"})
    classified = (
        pairs.merge(left, on="id_a", how="left", validate="many_to_one")
             .merge(right, on="id_b", how="left", validate="many_to_one")
    )
    classified["coordination_class"] = classified.apply(classify, axis=1)
    classified.to_parquet(PAIR_OUTPUT, index=False)

    summary = (
        classified.groupby(["geometry_tier", "coordination_class"], as_index=False)
        .agg(
            pairs=("pair_lo", "size"),
            unique_frameworks_a=("id_a", "nunique"),
            unique_frameworks_b=("id_b", "nunique"),
        )
        .sort_values(["geometry_tier", "coordination_class"])
    )
    summary.to_csv(SUMMARY_OUTPUT, index=False)
    signatures.loc[signatures["status"] != "ok"].to_csv(FAILURE_OUTPUT, index=False)

    print(summary.to_string(index=False))
    print(f"\nFramework assignments successful: {(signatures['status'] == 'ok').sum():,}/{len(signatures):,}")
    print(f"Saved signatures: {SIGNATURE_FILE}")
    print(f"Saved classified pairs: {PAIR_OUTPUT}")
    print(f"Saved summary: {SUMMARY_OUTPUT}")
    print("Adsorption outcomes were not used. No missing values were filled.")


if __name__ == "__main__":
    main()

