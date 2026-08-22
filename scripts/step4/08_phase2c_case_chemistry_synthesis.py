#!/usr/bin/env python3
"""
Project 7B Step 4 - Phase 2C
Selected-case chemistry evidence synthesis and Figure-5 readiness audit.

This phase does NOT create a population-wide chemistry mechanism. It integrates only
already-frozen case roles/outcomes with the newly validated selected-case structural
chemistry objects:

- two-setting CrystalNN local coordination
- ChemEnv geometry cross-check
- exact raw-CIF -> pymatgen REPEAT charge bridge
- validated first-shell partial-charge fingerprints
- frozen element/framework REPEAT summaries
- simple CIF composition/heteroatom descriptors

Outputs are case-level evidence cards and a decision about what, if anything, is worth
adding to the paper.

READ ONLY with respect to Steps 1-3.
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

TITLE = "PROJECT 7B STEP 4 - PHASE 2C CASE-CHEMISTRY EVIDENCE SYNTHESIS"


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
    for actual in df.columns:
        al = str(actual).lower()
        for c in candidates:
            cc = c.lower()
            if len(cc) >= 4 and cc in al:
                return actual
    if required:
        raise RuntimeError(f"Could not resolve {candidates}; columns={list(df.columns)}")
    return None


def safe_read(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path, low_memory=False)


def as_num(x):
    try:
        return float(x)
    except Exception:
        return np.nan


def finite_median(s):
    x = pd.to_numeric(s, errors="coerce").dropna()
    return float(x.median()) if len(x) else np.nan


def finite_mean(s):
    x = pd.to_numeric(s, errors="coerce").dropna()
    return float(x.mean()) if len(x) else np.nan


def finite_std(s):
    x = pd.to_numeric(s, errors="coerce").dropna()
    return float(x.std(ddof=0)) if len(x) else np.nan


def wasserstein_safe(a, b):
    from scipy.stats import wasserstein_distance
    aa = pd.to_numeric(pd.Series(a), errors="coerce").dropna().to_numpy(float)
    bb = pd.to_numeric(pd.Series(b), errors="coerce").dropna().to_numpy(float)
    if len(aa) == 0 or len(bb) == 0:
        return np.nan
    return float(wasserstein_distance(aa, bb))


def counter_string(vals):
    c = Counter(str(v) for v in vals if pd.notna(v) and str(v) != "")
    return ";".join(f"{k}:{c[k]}" for k in sorted(c))


def build_pair_map(case_set: pd.DataFrame, case_fw: pd.DataFrame) -> pd.DataFrame:
    pair_set = resolve_col(case_set, ["pair_id", "pair_key", "pair"], required=False)
    role = resolve_col(case_set, ["case_role", "selection_category", "role"], required=False)
    intervention = resolve_col(case_set, ["intervention", "intervention_class"], required=False)
    a = resolve_col(case_set, ["mof_a", "id_a", "framework_a"], required=False)
    b = resolve_col(case_set, ["mof_b", "id_b", "framework_b"], required=False)

    rows = []
    if pair_set and a and b:
        for _, r in case_set.iterrows():
            rows.append({
                "pair_id": str(r[pair_set]),
                "mof_a": norm_id(r[a]),
                "mof_b": norm_id(r[b]),
                "case_role": str(r[role]) if role else "",
                "intervention": str(r[intervention]) if intervention else "",
            })
        return pd.DataFrame(rows)

    pair_fw = resolve_col(case_fw, ["pair_id", "pair_key", "pair"], required=True)
    mof = resolve_col(case_fw, ["mof_id", "framework_id", "framework", "mof"], required=True)
    for pid, g in case_fw.groupby(pair_fw):
        ids = list(dict.fromkeys(norm_id(v) for v in g[mof].dropna().astype(str)))
        if len(ids) == 2:
            rows.append({
                "pair_id": str(pid),
                "mof_a": ids[0],
                "mof_b": ids[1],
                "case_role": "",
                "intervention": "",
            })
    return pd.DataFrame(rows)


def build_framework_summary(
    mapped: pd.DataFrame,
    neighbor: pd.DataFrame,
    site: pd.DataFrame,
    robustness: pd.DataFrame,
    chemenv: pd.DataFrame,
    old_framework_fingerprint: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    for mid in sorted(mapped["mof_id"].astype(str).unique()):
        m = mapped[mapped["mof_id"].astype(str).eq(mid)].copy()
        n = neighbor[neighbor["mof_id"].astype(str).eq(mid)].copy()
        s = site[site["mof_id"].astype(str).eq(mid)].copy()
        r = robustness[robustness["mof_id"].astype(str).eq(mid)].copy()
        c = chemenv[chemenv["mof_id"].astype(str).eq(mid)].copy()

        # Use only default CrystalNN for descriptive central/shell values, while
        # robustness across both methods is reported separately.
        sd = s[s["method"].astype(str).eq("default")].copy()
        nd = n[n["method"].astype(str).eq("default")].copy()

        if not old_framework_fingerprint.empty:
            ff = old_framework_fingerprint[
                old_framework_fingerprint["mof_id"].astype(str).eq(mid)
            ]
            ff = ff.iloc[0] if len(ff) else pd.Series(dtype=object)
        else:
            ff = pd.Series(dtype=object)

        metal_elements = counter_string(sd["central_element"]) if not sd.empty else ""
        default_shell_types = counter_string(sd["neighbor_elements"]) if not sd.empty else ""

        robust_exact = int((r["coordination_robustness_status"] == "ROBUST_EXACT_SHELL").sum()) if not r.empty else 0
        robust_element = int((r["coordination_robustness_status"] == "ROBUST_ELEMENT_SHELL").sum()) if not r.empty else 0
        sensitive = int((r["coordination_robustness_status"] == "METHOD_SENSITIVE").sum()) if not r.empty else 0
        total_sites = len(r)

        ce_ok = c[c["chemenv_status"].astype(str).eq("OK")].copy() if not c.empty else pd.DataFrame()

        all_charge = m["repeat_charge"]
        hetero_charge = m.loc[m["element"].isin(["N", "O", "S", "P", "F", "Cl", "Br", "I"]), "repeat_charge"]
        metal_charge = sd["central_repeat_charge_mapped"] if "central_repeat_charge_mapped" in sd.columns else pd.Series(dtype=float)

        row = {
            "mof_id": mid,
            "n_atoms": len(m),
            "metal_elements": metal_elements,
            "n_metal_sites": len(sd),
            "default_cn_median": finite_median(sd["coordination_number"]) if not sd.empty else np.nan,
            "default_cn_min": pd.to_numeric(sd["coordination_number"], errors="coerce").min() if not sd.empty else np.nan,
            "default_cn_max": pd.to_numeric(sd["coordination_number"], errors="coerce").max() if not sd.empty else np.nan,
            "default_shell_signature_counts": default_shell_types,
            "default_neighbor_distance_mean_A": finite_mean(nd["distance_A"]) if not nd.empty else np.nan,
            "default_neighbor_distance_sd_A": finite_std(nd["distance_A"]) if not nd.empty else np.nan,
            "crystalnn_robust_exact_sites": robust_exact,
            "crystalnn_robust_element_sites": robust_element,
            "crystalnn_method_sensitive_sites": sensitive,
            "crystalnn_robust_fraction": (
                (robust_exact + robust_element) / total_sites if total_sites else np.nan
            ),
            "chemenv_ok_sites": len(ce_ok),
            "chemenv_environment_counts": counter_string(ce_ok["ce_symbol"]) if not ce_ok.empty else "",
            "chemenv_csm_median": finite_median(ce_ok["csm"]) if not ce_ok.empty else np.nan,
            "framework_repeat_charge_mean": finite_mean(all_charge),
            "framework_repeat_charge_sd": finite_std(all_charge),
            "metal_repeat_charge_median": finite_median(metal_charge),
            "metal_repeat_charge_sd": finite_std(metal_charge),
            "heteroatom_repeat_charge_mean": finite_mean(hetero_charge),
            "heteroatom_repeat_charge_sd": finite_std(hetero_charge),
            "first_shell_neighbor_charge_mean": finite_mean(nd["neighbor_repeat_charge_mapped"]) if not nd.empty else np.nan,
            "first_shell_neighbor_charge_sd": finite_std(nd["neighbor_repeat_charge_mapped"]) if not nd.empty else np.nan,
            "first_shell_O_rows": int((nd["neighbor_element"] == "O").sum()) if not nd.empty else 0,
            "first_shell_N_rows": int((nd["neighbor_element"] == "N").sum()) if not nd.empty else 0,
            "first_shell_S_rows": int((nd["neighbor_element"] == "S").sum()) if not nd.empty else 0,
            "first_shell_halogen_rows": int(nd["neighbor_element"].isin(["F","Cl","Br","I"]).sum()) if not nd.empty else 0,
            # These columns were computed in Phase 2B directly from CIF composition/volume,
            # not from the invalid site-order charge assumption, so they remain valid.
            "selected_heteroatom_fraction": as_num(ff.get("selected_heteroatom_fraction", np.nan)),
            "selected_heteroatom_number_density_nm3": as_num(ff.get("selected_heteroatom_number_density_nm3", np.nan)),
            "cell_volume_A3": as_num(ff.get("cell_volume_A3", np.nan)),
        }
        rows.append(row)

    return pd.DataFrame(rows)


def pair_synthesis(pair_map, fw, mapped, site, neighbor):
    by = fw.set_index("mof_id")
    rows = []

    for _, p in pair_map.iterrows():
        a, b = norm_id(p["mof_a"]), norm_id(p["mof_b"])
        if a not in by.index or b not in by.index:
            continue
        A, B = by.loc[a], by.loc[b]

        ma = mapped[mapped["mof_id"].astype(str).eq(a)]
        mb = mapped[mapped["mof_id"].astype(str).eq(b)]

        # Unordered distribution separations. These are descriptive distances, not directions.
        all_charge_wd = wasserstein_safe(ma["repeat_charge"], mb["repeat_charge"])
        ha = ma.loc[ma["element"].isin(["N","O","S","P","F","Cl","Br","I"]), "repeat_charge"]
        hb = mb.loc[mb["element"].isin(["N","O","S","P","F","Cl","Br","I"]), "repeat_charge"]
        hetero_charge_wd = wasserstein_safe(ha, hb)

        same_metal_identity = A["metal_elements"] == B["metal_elements"]

        shell_same = A["default_shell_signature_counts"] == B["default_shell_signature_counts"]
        chemenv_same = A["chemenv_environment_counts"] == B["chemenv_environment_counts"]

        row = {
            "pair_id": p["pair_id"],
            "case_role": p.get("case_role", ""),
            "intervention": p.get("intervention", ""),
            "mof_a": a,
            "mof_b": b,
            "metal_elements_a": A["metal_elements"],
            "metal_elements_b": B["metal_elements"],
            "same_metal_identity": same_metal_identity,
            "crystalnn_shell_inventory_same": shell_same,
            "chemenv_inventory_same": chemenv_same,
            "method_sensitive_sites_total": int(A["crystalnn_method_sensitive_sites"] + B["crystalnn_method_sensitive_sites"]),
            "all_atom_charge_wasserstein": all_charge_wd,
            "heteroatom_charge_wasserstein": hetero_charge_wd,
            "abs_delta_heteroatom_number_density_nm3": (
                abs(float(B["selected_heteroatom_number_density_nm3"]) - float(A["selected_heteroatom_number_density_nm3"]))
                if np.isfinite(A["selected_heteroatom_number_density_nm3"]) and np.isfinite(B["selected_heteroatom_number_density_nm3"])
                else np.nan
            ),
            "abs_delta_metal_repeat_charge_median": (
                abs(float(B["metal_repeat_charge_median"]) - float(A["metal_repeat_charge_median"]))
                if np.isfinite(A["metal_repeat_charge_median"]) and np.isfinite(B["metal_repeat_charge_median"])
                else np.nan
            ),
            "abs_delta_first_shell_neighbor_charge_mean": (
                abs(float(B["first_shell_neighbor_charge_mean"]) - float(A["first_shell_neighbor_charge_mean"]))
                if np.isfinite(A["first_shell_neighbor_charge_mean"]) and np.isfinite(B["first_shell_neighbor_charge_mean"])
                else np.nan
            ),
            "abs_delta_default_neighbor_distance_mean_A": (
                abs(float(B["default_neighbor_distance_mean_A"]) - float(A["default_neighbor_distance_mean_A"]))
                if np.isfinite(A["default_neighbor_distance_mean_A"]) and np.isfinite(B["default_neighbor_distance_mean_A"])
                else np.nan
            ),
            "crystalnn_robust_fraction_a": A["crystalnn_robust_fraction"],
            "crystalnn_robust_fraction_b": B["crystalnn_robust_fraction"],
            "chemenv_a": A["chemenv_environment_counts"],
            "chemenv_b": B["chemenv_environment_counts"],
            "shells_a": A["default_shell_signature_counts"],
            "shells_b": B["default_shell_signature_counts"],
        }

        role = str(row["case_role"]).lower()
        intervention = str(row["intervention"]).lower()
        sensitive = row["method_sensitive_sites_total"] > 0

        if sensitive:
            status = "BOUNDARY_METHOD_SENSITIVE"
            paper_use = "Retain only as a coordination-method boundary/counterexample; do not annotate a robust local coordination mechanism."
        elif "metal" in intervention or "metal" in role:
            status = "ROBUST_METAL_LOCAL_CHEMISTRY"
            paper_use = "Suitable for a compact local-coordination + validated REPEAT-charge inset, with descriptive wording only."
        elif "functional" in intervention or "functional" in role:
            status = "EXPLORATORY_STRUCTURE_ONLY"
            paper_use = "Suitable only as an exploratory structure card; no class-level mechanism."
        else:
            status = "LINKER_CASE_NODE_CONTEXT_ONLY"
            paper_use = "May show that the metal-node environment is preserved/different and report global electrostatic fingerprints; do not attribute charges to the changed linker without explicit linker atom mapping."

        row["phase2c_status"] = status
        row["recommended_paper_use"] = paper_use
        rows.append(row)

    return pd.DataFrame(rows)


def overlap_old_coordination_audit(root: Path, selected_ids: set[str], fw_new: pd.DataFrame):
    old_path = root / "analysis" / "metal_coordination_signatures.parquet"
    if not old_path.exists():
        return pd.DataFrame([{
            "status": "OLD_COORDINATION_FILE_MISSING"
        }])

    old = pd.read_parquet(old_path)
    id_col = resolve_col(old, ["mof_id", "framework_id", "framework", "mof", "name"], required=False)
    if id_col is None:
        return pd.DataFrame([{
            "status": "OLD_SCHEMA_ID_NOT_RESOLVED",
            "old_columns": json.dumps([str(c) for c in old.columns])
        }])

    old["_mof_norm"] = old[id_col].astype(str).map(norm_id)
    sub = old[old["_mof_norm"].isin(selected_ids)].copy()

    # Do not fake an exact signature comparison if schema names do not make it unambiguous.
    signature_cols = [
        c for c in old.columns
        if any(k in str(c).lower() for k in ["signature", "coordination", "default", "neutral", "porous", "x_diff"])
    ]

    rows = []
    new_by = fw_new.set_index("mof_id")
    for mid in sorted(set(sub["_mof_norm"])):
        o = sub[sub["_mof_norm"].eq(mid)]
        rec = {
            "mof_id": mid,
            "old_rows": len(o),
            "old_signature_like_columns": json.dumps(signature_cols),
            "new_crystalnn_robust_fraction": (
                float(new_by.loc[mid, "crystalnn_robust_fraction"])
                if mid in new_by.index else np.nan
            ),
            "new_method_sensitive_sites": (
                int(new_by.loc[mid, "crystalnn_method_sensitive_sites"])
                if mid in new_by.index else np.nan
            ),
            "status": "OVERLAP_PRESENT_SCHEMA_PROFILED_NOT_FORCED",
        }
        for c in signature_cols[:12]:
            rec[f"old_{c}"] = json.dumps([str(v) for v in o[c].dropna().astype(str).unique()[:10]])
        rows.append(rec)

    if not rows:
        rows.append({
            "status": "NO_SELECTED_FRAMEWORK_OVERLAP",
            "old_columns": json.dumps([str(c) for c in old.columns])
        })
    return pd.DataFrame(rows)


def main():
    print(TITLE)
    print("=" * 72)

    root = find_root(Path.cwd())
    frozen = root / "Step 3 results" / "Paper7B_Hosein_to_Shayan_Frozen_Source_Package"
    phase2b = root / "Step 4 results" / "02_cif_chemistry" / "phase2b_selected_case_local_chemistry"
    bridge = root / "Step 4 results" / "02_cif_chemistry" / "phase2b2_exact_charge_site_bridge"
    out = root / "Step 4 results" / "02_cif_chemistry" / "phase2c_case_chemistry_synthesis"
    out.mkdir(parents=True, exist_ok=True)

    required = {
        "case_set": frozen / "08_structures" / "02_final_case_set.csv",
        "case_fw": frozen / "08_structures" / "02_final_case_frameworks.csv",
        "robustness": phase2b / "phase2b_crystalnn_setting_robustness.csv",
        "chemenv": phase2b / "phase2b_chemenv_geometry_crosscheck.csv",
        "fw_fingerprint": phase2b / "phase2b_framework_chemistry_fingerprints.csv",
        "mapped": bridge / "phase2b2_raw_cif_to_pymatgen_charge_map.csv",
        "neighbor": bridge / "phase2b2_first_shell_neighbors_with_validated_repeat_charges.csv",
        "site": bridge / "phase2b2_metal_site_summary_with_validated_repeat_charges.csv",
    }
    missing = [f"{k}: {p}" for k, p in required.items() if not p.exists()]
    if missing:
        print("Decision: FAIL")
        for m in missing:
            print(f"FATAL: missing {m}")
        sys.exit(2)

    case_set = pd.read_csv(required["case_set"], low_memory=False)
    case_fw = pd.read_csv(required["case_fw"], low_memory=False)
    robustness = pd.read_csv(required["robustness"], low_memory=False)
    chemenv = pd.read_csv(required["chemenv"], low_memory=False)
    fw_old = pd.read_csv(required["fw_fingerprint"], low_memory=False)
    mapped = pd.read_csv(required["mapped"], low_memory=False)
    neighbor = pd.read_csv(required["neighbor"], low_memory=False)
    site = pd.read_csv(required["site"], low_memory=False)

    pair_map = build_pair_map(case_set, case_fw)
    expected_ids = set(pair_map["mof_a"]).union(pair_map["mof_b"])

    fw = build_framework_summary(mapped, neighbor, site, robustness, chemenv, fw_old)
    pairs = pair_synthesis(pair_map, fw, mapped, site, neighbor)
    overlap = overlap_old_coordination_audit(root, expected_ids, fw)

    fw.to_csv(out / "phase2c_framework_local_chemistry_summary.csv", index=False)
    pairs.to_csv(out / "phase2c_pair_case_chemistry_cards.csv", index=False)
    overlap.to_csv(out / "phase2c_old_new_coordination_overlap_audit.csv", index=False)

    # Keep a compact decision map for manuscript integration.
    decision_map = pairs[[
        "pair_id", "case_role", "intervention", "phase2c_status",
        "recommended_paper_use", "method_sensitive_sites_total",
        "same_metal_identity", "crystalnn_shell_inventory_same",
        "chemenv_inventory_same", "all_atom_charge_wasserstein",
        "heteroatom_charge_wasserstein",
        "abs_delta_heteroatom_number_density_nm3",
        "abs_delta_metal_repeat_charge_median",
        "abs_delta_first_shell_neighbor_charge_mean",
        "abs_delta_default_neighbor_distance_mean_A",
    ]].copy()
    decision_map.to_csv(out / "phase2c_figure5_integration_decision_map.csv", index=False)

    # Audit gates.
    fatal = []
    warnings = []

    if len(pair_map) != 6:
        fatal.append(f"Frozen pair map contains {len(pair_map)} pairs, expected 6.")
    if len(expected_ids) != 12:
        fatal.append(f"Frozen selected framework count is {len(expected_ids)}, expected 12.")
    if len(fw) != 12:
        fatal.append(f"Framework chemistry summary contains {len(fw)} rows, expected 12.")
    if len(pairs) != 6:
        fatal.append(f"Pair chemistry cards contain {len(pairs)} rows, expected 6.")

    if site["central_repeat_charge_mapped"].isna().any():
        fatal.append("Validated metal-site table contains missing central REPEAT charges.")
    valid_neighbor = neighbor["neighbor_site_index"] >= 0
    if neighbor.loc[valid_neighbor, "neighbor_repeat_charge_mapped"].isna().any():
        fatal.append("Validated first-shell table contains missing REPEAT charges.")

    n_sensitive_pairs = int((pairs["method_sensitive_sites_total"] > 0).sum()) if not pairs.empty else 0
    n_robust_metal = int((pairs["phase2c_status"] == "ROBUST_METAL_LOCAL_CHEMISTRY").sum()) if not pairs.empty else 0

    # Never infer a linker mechanism from descriptive distances.
    interpretation = pd.DataFrame([
        {
            "evidence_object": "robust two-setting CrystalNN + ChemEnv + mapped REPEAT charge",
            "allowed_claim": "case-level local coordination/electrostatic structural context",
            "prohibited_claim": "adsorption site, oxidation state, charge transfer, causal mechanism",
        },
        {
            "evidence_object": "whole-framework / heteroatom charge-distribution Wasserstein distance",
            "allowed_claim": "descriptive electrostatic fingerprint separation between the two frozen structures",
            "prohibited_claim": "directional linker polarity rule or site-specific binding mechanism",
        },
        {
            "evidence_object": "heteroatom number density from CIF composition and cell volume",
            "allowed_claim": "whole-cell composition density descriptor",
            "prohibited_claim": "pore-accessible heteroatom density",
        },
        {
            "evidence_object": "linker-case preserved metal coordination",
            "allowed_claim": "the selected case does not require an obvious metal-node coordination change to exhibit the reported adsorption contrast",
            "prohibited_claim": "therefore a specific linker atom or electrostatic mechanism caused the effect",
        },
    ])
    interpretation.to_csv(out / "phase2c_interpretation_boundaries.csv", index=False)

    decision = "PASS" if not fatal else "FAIL"
    summary = {
        "decision": decision,
        "frozen_pairs": len(pair_map),
        "selected_frameworks": len(expected_ids),
        "framework_summaries": len(fw),
        "pair_cards": len(pairs),
        "pairs_with_any_method_sensitive_metal_site": n_sensitive_pairs,
        "robust_metal_local_chemistry_cases": n_robust_metal,
        "fatal": fatal,
        "warnings": warnings,
        "next_decision": (
            "REVIEW_CASE_CARDS_BEFORE_ANY_FIGURE_OR_GLOBAL_CHEMISTRY_EXTENSION"
            if decision == "PASS" else "STOP"
        ),
    }
    (out / "phase2c_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Decision: {decision}")
    print(f"Frozen selected pairs integrated: {len(pair_map)}")
    print(f"Selected frameworks integrated: {len(expected_ids)}")
    print(f"Framework local-chemistry summaries: {len(fw)}")
    print(f"Pair chemistry cards: {len(pairs)}")
    print(f"Pairs with any CrystalNN method-sensitive metal site: {n_sensitive_pairs}")
    print(f"Robust metal local-chemistry cases: {n_robust_metal}")

    if not pairs.empty:
        print("\nCase-level chemistry synthesis:")
        for _, r in pairs.iterrows():
            print(
                f"  {r['case_role']} | {r['phase2c_status']} | "
                f"charge WD={r['all_atom_charge_wasserstein']:.4g} | "
                f"hetero WD={r['heteroatom_charge_wasserstein']:.4g} | "
                f"method-sensitive sites={int(r['method_sensitive_sites_total'])}"
            )

    print("\nNo population-wide mechanism or directional chemistry rule is inferred from these six cases.")
    for w in warnings:
        print(f"WARN: {w}")
    for f in fatal:
        print(f"FATAL: {f}")

    print(f"Outputs: {out}")
    if decision != "PASS":
        sys.exit(2)


if __name__ == "__main__":
    main()
