#!/usr/bin/env python3
"""
Project 7B Step 4 - Phase 2B2
Exact raw-CIF-row -> pymatgen-site bridge for selected-case REPEAT charges.

Scientific purpose
------------------
The frozen Step 3 charge audit established exact ROW ALIGNMENT among raw CIF:
  atom-site symbol / label / occupancy / REPEAT charge columns.

It did NOT establish that raw CIF row order == pymatgen Structure site order.

Phase 2B2 creates and audits that missing bridge using the SAME selected CIF:
  frozen atom_row
      -> raw CIF element + fractional coordinates
      -> one-to-one periodic coordinate match within the same element
      -> pymatgen site_index
      -> frozen REPEAT charge

Hard gates
----------
- same number of raw CIF atom rows, frozen charge rows, and pymatgen sites;
- exact element agreement between frozen row and raw CIF row;
- one-to-one element-constrained assignment;
- assigned periodic Cartesian distance <= 1e-3 Å for EVERY site;
- no same-element alternative site within 0.05 Å;
- 100% selected atoms mapped;
- recomputed framework/element charge summaries reproduce frozen summaries.

This does NOT create:
- linker/site chemical assignment,
- adsorption sites,
- oxidation states,
- charge transfer,
- causal mechanism,
- pore accessibility,
- directional substitution rules.

READ ONLY with respect to Steps 1-3.
"""

from __future__ import annotations

import json
import math
import re
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

TITLE = "PROJECT 7B STEP 4 - PHASE 2B2 EXACT CHARGE-SITE BRIDGE"

STRICT_DISTANCE_A = 1e-3
AMBIGUOUS_SECOND_NEIGHBOR_A = 0.05

SYMBOL_KEYS = [
    "_atom_site_type_symbol",
    "_atom_site_symbol",
]
LABEL_KEYS = [
    "_atom_site_label",
]
OCC_KEYS = [
    "_atom_site_occupancy",
]
FX_KEYS = ["_atom_site_fract_x"]
FY_KEYS = ["_atom_site_fract_y"]
FZ_KEYS = ["_atom_site_fract_z"]


def find_root(start: Path) -> Path:
    p = start.resolve()
    for cand in [p] + list(p.parents):
        if (cand / "Step 3 results").exists() and (cand / "Step 4 extension").exists():
            return cand
    raise RuntimeError("Could not locate Project 7B root.")


def norm_id(x) -> str:
    s = str(x).strip()
    if s.lower().endswith(".cif"):
        s = s[:-4]
    return s


def resolve_col(df: pd.DataFrame, candidates: list[str], required=False):
    lower = {str(c).lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    if required:
        raise RuntimeError(
            f"Could not resolve any of {candidates}. Available columns: {list(df.columns)}"
        )
    return None


def first(block, keys):
    for k in keys:
        if k in block.data:
            v = block.data[k]
            if isinstance(v, (list, tuple)):
                return k, list(v)
            return k, [v]
    return None, None


def clean_symbol(x) -> str:
    s = str(x).strip().strip("'\"")
    m = re.match(r"^([A-Z][a-z]?)", s)
    if not m:
        raise ValueError(f"Cannot parse element symbol from {x!r}")
    return m.group(1)


def cif_float(x) -> float:
    s = str(x).strip().strip("'\"")
    if s in {"?", ".", ""}:
        raise ValueError(f"Missing CIF numeric value: {x!r}")
    # Remove standard uncertainty, e.g. 0.1234(5)
    s = re.sub(r"(?<=\d)\(\d+\)$", "", s)
    try:
        return float(s)
    except ValueError:
        # Rare but valid fractional form
        return float(Fraction(s))


def find_selected_cifs(root: Path, frozen: Path, expected_ids: set[str]) -> dict[str, Path]:
    candidates = []
    for base in [
        frozen / "08_structures" / "cifs_selected",
        frozen / "08_structures",
        root / "analysis" / "final_structure_case_inspection" / "cifs",
    ]:
        if base.exists():
            candidates.extend(base.rglob("*.cif"))

    by_id = {}
    for p in candidates:
        stem = norm_id(p.stem)
        if stem in expected_ids and stem not in by_id:
            by_id[stem] = p

    missing = expected_ids - set(by_id)
    for mid in missing:
        hits = [p for p in candidates if mid in p.stem]
        if len(hits) == 1:
            by_id[mid] = hits[0]
    return by_id


def raw_cif_rows(path: Path) -> pd.DataFrame:
    from pymatgen.io.cif import CifFile

    raw = path.read_bytes()
    cf = CifFile.from_str(raw.decode("utf-8", "strict"))
    if len(cf.data) != 1:
        raise ValueError(f"Expected one CIF block, found {len(cf.data)}")
    block = next(iter(cf.data.values()))

    sk, symbols = first(block, SYMBOL_KEYS)
    lk, labels = first(block, LABEL_KEYS)
    ok, occ = first(block, OCC_KEYS)
    xk, xs = first(block, FX_KEYS)
    yk, ys = first(block, FY_KEYS)
    zk, zs = first(block, FZ_KEYS)

    if sk is None:
        raise ValueError("No raw CIF atom-site type-symbol column")
    if xk is None or yk is None or zk is None:
        raise ValueError("Raw CIF lacks fractional-coordinate atom-site columns")

    n = len(symbols)
    labels = labels if labels is not None else [None] * n
    occ = occ if occ is not None else [1.0] * n

    lengths = {
        "symbol": len(symbols),
        "label": len(labels),
        "occupancy": len(occ),
        "fract_x": len(xs),
        "fract_y": len(ys),
        "fract_z": len(zs),
    }
    if len(set(lengths.values())) != 1:
        raise ValueError(f"Raw CIF atom-loop length mismatch: {lengths}")

    return pd.DataFrame({
        "raw_atom_row": np.arange(n, dtype=int),
        "raw_label": [None if v is None else str(v) for v in labels],
        "raw_element": [clean_symbol(v) for v in symbols],
        "raw_occupancy": [cif_float(v) for v in occ],
        "raw_fract_x": [cif_float(v) for v in xs],
        "raw_fract_y": [cif_float(v) for v in ys],
        "raw_fract_z": [cif_float(v) for v in zs],
        "raw_symbol_column": sk,
        "raw_label_column": lk,
        "raw_occupancy_column": ok,
        "raw_fract_x_column": xk,
        "raw_fract_y_column": yk,
        "raw_fract_z_column": zk,
    })


def safe_pmg_symbol(site) -> str:
    try:
        return site.specie.symbol
    except Exception:
        els = list(site.species.elements)
        if len(els) != 1:
            raise ValueError(f"Disordered/multi-element site encountered: {site.species}")
        return els[0].symbol


def bridge_one(mof_id: str, cif_path: Path, frozen_rows: pd.DataFrame):
    from pymatgen.core import Structure
    from scipy.optimize import linear_sum_assignment

    raw = raw_cif_rows(cif_path).copy()
    st = Structure.from_file(str(cif_path))

    n_raw = len(raw)
    n_frozen = len(frozen_rows)
    n_pmg = len(st)
    if not (n_raw == n_frozen == n_pmg):
        raise ValueError(
            f"Row/site count mismatch: raw={n_raw}, frozen={n_frozen}, pymatgen={n_pmg}"
        )

    # Frozen Step 3 charge table is explicitly in raw CIF atom-row order.
    fr = frozen_rows.sort_values("atom_row").reset_index(drop=True).copy()
    expected_atom_rows = list(range(n_raw))
    actual_atom_rows = pd.to_numeric(fr["atom_row"], errors="raise").astype(int).tolist()
    if actual_atom_rows != expected_atom_rows:
        raise ValueError("Frozen atom_row is not contiguous raw-CIF row order 0..n-1")

    frozen_el = fr["element"].astype(str).tolist()
    raw_el = raw["raw_element"].astype(str).tolist()
    element_row_agreement = np.mean([a == b for a, b in zip(frozen_el, raw_el)])
    if element_row_agreement != 1.0:
        bad = [
            (i, a, b)
            for i, (a, b) in enumerate(zip(frozen_el, raw_el))
            if a != b
        ][:10]
        raise ValueError(
            f"Frozen/raw row element agreement is {element_row_agreement:.6f}; examples={bad}"
        )

    pmg_el = [safe_pmg_symbol(s) for s in st]
    if CounterLike(raw_el) != CounterLike(pmg_el):
        raise ValueError(
            f"Raw/pymatgen element multisets differ: raw={CounterLike(raw_el)}, pmg={CounterLike(pmg_el)}"
        )

    raw_frac = raw[["raw_fract_x", "raw_fract_y", "raw_fract_z"]].to_numpy(float)
    pmg_frac = np.array([s.frac_coords for s in st], dtype=float)

    mapping_rows = []

    for el in sorted(set(raw_el)):
        ridx = np.array([i for i, e in enumerate(raw_el) if e == el], dtype=int)
        pidx = np.array([i for i, e in enumerate(pmg_el) if e == el], dtype=int)

        if len(ridx) != len(pidx):
            raise ValueError(f"{el}: raw count {len(ridx)} != pymatgen count {len(pidx)}")

        dist = st.lattice.get_all_distances(raw_frac[ridx], pmg_frac[pidx])
        rr, cc = linear_sum_assignment(dist)

        if len(rr) != len(ridx):
            raise ValueError(f"{el}: incomplete Hungarian assignment")

        for local_r, local_c in zip(rr, cc):
            r = int(ridx[local_r])
            p = int(pidx[local_c])
            d = float(dist[local_r, local_c])

            same_row_distances = np.sort(dist[local_r])
            second = (
                float(same_row_distances[1])
                if len(same_row_distances) > 1
                else np.inf
            )
            ambiguous = bool(second < AMBIGUOUS_SECOND_NEIGHBOR_A)

            mapping_rows.append({
                "mof_id": mof_id,
                "raw_atom_row": r,
                "raw_label": raw.loc[r, "raw_label"],
                "element": el,
                "raw_occupancy": float(raw.loc[r, "raw_occupancy"]),
                "raw_fract_x": float(raw.loc[r, "raw_fract_x"]),
                "raw_fract_y": float(raw.loc[r, "raw_fract_y"]),
                "raw_fract_z": float(raw.loc[r, "raw_fract_z"]),
                "repeat_charge": float(fr.loc[r, "repeat_charge"]),
                "pymatgen_site_index": p,
                "pymatgen_element": pmg_el[p],
                "pymatgen_fract_x": float(pmg_frac[p, 0]),
                "pymatgen_fract_y": float(pmg_frac[p, 1]),
                "pymatgen_fract_z": float(pmg_frac[p, 2]),
                "mapping_distance_A": d,
                "second_nearest_same_element_A": second,
                "ambiguous_same_element_geometry": ambiguous,
            })

    m = pd.DataFrame(mapping_rows).sort_values("raw_atom_row").reset_index(drop=True)

    if len(m) != n_raw:
        raise ValueError(f"Mapped {len(m)} of {n_raw} atom rows")
    if m["pymatgen_site_index"].nunique() != n_pmg:
        raise ValueError("Pymatgen site assignment is not one-to-one")
    if m["raw_atom_row"].nunique() != n_raw:
        raise ValueError("Raw atom-row assignment is not one-to-one")
    if (m["element"] != m["pymatgen_element"]).any():
        raise ValueError("Element mismatch after coordinate assignment")
    if (m["mapping_distance_A"] > STRICT_DISTANCE_A).any():
        worst = m.nlargest(10, "mapping_distance_A")[
            ["raw_atom_row", "element", "pymatgen_site_index", "mapping_distance_A"]
        ].to_dict("records")
        raise ValueError(
            f"Mapping exceeds strict {STRICT_DISTANCE_A:g} Å tolerance; worst={worst}"
        )
    if m["ambiguous_same_element_geometry"].any():
        bad = m.loc[m["ambiguous_same_element_geometry"], [
            "raw_atom_row", "element", "pymatgen_site_index",
            "mapping_distance_A", "second_nearest_same_element_A"
        ]].head(10).to_dict("records")
        raise ValueError(
            f"Ambiguous same-element site mapping within "
            f"{AMBIGUOUS_SECOND_NEIGHBOR_A:g} Å; examples={bad}"
        )

    return m, st


def CounterLike(values):
    from collections import Counter
    return dict(sorted(Counter(values).items()))


def compare_summary(mapped: pd.DataFrame, fw_frozen: pd.DataFrame, el_frozen: pd.DataFrame):
    recomputed_fw = (
        mapped.groupby("mof_id", as_index=False)
        .agg(
            atom_rows=("raw_atom_row", "size"),
            charge_sum=("repeat_charge", "sum"),
            charge_mean=("repeat_charge", "mean"),
            charge_std=("repeat_charge", "std"),
            charge_min=("repeat_charge", "min"),
            charge_max=("repeat_charge", "max"),
        )
    )

    fw_id = resolve_col(fw_frozen, ["mof_id"], required=True)
    joined_fw = recomputed_fw.merge(
        fw_frozen, left_on="mof_id", right_on=fw_id, how="left", suffixes=("_recomputed", "_frozen")
    )

    fw_checks = []
    for _, r in joined_fw.iterrows():
        rec = {"mof_id": r["mof_id"]}
        for c in ["atom_rows", "charge_sum", "charge_mean", "charge_std", "charge_min", "charge_max"]:
            a = r.get(f"{c}_recomputed", np.nan)
            b = r.get(f"{c}_frozen", np.nan)
            if pd.isna(a) or pd.isna(b):
                rec[f"{c}_abs_error"] = np.nan
            else:
                rec[f"{c}_abs_error"] = abs(float(a) - float(b))
        fw_checks.append(rec)
    fw_check_df = pd.DataFrame(fw_checks)

    recomputed_el = (
        mapped.groupby(["mof_id", "element"], as_index=False)
        .agg(
            atom_rows=("raw_atom_row", "size"),
            charge_mean=("repeat_charge", "mean"),
            charge_median=("repeat_charge", "median"),
            charge_std=("repeat_charge", "std"),
            charge_min=("repeat_charge", "min"),
            charge_max=("repeat_charge", "max"),
        )
    )

    el_id = resolve_col(el_frozen, ["mof_id"], required=True)
    el_el = resolve_col(el_frozen, ["element"], required=True)
    joined_el = recomputed_el.merge(
        el_frozen,
        left_on=["mof_id", "element"],
        right_on=[el_id, el_el],
        how="left",
        suffixes=("_recomputed", "_frozen"),
    )

    el_checks = []
    for _, r in joined_el.iterrows():
        rec = {"mof_id": r["mof_id"], "element": r["element"]}
        for c in ["atom_rows", "charge_mean", "charge_median", "charge_std", "charge_min", "charge_max"]:
            a = r.get(f"{c}_recomputed", np.nan)
            b = r.get(f"{c}_frozen", np.nan)
            if pd.isna(a) and pd.isna(b):
                rec[f"{c}_abs_error"] = 0.0
            elif pd.isna(a) or pd.isna(b):
                rec[f"{c}_abs_error"] = np.nan
            else:
                rec[f"{c}_abs_error"] = abs(float(a) - float(b))
        el_checks.append(rec)
    el_check_df = pd.DataFrame(el_checks)

    return fw_check_df, el_check_df


def attach_to_phase2b(root: Path, mapped: pd.DataFrame, out: Path):
    phase2b = root / "Step 4 results" / "02_cif_chemistry" / "phase2b_selected_case_local_chemistry"
    nb_path = phase2b / "phase2b_crystalnn_first_shell_neighbors.csv"
    site_path = phase2b / "phase2b_crystalnn_metal_site_summary.csv"

    if not nb_path.exists() or not site_path.exists():
        return None, None, ["Phase 2B CrystalNN outputs were not found; charge bridge itself is still valid."]

    lookup = mapped[["mof_id", "pymatgen_site_index", "repeat_charge"]].copy()

    nb = pd.read_csv(nb_path, low_memory=False)
    nb = nb.drop(columns=[c for c in ["central_charge", "neighbor_charge"] if c in nb.columns])

    central = lookup.rename(columns={
        "pymatgen_site_index": "central_site_index",
        "repeat_charge": "central_repeat_charge_mapped",
    })
    neigh = lookup.rename(columns={
        "pymatgen_site_index": "neighbor_site_index",
        "repeat_charge": "neighbor_repeat_charge_mapped",
    })

    nb2 = nb.merge(central, on=["mof_id", "central_site_index"], how="left")
    nb2 = nb2.merge(neigh, on=["mof_id", "neighbor_site_index"], how="left")
    nb2.to_csv(out / "phase2b2_first_shell_neighbors_with_validated_repeat_charges.csv", index=False)

    site = pd.read_csv(site_path, low_memory=False)
    site = site.drop(columns=[c for c in ["central_charge", "mean_neighbor_charge"] if c in site.columns])
    site2 = site.merge(central, on=["mof_id", "central_site_index"], how="left")

    mean_neighbor = (
        nb2.groupby(["mof_id", "method", "central_site_index"], as_index=False)
        .agg(
            mapped_neighbor_charge_mean=("neighbor_repeat_charge_mapped", "mean"),
            mapped_neighbor_charge_median=("neighbor_repeat_charge_mapped", "median"),
            mapped_neighbor_charge_min=("neighbor_repeat_charge_mapped", "min"),
            mapped_neighbor_charge_max=("neighbor_repeat_charge_mapped", "max"),
            mapped_neighbor_charge_nonnull=("neighbor_repeat_charge_mapped", "count"),
        )
    )
    site2 = site2.merge(
        mean_neighbor,
        on=["mof_id", "method", "central_site_index"],
        how="left",
    )
    site2.to_csv(out / "phase2b2_metal_site_summary_with_validated_repeat_charges.csv", index=False)

    warnings = []
    central_missing = int(site2["central_repeat_charge_mapped"].isna().sum())
    neighbor_missing = int(nb2.loc[nb2["neighbor_site_index"] >= 0, "neighbor_repeat_charge_mapped"].isna().sum())
    if central_missing:
        warnings.append(f"{central_missing} metal-site rows lack mapped central charge.")
    if neighbor_missing:
        warnings.append(f"{neighbor_missing} first-shell neighbor rows lack mapped charge.")

    return nb2, site2, warnings


def main():
    print(TITLE)
    print("=" * 72)

    root = find_root(Path.cwd())
    frozen = root / "Step 3 results" / "Paper7B_Hosein_to_Shayan_Frozen_Source_Package"
    out = root / "Step 4 results" / "02_cif_chemistry" / "phase2b2_exact_charge_site_bridge"
    out.mkdir(parents=True, exist_ok=True)

    atom_path = frozen / "06_cif_chemistry" / "03_atom_charge_rows.csv"
    fw_path = frozen / "06_cif_chemistry" / "03_framework_charge_summaries.csv"
    el_path = frozen / "06_cif_chemistry" / "03_element_charge_summaries.csv"
    case_fw_path = frozen / "08_structures" / "02_final_case_frameworks.csv"

    for p in [atom_path, fw_path, el_path, case_fw_path]:
        if not p.exists():
            raise RuntimeError(f"Missing frozen source: {p}")

    atom = pd.read_csv(atom_path, low_memory=False)
    fw_frozen = pd.read_csv(fw_path, low_memory=False)
    el_frozen = pd.read_csv(el_path, low_memory=False)
    case_fw = pd.read_csv(case_fw_path, low_memory=False)

    case_mof_col = resolve_col(case_fw, ["mof_id", "framework_id", "framework", "mof"], required=True)
    expected = {norm_id(v) for v in case_fw[case_mof_col].dropna().astype(str)}

    atom_mof_col = resolve_col(atom, ["mof_id"], required=True)
    required_atom_cols = ["atom_row", "element", "repeat_charge"]
    for c in required_atom_cols:
        if c not in atom.columns:
            raise RuntimeError(f"Frozen atom-charge table missing {c}")

    cifs = find_selected_cifs(root, frozen, expected)

    fatal = []
    warnings = []
    mapped_parts = []
    audit_rows = []

    if len(cifs) != len(expected):
        fatal.append(f"Resolved {len(cifs)} CIFs for {len(expected)} selected frameworks.")

    if not fatal:
        for mid in sorted(expected):
            try:
                fr = atom[atom[atom_mof_col].astype(str).map(norm_id).eq(mid)].copy()
                m, st = bridge_one(mid, cifs[mid], fr)
                mapped_parts.append(m)

                audit_rows.append({
                    "mof_id": mid,
                    "cif_path": str(cifs[mid].relative_to(root)),
                    "raw_rows": len(m),
                    "mapped_rows": len(m),
                    "unique_pymatgen_sites": int(m["pymatgen_site_index"].nunique()),
                    "max_mapping_distance_A": float(m["mapping_distance_A"].max()),
                    "median_mapping_distance_A": float(m["mapping_distance_A"].median()),
                    "minimum_second_nearest_same_element_A": float(
                        m["second_nearest_same_element_A"].replace(np.inf, np.nan).min()
                    ) if np.isfinite(
                        m["second_nearest_same_element_A"].replace(np.inf, np.nan)
                    ).any() else np.inf,
                    "ambiguous_rows": int(m["ambiguous_same_element_geometry"].sum()),
                    "mapping_pass": True,
                })

            except Exception as exc:
                fatal.append(f"{mid}: {type(exc).__name__}: {exc}")
                audit_rows.append({
                    "mof_id": mid,
                    "cif_path": str(cifs.get(mid, "")),
                    "mapping_pass": False,
                    "error": f"{type(exc).__name__}: {exc}",
                })

    mapped = pd.concat(mapped_parts, ignore_index=True) if mapped_parts else pd.DataFrame()
    audit = pd.DataFrame(audit_rows)

    if not mapped.empty:
        mapped.to_csv(out / "phase2b2_raw_cif_to_pymatgen_charge_map.csv", index=False)
    audit.to_csv(out / "phase2b2_framework_mapping_audit.csv", index=False)

    fw_check = pd.DataFrame()
    el_check = pd.DataFrame()

    if not fatal and not mapped.empty:
        fw_check, el_check = compare_summary(mapped, fw_frozen, el_frozen)
        fw_check.to_csv(out / "phase2b2_framework_summary_reproduction.csv", index=False)
        el_check.to_csv(out / "phase2b2_element_summary_reproduction.csv", index=False)

        # Exact reproduction gates with floating tolerance
        err_cols_fw = [c for c in fw_check.columns if c.endswith("_abs_error")]
        err_cols_el = [c for c in el_check.columns if c.endswith("_abs_error")]

        fw_max = float(np.nanmax(fw_check[err_cols_fw].to_numpy(float))) if err_cols_fw else 0.0
        el_max = float(np.nanmax(el_check[err_cols_el].to_numpy(float))) if err_cols_el else 0.0

        # Values are derived from the identical frozen charge rows. Errors should be floating noise only.
        if fw_max > 1e-10:
            fatal.append(f"Framework charge-summary reproduction max absolute error is {fw_max:.3e}.")
        if el_max > 1e-10:
            fatal.append(f"Element charge-summary reproduction max absolute error is {el_max:.3e}.")

        nb2, site2, attach_warnings = attach_to_phase2b(root, mapped, out)
        warnings.extend(attach_warnings)

    # Final permission explicitly separates charge mapping from mechanism interpretation.
    decision = "PASS" if not fatal else "FAIL"
    permission = (
        "SITE_LEVEL_REPEAT_CHARGE_ATTACHMENT_VALIDATED_FOR_SELECTED_CASE_STRUCTURAL_DESCRIPTION"
        if decision == "PASS"
        else "SITE_LEVEL_CHARGES_REMAIN_QUARANTINED"
    )

    evidence = pd.DataFrame([
        {
            "object": "mapped REPEAT charge on selected-case pymatgen site",
            "status_if_phase_passes": "VALIDATED_DESCRIPTIVE",
            "allowed": "site-level partial-charge annotation and first-shell charge fingerprint in the six frozen cases",
            "not_allowed": "oxidation state, charge transfer, adsorption-site assignment, causal electrostatic mechanism",
        },
        {
            "object": "mapped REPEAT charge on CrystalNN neighbor",
            "status_if_phase_passes": "VALIDATED_DESCRIPTIVE",
            "allowed": "descriptive local electrostatic fingerprint where CrystalNN shell itself is robust",
            "not_allowed": "claim that the neighbor is guest-accessible or is a preferred binding site",
        },
        {
            "object": "linker-local charge change",
            "status_if_phase_passes": "NOT_ESTABLISHED",
            "allowed": "none without an explicit linker atom mapping",
            "not_allowed": "automatic attribution of charge difference to the changed linker",
        },
    ])
    evidence.to_csv(out / "phase2b2_charge_evidence_boundaries.csv", index=False)

    summary = {
        "decision": decision,
        "permission": permission,
        "selected_frameworks": len(expected),
        "selected_cifs": len(cifs),
        "mapped_atom_rows": int(len(mapped)),
        "expected_frozen_atom_rows": int(
            atom[atom[atom_mof_col].astype(str).map(norm_id).isin(expected)].shape[0]
        ),
        "strict_distance_tolerance_A": STRICT_DISTANCE_A,
        "ambiguity_second_neighbor_threshold_A": AMBIGUOUS_SECOND_NEIGHBOR_A,
        "fatal": fatal,
        "warnings": warnings,
    }
    (out / "phase2b2_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Decision: {decision}")
    print(f"Selected frameworks: {len(expected)}")
    print(f"Selected CIFs resolved: {len(cifs)}")
    print(f"Mapped atom rows: {len(mapped)}")
    if not mapped.empty:
        print(f"Unique pymatgen sites mapped: {mapped[['mof_id','pymatgen_site_index']].drop_duplicates().shape[0]}")
        print(f"Maximum mapping distance: {mapped['mapping_distance_A'].max():.6g} Å")
        finite_second = mapped["second_nearest_same_element_A"].replace(np.inf, np.nan).dropna()
        if len(finite_second):
            print(f"Minimum second-nearest same-element distance: {finite_second.min():.6g} Å")
        print(f"Ambiguous mappings: {int(mapped['ambiguous_same_element_geometry'].sum())}")

    if not fw_check.empty:
        errcols = [c for c in fw_check.columns if c.endswith("_abs_error")]
        print(
            "Framework summary reproduction max error: "
            f"{np.nanmax(fw_check[errcols].to_numpy(float)):.3e}"
        )
    if not el_check.empty:
        errcols = [c for c in el_check.columns if c.endswith("_abs_error")]
        print(
            "Element summary reproduction max error: "
            f"{np.nanmax(el_check[errcols].to_numpy(float)):.3e}"
        )

    print(f"Permission: {permission}")
    for w in warnings:
        print(f"WARN: {w}")
    for f in fatal:
        print(f"FATAL: {f}")

    print(
        "No linker assignment, adsorption-site inference, oxidation state, charge-transfer "
        "claim, adsorption effect, matching, bootstrap, or process metric was computed."
    )
    print(f"Outputs: {out}")

    if decision != "PASS":
        sys.exit(2)


if __name__ == "__main__":
    main()
