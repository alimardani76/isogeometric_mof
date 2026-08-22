#!/usr/bin/env python3
"""
Project 7B Step 4 - Phase 2B
Selected-case CIF/local-chemistry extension.

Purpose
-------
Compute a narrowly defined, auditable chemistry description for the SIX FROZEN
structure cases without changing pair selection, adsorption effects, matching,
bootstrap inference, or process metrics.

Primary objects:
1. Exact original CrystalNN setting A: CrystalNN()
2. Exact original CrystalNN setting B: CrystalNN(x_diff_weight=0,
   porous_adjustment=False)
3. Independent geometry-only ChemEnv cross-check on metal sites
4. First-shell element/distance/REPEAT-charge summaries
5. Whole-framework heteroatom and charge fingerprints
6. Pair-level descriptive chemistry cards and evidence-boundary decisions

Important claim boundary
------------------------
These outputs describe structural/local-chemical context. They DO NOT establish:
- adsorption sites,
- oxidation states,
- charge transfer,
- a causal mechanism,
- a directional substitution rule,
- pore accessibility of a specific atom.

READ ONLY with respect to Steps 1-3.
"""

from __future__ import annotations

import json
import math
import re
import sys
import traceback
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

TITLE = "PROJECT 7B STEP 4 - PHASE 2B SELECTED-CASE LOCAL CHEMISTRY"


def find_project_root(start: Path) -> Path:
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


def resolve_col(df: pd.DataFrame, candidates: list[str], required: bool = False) -> str | None:
    lower = {str(c).lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    for actual in df.columns:
        al = str(actual).lower()
        for c in candidates:
            if c.lower() in al:
                return actual
    if required:
        raise RuntimeError(f"Could not resolve column from candidates {candidates}. Available: {list(df.columns)}")
    return None


def safe_symbol(site) -> str:
    # Selected CIFs are expected to be ordered, but keep this robust.
    try:
        return site.specie.symbol
    except Exception:
        els = list(site.species.elements)
        if not els:
            return "?"
        return els[0].symbol


def is_metal_symbol(symbol: str) -> bool:
    from pymatgen.core import Element
    try:
        return bool(Element(symbol).is_metal)
    except Exception:
        return False


HALOGENS = {"F", "Cl", "Br", "I", "At", "Ts"}
HETERO = {"N", "O", "S", "P", "F", "Cl", "Br", "I"}


def element_counter_string(symbols) -> str:
    c = Counter(symbols)
    return ";".join(f"{k}:{c[k]}" for k in sorted(c))


def jaccard(a, b) -> float:
    a = set(a)
    b = set(b)
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def find_selected_cifs(frozen: Path, expected_ids: set[str]) -> dict[str, Path]:
    candidates = []
    for base in [
        frozen / "08_structures" / "cifs_selected",
        frozen / "08_structures",
    ]:
        if base.exists():
            candidates.extend(base.rglob("*.cif"))

    # Fallback to the original analysis folder only when frozen package lacks a CIF.
    root = frozen.parents[1]
    fallback = root / "analysis" / "final_structure_case_inspection" / "cifs"
    if fallback.exists():
        candidates.extend(fallback.rglob("*.cif"))

    by_id = {}
    for p in candidates:
        stem = norm_id(p.stem)
        if stem in expected_ids and stem not in by_id:
            by_id[stem] = p

    # Conservative secondary matching, useful when selected CIF filenames have a wrapper.
    missing = expected_ids - set(by_id)
    for mid in list(missing):
        hits = [p for p in candidates if mid == norm_id(p.name) or mid in p.stem]
        if len(hits) == 1:
            by_id[mid] = hits[0]

    return by_id


def build_case_mapping(case_set: pd.DataFrame, case_frameworks: pd.DataFrame):
    pair_col_set = resolve_col(case_set, ["pair_id", "pair"])
    pair_col_fw = resolve_col(case_frameworks, ["pair_id", "pair"])
    mof_col_fw = resolve_col(case_frameworks, ["mof_id", "framework_id", "framework", "mof"], required=True)

    role_col = resolve_col(case_set, ["case_role", "role", "selection_role", "case_label"])
    intervention_col = resolve_col(case_set, ["intervention", "intervention_class", "change_type"])
    a_col = resolve_col(case_set, ["mof_a", "mof_id_a", "framework_a", "framework_id_a", "left_mof"])
    b_col = resolve_col(case_set, ["mof_b", "mof_id_b", "framework_b", "framework_id_b", "right_mof"])

    rows = []
    if pair_col_set and a_col and b_col:
        for _, r in case_set.iterrows():
            rows.append({
                "pair_id": str(r[pair_col_set]),
                "mof_a": norm_id(r[a_col]),
                "mof_b": norm_id(r[b_col]),
                "case_role": str(r[role_col]) if role_col else "",
                "intervention": str(r[intervention_col]) if intervention_col else "",
            })
    elif pair_col_fw:
        grouped = case_frameworks.groupby(pair_col_fw, dropna=False)
        for pid, g in grouped:
            ids = [norm_id(v) for v in g[mof_col_fw].dropna().astype(str).tolist()]
            ids = list(dict.fromkeys(ids))
            if len(ids) != 2:
                continue
            role = ""
            intervention = ""
            if pair_col_set and str(pid) in set(case_set[pair_col_set].astype(str)):
                rr = case_set[case_set[pair_col_set].astype(str).eq(str(pid))].iloc[0]
                role = str(rr[role_col]) if role_col else ""
                intervention = str(rr[intervention_col]) if intervention_col else ""
            rows.append({
                "pair_id": str(pid),
                "mof_a": ids[0],
                "mof_b": ids[1],
                "case_role": role,
                "intervention": intervention,
            })
    else:
        raise RuntimeError("Could not recover frozen pair-to-framework mapping.")

    return pd.DataFrame(rows)


def prepare_charge_table(charge_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    mof_col = resolve_col(charge_df, ["mof_id", "framework_id", "framework", "mof"], required=True)
    idx_col = resolve_col(charge_df, ["site_index", "atom_index", "site_idx", "atom_idx", "index"])
    elem_col = resolve_col(charge_df, ["element", "symbol", "atom_symbol", "species"])
    charge_col = resolve_col(charge_df, ["charge", "repeat_charge", "partial_charge", "q"], required=True)
    label_col = resolve_col(charge_df, ["site_label", "atom_label", "label"])

    x = charge_df.copy()
    x["_mof_id"] = x[mof_col].astype(str).map(norm_id)
    if idx_col is not None:
        x["_site_index"] = pd.to_numeric(x[idx_col], errors="coerce").astype("Int64")
    else:
        x["_site_index"] = x.groupby("_mof_id").cumcount().astype("Int64")
    x["_charge"] = pd.to_numeric(x[charge_col], errors="coerce")
    if elem_col:
        x["_element"] = x[elem_col].astype(str)
    else:
        x["_element"] = ""
    if label_col:
        x["_label"] = x[label_col].astype(str)
    else:
        x["_label"] = ""

    meta = {
        "mof_col": mof_col,
        "idx_col": idx_col,
        "elem_col": elem_col,
        "charge_col": charge_col,
        "label_col": label_col,
    }
    return x, meta


def charge_lookup_for_mof(charges: pd.DataFrame, mof_id: str, nsites: int, symbols: list[str]):
    sub = charges[charges["_mof_id"].eq(mof_id)].copy().sort_values("_site_index")
    if len(sub) != nsites:
        return {}, {
            "charge_rows": len(sub),
            "site_count": nsites,
            "row_alignment": False,
            "element_alignment_fraction": np.nan,
        }

    idxs = sub["_site_index"].astype(int).tolist()
    if idxs == list(range(1, nsites + 1)):
        sub["_site_index0"] = sub["_site_index"].astype(int) - 1
    elif idxs == list(range(0, nsites)):
        sub["_site_index0"] = sub["_site_index"].astype(int)
    else:
        # Phase 2A already checked row alignment. If explicit indices are unusual,
        # use row order but flag that this was required.
        sub["_site_index0"] = np.arange(nsites)

    lookup = dict(zip(sub["_site_index0"].astype(int), sub["_charge"].astype(float)))
    if sub["_element"].astype(str).str.len().gt(0).any():
        mapped = sub.sort_values("_site_index0")["_element"].astype(str).tolist()
        matches = []
        for a, b in zip(mapped, symbols):
            aa = re.sub(r"[^A-Za-z]", "", a)
            matches.append(aa.startswith(b) or b.startswith(aa))
        elem_frac = float(np.mean(matches)) if matches else np.nan
    else:
        elem_frac = np.nan

    return lookup, {
        "charge_rows": len(sub),
        "site_count": nsites,
        "row_alignment": True,
        "element_alignment_fraction": elem_frac,
    }


def run_crystalnn(structure, mof_id: str, charge_lookup: dict, metal_indices: list[int]):
    from pymatgen.analysis.local_env import CrystalNN

    settings = {
        "default": CrystalNN(),
        "neutral_no_porous": CrystalNN(x_diff_weight=0, porous_adjustment=False),
    }

    neighbor_rows = []
    site_rows = []

    for method_name, cnn in settings.items():
        for i in metal_indices:
            central = structure[i]
            central_symbol = safe_symbol(central)
            try:
                infos = cnn.get_nn_info(structure, i)
                error = ""
            except Exception as exc:
                infos = []
                error = f"{type(exc).__name__}: {exc}"

            neighbor_indices = []
            neighbor_symbols = []
            distances = []
            weights = []

            for nn in infos:
                nsite = nn.get("site")
                j = nn.get("site_index")
                if j is None and nsite is not None:
                    # Do not attempt fuzzy site matching. Keep missing index explicit.
                    j = -1
                try:
                    j_int = int(j)
                except Exception:
                    j_int = -1

                nsym = safe_symbol(nsite) if nsite is not None else "?"
                try:
                    dist = float(central.distance(nsite))
                except Exception:
                    dist = np.nan
                try:
                    weight = float(nn.get("weight", np.nan))
                except Exception:
                    weight = np.nan

                neighbor_indices.append(j_int)
                neighbor_symbols.append(nsym)
                distances.append(dist)
                weights.append(weight)

                neighbor_rows.append({
                    "mof_id": mof_id,
                    "method": method_name,
                    "central_site_index": i,
                    "central_element": central_symbol,
                    "central_charge": charge_lookup.get(i, np.nan),
                    "neighbor_site_index": j_int,
                    "neighbor_element": nsym,
                    "neighbor_charge": charge_lookup.get(j_int, np.nan) if j_int >= 0 else np.nan,
                    "distance_A": dist,
                    "crystalnn_weight": weight,
                    "neighbor_is_heteroatom": nsym in HETERO,
                    "neighbor_is_halogen": nsym in HALOGENS,
                    "neighbor_is_metal": is_metal_symbol(nsym),
                })

            site_rows.append({
                "mof_id": mof_id,
                "method": method_name,
                "central_site_index": i,
                "central_element": central_symbol,
                "central_charge": charge_lookup.get(i, np.nan),
                "coordination_number": len(infos),
                "weighted_coordination_sum": float(np.nansum(weights)) if weights else 0.0,
                "neighbor_indices_json": json.dumps(neighbor_indices),
                "neighbor_elements": element_counter_string(neighbor_symbols),
                "neighbor_elements_json": json.dumps(neighbor_symbols),
                "mean_neighbor_distance_A": float(np.nanmean(distances)) if distances else np.nan,
                "max_neighbor_distance_A": float(np.nanmax(distances)) if distances else np.nan,
                "n_N": int(sum(s == "N" for s in neighbor_symbols)),
                "n_O": int(sum(s == "O" for s in neighbor_symbols)),
                "n_S": int(sum(s == "S" for s in neighbor_symbols)),
                "n_P": int(sum(s == "P" for s in neighbor_symbols)),
                "n_halogen": int(sum(s in HALOGENS for s in neighbor_symbols)),
                "mean_neighbor_charge": float(np.nanmean(
                    [charge_lookup.get(j, np.nan) for j in neighbor_indices if j >= 0]
                )) if neighbor_indices else np.nan,
                "error": error,
            })

    site_df = pd.DataFrame(site_rows)
    neighbor_df = pd.DataFrame(neighbor_rows)

    robustness = []
    for i in metal_indices:
        a = site_df[(site_df["central_site_index"].eq(i)) & (site_df["method"].eq("default"))]
        b = site_df[(site_df["central_site_index"].eq(i)) & (site_df["method"].eq("neutral_no_porous"))]
        if a.empty or b.empty:
            continue
        a = a.iloc[0]
        b = b.iloc[0]
        ai = json.loads(a["neighbor_indices_json"])
        bi = json.loads(b["neighbor_indices_json"])
        ae = Counter(json.loads(a["neighbor_elements_json"]))
        be = Counter(json.loads(b["neighbor_elements_json"]))
        exact = sorted(ai) == sorted(bi)
        same_elements = ae == be
        same_cn = int(a["coordination_number"]) == int(b["coordination_number"])

        if exact and same_cn:
            status = "ROBUST_EXACT_SHELL"
        elif same_elements and same_cn:
            status = "ROBUST_ELEMENT_SHELL"
        else:
            status = "METHOD_SENSITIVE"

        robustness.append({
            "mof_id": mof_id,
            "central_site_index": i,
            "central_element": a["central_element"],
            "default_cn": int(a["coordination_number"]),
            "neutral_cn": int(b["coordination_number"]),
            "same_cn": same_cn,
            "same_element_multiset": same_elements,
            "exact_neighbor_index_set": exact,
            "neighbor_index_jaccard": jaccard(ai, bi),
            "coordination_robustness_status": status,
        })

    return site_df, neighbor_df, pd.DataFrame(robustness)


def run_chemenv(structure, mof_id: str, metal_indices: list[int]):
    """
    Geometry-only ChemEnv cross-check.

    We intentionally:
      - preserve site indexing (structure_refinement='none'),
      - avoid inferred oxidation states (valences='undefined'),
      - analyze only the metal sites,
      - use SimplestChemenvStrategy with the standard 1.4 / 0.3 geometry cutoffs,
      - disable the valence-based additional condition.
    """
    from pymatgen.analysis.chemenv.coordination_environments.coordination_geometry_finder import LocalGeometryFinder
    from pymatgen.analysis.chemenv.coordination_environments.chemenv_strategies import SimplestChemenvStrategy
    from pymatgen.analysis.chemenv.coordination_environments.structure_environments import LightStructureEnvironments

    rows = []
    if not metal_indices:
        return pd.DataFrame(rows)

    try:
        lgf = LocalGeometryFinder()
        lgf.setup_parameters(structure_refinement="none")
        lgf.setup_structure(structure=structure)
        se = lgf.compute_structure_environments(
            only_indices=metal_indices,
            only_cations=False,
            valences="undefined",
            maximum_distance_factor=2.0,
            minimum_angle_factor=0.05,
        )
        strategy = SimplestChemenvStrategy(
            distance_cutoff=1.4,
            angle_cutoff=0.3,
            additional_condition=0,
        )
        lse = LightStructureEnvironments.from_structure_environments(
            strategy=strategy,
            structure_environments=se,
        )

        for i in metal_indices:
            ces = None
            try:
                ces = lse.coordination_environments[i]
            except Exception:
                ces = None

            if not ces:
                rows.append({
                    "mof_id": mof_id,
                    "central_site_index": i,
                    "central_element": safe_symbol(structure[i]),
                    "ce_symbol": "",
                    "ce_fraction": np.nan,
                    "csm": np.nan,
                    "chemenv_status": "NO_ENVIRONMENT",
                    "error": "",
                })
                continue

            # Usually a unique environment for SimplestChemenvStrategy.
            for ce in ces:
                if ce is None:
                    continue
                rows.append({
                    "mof_id": mof_id,
                    "central_site_index": i,
                    "central_element": safe_symbol(structure[i]),
                    "ce_symbol": str(ce.get("ce_symbol", "")),
                    "ce_fraction": float(ce.get("ce_fraction", np.nan)) if ce.get("ce_fraction", None) is not None else np.nan,
                    "csm": float(ce.get("csm", np.nan)) if ce.get("csm", None) is not None else np.nan,
                    "chemenv_status": "OK",
                    "error": "",
                })

    except Exception as exc:
        # Do not fail the whole chemistry phase merely because ChemEnv cannot classify
        # one large porous structure. That becomes explicit method sensitivity.
        rows.append({
            "mof_id": mof_id,
            "central_site_index": -1,
            "central_element": "",
            "ce_symbol": "",
            "ce_fraction": np.nan,
            "csm": np.nan,
            "chemenv_status": "STRUCTURE_LEVEL_FAILURE",
            "error": f"{type(exc).__name__}: {exc}",
        })

    return pd.DataFrame(rows)


def framework_fingerprint(structure, mof_id: str, charge_lookup: dict, robust_df: pd.DataFrame, chemenv_df: pd.DataFrame):
    symbols = [safe_symbol(s) for s in structure]
    n = len(symbols)
    volume_a3 = float(structure.volume)
    volume_nm3 = volume_a3 / 1000.0
    metal_indices = [i for i, s in enumerate(symbols) if is_metal_symbol(s)]
    nonmetal_indices = [i for i in range(n) if i not in metal_indices]

    charges = np.array([charge_lookup.get(i, np.nan) for i in range(n)], dtype=float)

    def idx_stats(indices):
        vals = charges[indices] if len(indices) else np.array([], dtype=float)
        vals = vals[np.isfinite(vals)]
        if len(vals) == 0:
            return np.nan, np.nan, np.nan
        return float(np.mean(vals)), float(np.median(vals)), float(np.std(vals, ddof=0))

    metal_mean, metal_med, metal_sd = idx_stats(metal_indices)
    hetero_indices = [i for i, s in enumerate(symbols) if s in HETERO]
    het_mean, het_med, het_sd = idx_stats(hetero_indices)

    c = Counter(symbols)
    robust_counts = Counter(robust_df["coordination_robustness_status"]) if not robust_df.empty else Counter()
    ce_symbols = Counter(
        chemenv_df.loc[chemenv_df["chemenv_status"].eq("OK"), "ce_symbol"].astype(str)
    ) if not chemenv_df.empty else Counter()

    return {
        "mof_id": mof_id,
        "n_sites": n,
        "cell_volume_A3": volume_a3,
        "n_metal_sites": len(metal_indices),
        "metal_elements": element_counter_string([symbols[i] for i in metal_indices]),
        "n_N": c["N"],
        "n_O": c["O"],
        "n_S": c["S"],
        "n_P": c["P"],
        "n_F": c["F"],
        "n_Cl": c["Cl"],
        "n_Br": c["Br"],
        "n_I": c["I"],
        "n_selected_heteroatoms": len(hetero_indices),
        "selected_heteroatom_fraction": len(hetero_indices) / n if n else np.nan,
        "selected_heteroatom_number_density_nm3": len(hetero_indices) / volume_nm3 if volume_nm3 > 0 else np.nan,
        "metal_charge_mean": metal_mean,
        "metal_charge_median": metal_med,
        "metal_charge_sd": metal_sd,
        "heteroatom_charge_mean": het_mean,
        "heteroatom_charge_median": het_med,
        "heteroatom_charge_sd": het_sd,
        "n_robust_exact_metal_sites": robust_counts["ROBUST_EXACT_SHELL"],
        "n_robust_element_shell_sites": robust_counts["ROBUST_ELEMENT_SHELL"],
        "n_method_sensitive_metal_sites": robust_counts["METHOD_SENSITIVE"],
        "metal_shell_robust_fraction": (
            (robust_counts["ROBUST_EXACT_SHELL"] + robust_counts["ROBUST_ELEMENT_SHELL"]) / len(robust_df)
            if len(robust_df) else np.nan
        ),
        "chemenv_environment_counts": ";".join(f"{k}:{v}" for k, v in sorted(ce_symbols.items())),
        "chemenv_ok_sites": int((chemenv_df["chemenv_status"] == "OK").sum()) if not chemenv_df.empty else 0,
        "chemenv_failed": bool((chemenv_df["chemenv_status"] == "STRUCTURE_LEVEL_FAILURE").any()) if not chemenv_df.empty else False,
    }


def pair_cards(pair_map: pd.DataFrame, fw: pd.DataFrame):
    numeric_cols = [
        "n_selected_heteroatoms",
        "selected_heteroatom_fraction",
        "selected_heteroatom_number_density_nm3",
        "metal_charge_mean",
        "metal_charge_median",
        "heteroatom_charge_mean",
        "heteroatom_charge_median",
        "metal_shell_robust_fraction",
    ]
    by = fw.set_index("mof_id")
    rows = []
    for _, r in pair_map.iterrows():
        a = norm_id(r["mof_a"])
        b = norm_id(r["mof_b"])
        if a not in by.index or b not in by.index:
            continue

        A = by.loc[a]
        B = by.loc[b]
        row = {
            "pair_id": r["pair_id"],
            "case_role": r.get("case_role", ""),
            "intervention": r.get("intervention", ""),
            "mof_a": a,
            "mof_b": b,
            "metal_elements_a": A["metal_elements"],
            "metal_elements_b": B["metal_elements"],
            "chemenv_a": A["chemenv_environment_counts"],
            "chemenv_b": B["chemenv_environment_counts"],
            "method_sensitive_sites_a": A["n_method_sensitive_metal_sites"],
            "method_sensitive_sites_b": B["n_method_sensitive_metal_sites"],
        }
        for c in numeric_cols:
            try:
                row[f"{c}_a"] = float(A[c])
                row[f"{c}_b"] = float(B[c])
                row[f"delta_{c}_b_minus_a"] = float(B[c]) - float(A[c])
            except Exception:
                row[f"{c}_a"] = np.nan
                row[f"{c}_b"] = np.nan
                row[f"delta_{c}_b_minus_a"] = np.nan

        intervention = str(row["intervention"]).lower()
        role = str(row["case_role"]).lower()
        any_sensitive = (A["n_method_sensitive_metal_sites"] > 0) or (B["n_method_sensitive_metal_sites"] > 0)

        if any_sensitive:
            status = "METHOD_SENSITIVE_CONTEXT"
        elif "metal" in intervention or "metal" in role:
            status = "STRUCTURALLY_SUPPORTED_METAL_CONTEXT"
        elif "functional" in intervention or "functional" in role:
            status = "DESCRIPTIVE_EXPLORATORY_CONTEXT"
        else:
            status = "DESCRIPTIVE_LINKER_CONTEXT"

        row["figure5_annotation_status"] = status
        rows.append(row)

    return pd.DataFrame(rows)


def main():
    print(TITLE)
    print("=" * 72)

    root = find_project_root(Path.cwd())
    frozen = root / "Step 3 results" / "Paper7B_Hosein_to_Shayan_Frozen_Source_Package"
    out = root / "Step 4 results" / "02_cif_chemistry" / "phase2b_selected_case_local_chemistry"
    out.mkdir(parents=True, exist_ok=True)

    # Dependencies
    try:
        import pymatgen  # noqa
        from pymatgen.core import Structure  # noqa
    except Exception as exc:
        raise RuntimeError(f"pymatgen unavailable: {exc}")

    case_set_path = frozen / "08_structures" / "02_final_case_set.csv"
    case_fw_path = frozen / "08_structures" / "02_final_case_frameworks.csv"
    charge_path = frozen / "06_cif_chemistry" / "03_atom_charge_rows.csv"

    for p in [case_set_path, case_fw_path, charge_path]:
        if not p.exists():
            raise RuntimeError(f"Missing frozen source: {p}")

    case_set = pd.read_csv(case_set_path, low_memory=False)
    case_fw = pd.read_csv(case_fw_path, low_memory=False)
    charges_raw = pd.read_csv(charge_path, low_memory=False)

    pair_map = build_case_mapping(case_set, case_fw)
    expected_ids = set(pair_map["mof_a"]).union(pair_map["mof_b"])
    cifs = find_selected_cifs(frozen, expected_ids)

    charges, charge_meta = prepare_charge_table(charges_raw)

    fatal = []
    warnings = []
    if len(pair_map) != 6:
        warnings.append(f"Recovered {len(pair_map)} pair mappings; expected 6.")
    if len(expected_ids) != 12:
        warnings.append(f"Recovered {len(expected_ids)} unique selected framework IDs; expected 12.")
    if len(cifs) != len(expected_ids):
        fatal.append(f"Found {len(cifs)} CIFs for {len(expected_ids)} expected frameworks.")

    all_site = []
    all_neighbor = []
    all_robust = []
    all_ce = []
    fw_rows = []
    audit_rows = []

    if not fatal:
        from pymatgen.core import Structure

        for mid in sorted(expected_ids):
            p = cifs[mid]
            try:
                structure = Structure.from_file(str(p))
                symbols = [safe_symbol(s) for s in structure]
                metal_indices = [i for i, s in enumerate(symbols) if is_metal_symbol(s)]

                charge_lookup, align = charge_lookup_for_mof(
                    charges, mid, len(structure), symbols
                )
                if not align["row_alignment"]:
                    fatal.append(
                        f"{mid}: charge rows {align['charge_rows']} != CIF sites {align['site_count']}."
                    )
                    continue
                if (
                    np.isfinite(align["element_alignment_fraction"])
                    and align["element_alignment_fraction"] < 0.99
                ):
                    warnings.append(
                        f"{mid}: element-label alignment fraction is "
                        f"{align['element_alignment_fraction']:.3f}."
                    )

                site_df, nb_df, robust_df = run_crystalnn(
                    structure, mid, charge_lookup, metal_indices
                )
                ce_df = run_chemenv(structure, mid, metal_indices)

                all_site.append(site_df)
                all_neighbor.append(nb_df)
                all_robust.append(robust_df)
                all_ce.append(ce_df)

                fw_rows.append(
                    framework_fingerprint(
                        structure, mid, charge_lookup, robust_df, ce_df
                    )
                )

                audit_rows.append({
                    "mof_id": mid,
                    "cif_path": str(p.relative_to(root)),
                    "n_sites": len(structure),
                    "n_metal_sites": len(metal_indices),
                    "charge_rows": align["charge_rows"],
                    "charge_row_alignment": align["row_alignment"],
                    "element_alignment_fraction": align["element_alignment_fraction"],
                    "crystalnn_default_failures": int(
                        ((site_df["method"] == "default") & site_df["error"].astype(str).str.len().gt(0)).sum()
                    ) if not site_df.empty else 0,
                    "crystalnn_neutral_failures": int(
                        ((site_df["method"] == "neutral_no_porous") & site_df["error"].astype(str).str.len().gt(0)).sum()
                    ) if not site_df.empty else 0,
                    "method_sensitive_metal_sites": int(
                        (robust_df["coordination_robustness_status"] == "METHOD_SENSITIVE").sum()
                    ) if not robust_df.empty else 0,
                    "chemenv_ok_sites": int((ce_df["chemenv_status"] == "OK").sum()) if not ce_df.empty else 0,
                    "chemenv_structure_failure": bool(
                        (ce_df["chemenv_status"] == "STRUCTURE_LEVEL_FAILURE").any()
                    ) if not ce_df.empty else False,
                    "chemenv_error": "; ".join(
                        ce_df.loc[ce_df["error"].astype(str).str.len().gt(0), "error"].astype(str).unique()
                    ) if not ce_df.empty else "",
                })

            except Exception as exc:
                fatal.append(f"{mid}: {type(exc).__name__}: {exc}")
                audit_rows.append({
                    "mof_id": mid,
                    "cif_path": str(p.relative_to(root)),
                    "fatal_error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(limit=3),
                })

    site_all = pd.concat(all_site, ignore_index=True) if all_site else pd.DataFrame()
    nb_all = pd.concat(all_neighbor, ignore_index=True) if all_neighbor else pd.DataFrame()
    robust_all = pd.concat(all_robust, ignore_index=True) if all_robust else pd.DataFrame()
    ce_all = pd.concat(all_ce, ignore_index=True) if all_ce else pd.DataFrame()
    fw_df = pd.DataFrame(fw_rows)
    audit_df = pd.DataFrame(audit_rows)
    pair_df = pair_cards(pair_map, fw_df) if not fw_df.empty else pd.DataFrame()

    # Evidence decision map.
    decision_rows = []
    for _, r in pair_df.iterrows():
        status = r["figure5_annotation_status"]
        if status == "STRUCTURALLY_SUPPORTED_METAL_CONTEXT":
            allowed = (
                "Use local coordination geometry, first-shell composition, distances, "
                "and aligned REPEAT charge fingerprints as structural context."
            )
            prohibited = (
                "Do not claim adsorption site, oxidation state, charge transfer, "
                "or a universal metal substitution rule."
            )
        elif status == "DESCRIPTIVE_LINKER_CONTEXT":
            allowed = (
                "Use framework heteroatom composition/density and charge fingerprints "
                "as descriptive context; metal-shell robustness may demonstrate preserved node context."
            )
            prohibited = (
                "Do not call these the changed linker atoms unless an explicit linker-site mapping exists; "
                "do not infer adsorption mechanism."
            )
        elif status == "DESCRIPTIVE_EXPLORATORY_CONTEXT":
            allowed = "Use only as an exploratory case-level structural fingerprint."
            prohibited = "No class-level functional-motif claim."
        else:
            allowed = "Show the case only with an explicit method-sensitivity label if retained."
            prohibited = "Do not present the coordination description as method-robust."

        decision_rows.append({
            "pair_id": r["pair_id"],
            "case_role": r["case_role"],
            "intervention": r["intervention"],
            "status": status,
            "allowed_use": allowed,
            "prohibited_use": prohibited,
        })
    decision_df = pd.DataFrame(decision_rows)

    # Save all data.
    pair_map.to_csv(out / "phase2b_frozen_pair_mapping.csv", index=False)
    audit_df.to_csv(out / "phase2b_framework_audit.csv", index=False)
    site_all.to_csv(out / "phase2b_crystalnn_metal_site_summary.csv", index=False)
    nb_all.to_csv(out / "phase2b_crystalnn_first_shell_neighbors.csv", index=False)
    robust_all.to_csv(out / "phase2b_crystalnn_setting_robustness.csv", index=False)
    ce_all.to_csv(out / "phase2b_chemenv_geometry_crosscheck.csv", index=False)
    fw_df.to_csv(out / "phase2b_framework_chemistry_fingerprints.csv", index=False)
    pair_df.to_csv(out / "phase2b_pair_chemistry_cards.csv", index=False)
    decision_df.to_csv(out / "phase2b_figure5_evidence_decisions.csv", index=False)

    metadata = {
        "phase": "2B",
        "scope": "six frozen selected structure cases only",
        "crystalnn_setting_A": "CrystalNN()",
        "crystalnn_setting_B": "CrystalNN(x_diff_weight=0, porous_adjustment=False)",
        "chemenv": {
            "strategy": "SimplestChemenvStrategy",
            "distance_cutoff": 1.4,
            "angle_cutoff": 0.3,
            "additional_condition": 0,
            "structure_refinement": "none",
            "valences": "undefined",
            "scope": "metal sites only",
            "interpretation": "geometry-only independent cross-check",
        },
        "heteroatom_set_for_selected_case_descriptor": sorted(HETERO),
        "charge_source": "frozen aligned REPEAT atom-level rows",
        "orientation_warning": "pair deltas are B-minus-A bookkeeping only and are NOT chemical substitution directions",
        "forbidden_claims": [
            "adsorption site",
            "oxidation state",
            "charge transfer",
            "causal mechanism",
            "directional substitution rule",
            "atom-specific pore accessibility",
        ],
        "charge_column_resolution": charge_meta,
    }
    (out / "phase2b_method_manifest.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    if not ce_all.empty:
        ce_fail_structures = int(
            ce_all.loc[ce_all["chemenv_status"] == "STRUCTURE_LEVEL_FAILURE", "mof_id"].nunique()
        )
        if ce_fail_structures:
            warnings.append(
                f"ChemEnv failed at structure level for {ce_fail_structures} selected framework(s); "
                "these remain explicit method-sensitivity cases."
            )

    crystal_fail_sites = 0
    if not site_all.empty:
        crystal_fail_sites = int(site_all["error"].astype(str).str.len().gt(0).sum())
        if crystal_fail_sites:
            warnings.append(
                f"CrystalNN reported {crystal_fail_sites} metal-site evaluation failure(s)."
            )

    decision = "PASS" if not fatal else "FAIL"
    summary = {
        "decision": decision,
        "frozen_pairs": int(len(pair_map)),
        "selected_frameworks": int(len(expected_ids)),
        "cifs_processed": int(audit_df.get("mof_id", pd.Series(dtype=str)).nunique()),
        "metal_sites_crystalnn_rows": int(len(site_all)),
        "first_shell_neighbor_rows": int(len(nb_all)),
        "setting_robustness_site_rows": int(len(robust_all)),
        "chemenv_rows": int(len(ce_all)),
        "pair_chemistry_cards": int(len(pair_df)),
        "fatal_issues": fatal,
        "warnings": warnings,
    }
    (out / "phase2b_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(f"Decision: {decision}")
    print(f"Frozen selected pairs: {len(pair_map)}")
    print(f"Selected frameworks: {len(expected_ids)}")
    print(f"Selected CIFs resolved: {len(cifs)}")
    print(f"Framework chemistry fingerprints: {len(fw_df)}")
    print(f"CrystalNN metal-site method rows: {len(site_all)}")
    print(f"CrystalNN first-shell neighbor rows: {len(nb_all)}")
    print(f"CrystalNN setting-comparison sites: {len(robust_all)}")
    print(f"ChemEnv cross-check rows: {len(ce_all)}")
    print(f"Pair chemistry cards: {len(pair_df)}")

    if not robust_all.empty:
        counts = robust_all["coordination_robustness_status"].value_counts()
        print("\nCrystalNN selected-site robustness:")
        for k, v in counts.items():
            print(f"  {k}: {v}")

    if not decision_df.empty:
        print("\nFigure 5 chemistry annotation decisions:")
        for _, r in decision_df.iterrows():
            print(f"  {r['pair_id']} | {r['case_role']} | {r['status']}")

    for w in warnings:
        print(f"WARN: {w}")
    for f in fatal:
        print(f"FATAL: {f}")

    print(
        "No adsorption effect, matching, bootstrap, pair selection, or process "
        "metric was recomputed."
    )
    print(f"Outputs: {out}")

    if decision != "PASS":
        sys.exit(2)


if __name__ == "__main__":
    main()
