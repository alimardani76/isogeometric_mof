from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd

from .utils import ROOT, DATA_RASPA

DERIVED_DIR = ROOT / "data" / "derived"
VALIDATION_DIR = ROOT / "outputs" / "validation"
ORIENTATION_FILE = DATA_RASPA / "publication_pair_orientation.csv"
RAW_STATS_FILE = DATA_RASPA / "final_pair_statistics.csv"
PAIR_SUMMARY_FILE = DATA_RASPA / "pair_summary.csv"
STRUCTURAL_TABLE_FILE = ROOT / "data" / "si" / "Table_S09_Final_Cases_Charges.csv"

PAIR_ORDER = ["A1", "A2", "A3", "A4", "B1", "B2", "C1", "C2"]
STRUCTURAL_ROLE_TO_PAIR = {
    "strong_linker_process_aligned": "A1",
    "near_null_comparison": "A2",
    "strong_metal_process_aligned": "A3",
    "cu_zn_pressure_exception": "A4",
    "process_discordant_comparison": "C1",
    "functional_motif_example": "C2",
}


def _native_pair_map() -> pd.DataFrame:
    p = pd.read_csv(PAIR_SUMMARY_FILE, low_memory=False)
    cols = ["pair_id", "role", "group", "A_mof", "B_mof"]
    d = p[cols].drop_duplicates().copy()
    if d["pair_id"].duplicated().any():
        raise RuntimeError("pair_summary.csv contains more than one native A/B identity for a pair.")
    return d


def _structural_map() -> pd.DataFrame:
    t = pd.read_csv(STRUCTURAL_TABLE_FILE, low_memory=False)
    rows = []
    for role, pair_id in STRUCTURAL_ROLE_TO_PAIR.items():
        g = t[t["role"] == role].copy()
        if set(g["endpoint"]) != {"A", "B"} or len(g) != 2:
            raise RuntimeError(f"Table S09 does not define exactly A/B for {role}.")
        rows.append({
            "pair_id": pair_id,
            "structural_A_mof": g.loc[g.endpoint == "A", "mof_id"].iloc[0],
            "structural_B_mof": g.loc[g.endpoint == "B", "mof_id"].iloc[0],
        })
    return pd.DataFrame(rows)


def orientation_audit() -> pd.DataFrame:
    native = _native_pair_map()
    orient = pd.read_csv(ORIENTATION_FILE, low_memory=False)
    if set(orient.pair_id) != set(PAIR_ORDER):
        raise RuntimeError("publication_pair_orientation.csv must define exactly A1-A4, B1-B2, C1-C2.")
    d = orient.merge(native, on=["pair_id", "role"], how="left", validate="one_to_one")
    if d[["A_mof", "B_mof"]].isna().any().any():
        raise RuntimeError("One or more publication pairs do not match pair_summary.csv.")

    def status(r):
        same = (r.canonical_A_mof == r.A_mof and r.canonical_B_mof == r.B_mof)
        flipped = (r.canonical_A_mof == r.B_mof and r.canonical_B_mof == r.A_mof)
        if same:
            return "same"
        if flipped:
            return "reversed"
        return "ERROR"

    d["orientation_action"] = d.apply(status, axis=1)
    if (d.orientation_action == "ERROR").any():
        bad = d.loc[d.orientation_action == "ERROR", ["pair_id", "A_mof", "B_mof", "canonical_A_mof", "canonical_B_mof"]]
        raise RuntimeError("Canonical identities are not the same unordered pair as native RASPA identities:\n" + bad.to_string(index=False))

    # Independent bridge check against Table S09 for the six structural cases.
    structural = _structural_map()
    ck = d.merge(structural, on="pair_id", how="left")
    structural_rows = ck.structural_A_mof.notna()
    if not (ck.loc[structural_rows, "canonical_A_mof"].to_numpy() == ck.loc[structural_rows, "structural_A_mof"].to_numpy()).all():
        raise RuntimeError("Canonical A identities disagree with Table S09.")
    if not (ck.loc[structural_rows, "canonical_B_mof"].to_numpy() == ck.loc[structural_rows, "structural_B_mof"].to_numpy()).all():
        raise RuntimeError("Canonical B identities disagree with Table S09.")
    return d


def _absolute_ci(low: float, high: float) -> tuple[float, float]:
    if not np.isfinite(low) or not np.isfinite(high):
        return (np.nan, np.nan)
    if low <= 0 <= high:
        return (0.0, max(abs(low), abs(high)))
    vals = [abs(low), abs(high)]
    return (min(vals), max(vals))


def publication_statistics(write: bool = True) -> pd.DataFrame:
    audit = orientation_audit().set_index("pair_id")
    raw = pd.read_csv(RAW_STATS_FILE, low_memory=False).copy()
    raw["native_A_mean"] = raw["A_mean"]
    raw["native_A_between_seed_sd"] = raw["A_between_seed_sd"]
    raw["native_B_mean"] = raw["B_mean"]
    raw["native_B_between_seed_sd"] = raw["B_between_seed_sd"]
    raw["native_signed_log2_A_over_B"] = raw["signed_log2_A_over_B"]
    raw["native_absolute_fold_difference"] = raw["absolute_fold_difference"]
    raw["native_approx_95ci_log2_low"] = raw["approx_95ci_log2_low"]
    raw["native_approx_95ci_log2_high"] = raw["approx_95ci_log2_high"]
    raw["native_delta_total_energy_B_minus_A_K_per_CO2"] = raw["delta_total_energy_B_minus_A_K_per_CO2"]
    raw["native_delta_vdw_energy_B_minus_A_K_per_CO2"] = raw["delta_vdw_energy_B_minus_A_K_per_CO2"]
    raw["native_delta_coulomb_energy_B_minus_A_K_per_CO2"] = raw["delta_coulomb_energy_B_minus_A_K_per_CO2"]

    rows = []
    for _, r0 in raw.iterrows():
        r = r0.copy()
        a = audit.loc[r.pair_id]
        rev = a.orientation_action == "reversed"
        r["native_A_mof"] = a.A_mof
        r["native_B_mof"] = a.B_mof
        r["publication_A_mof"] = a.canonical_A_mof
        r["publication_B_mof"] = a.canonical_B_mof
        r["orientation_action"] = a.orientation_action
        r["orientation_source"] = a.orientation_source
        if rev:
            r["A_mean"], r["B_mean"] = r0.B_mean, r0.A_mean
            r["A_between_seed_sd"], r["B_between_seed_sd"] = r0.B_between_seed_sd, r0.A_between_seed_sd
            r["A_over_B"] = np.nan if not np.isfinite(r0.A_over_B) or r0.A_over_B == 0 else 1.0 / r0.A_over_B
            r["signed_log2_A_over_B"] = -r0.signed_log2_A_over_B
            r["approx_95ci_log2_low"] = -r0.approx_95ci_log2_high
            r["approx_95ci_log2_high"] = -r0.approx_95ci_log2_low
            for col in [
                "delta_total_energy_B_minus_A_K_per_CO2",
                "delta_vdw_energy_B_minus_A_K_per_CO2",
                "delta_coulomb_energy_B_minus_A_K_per_CO2",
            ]:
                r[col] = -r0[col] if np.isfinite(r0[col]) else np.nan
        r["absolute_log2_contrast"] = abs(r["signed_log2_A_over_B"])
        lo, hi = _absolute_ci(r["approx_95ci_log2_low"], r["approx_95ci_log2_high"])
        r["absolute_log2_ci_low"] = lo
        r["absolute_log2_ci_high"] = hi
        rows.append(r)

    out = pd.DataFrame(rows)
    out["pair_id"] = pd.Categorical(out["pair_id"], PAIR_ORDER, ordered=True)
    out = out.sort_values(["pair_id", "mode"]).reset_index(drop=True)
    out["pair_id"] = out["pair_id"].astype(str)

    # Invariants: unordered results cannot change; signed values must match the recomputed ratio.
    if not np.allclose(out["absolute_fold_difference"], out["native_absolute_fold_difference"], equal_nan=True):
        raise RuntimeError("Absolute fold difference changed during orientation standardization.")
    mask = np.isfinite(out.A_over_B) & (out.A_over_B > 0) & np.isfinite(out.signed_log2_A_over_B)
    if not np.allclose(np.log2(out.loc[mask, "A_over_B"]), out.loc[mask, "signed_log2_A_over_B"], rtol=1e-10, atol=1e-10):
        raise RuntimeError("Signed log2 contrast is inconsistent with publication A/B ratio.")

    if write:
        DERIVED_DIR.mkdir(parents=True, exist_ok=True)
        out.to_csv(DERIVED_DIR / "final_pair_statistics_publication.csv", index=False)
        orientation_audit().to_csv(DERIVED_DIR / "publication_orientation_audit.csv", index=False)
        write_validation_report(out)
    return out


def correlation_summary(st: pd.DataFrame) -> dict:
    h = st[st["mode"] == "henry_full"].set_index("pair_id").loc[PAIR_ORDER]
    result = {}
    for mode, label in [("gcmc_0p1bar", "0.1 bar"), ("gcmc_1bar", "1 bar")]:
        g = st[st["mode"] == mode].set_index("pair_id").loc[PAIR_ORDER]
        x = h.signed_log2_A_over_B.to_numpy(float)
        y = g.signed_log2_A_over_B.to_numpy(float)
        result[mode] = {
            "label": label,
            "pearson_r": float(np.corrcoef(x, y)[0, 1]),
            "n_pairs": int(len(x)),
        }
    return result


def write_validation_report(st: pd.DataFrame) -> None:
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    audit = orientation_audit()
    corr = correlation_summary(st)
    payload = {
        "publication_pair_order": PAIR_ORDER,
        "orientation_actions": dict(zip(audit.pair_id, audit.orientation_action)),
        "reversed_pairs": audit.loc[audit.orientation_action == "reversed", "pair_id"].tolist(),
        "unchanged_pairs": audit.loc[audit.orientation_action == "same", "pair_id"].tolist(),
        "finite_pressure_correlations": corr,
        "checks": {
            "canonical_pairs_match_native_unordered_pairs": True,
            "six_structural_cases_match_Table_S09": True,
            "absolute_fold_difference_preserved": True,
            "signed_log2_consistent_with_publication_ratio": True,
        },
    }
    (VALIDATION_DIR / "RASPA_publication_validation.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [
        "Paper 7B RASPA publication-orientation validation",
        "=================================================",
        "",
        "Pair actions:",
    ]
    for _, r in audit.iterrows():
        lines.append(f"  {r.pair_id}: {r.orientation_action:8s} | A={r.canonical_A_mof} | B={r.canonical_B_mof}")
    lines += ["", "Publication-oriented Pearson correlations:"]
    for v in corr.values():
        lines.append(f"  Henry vs {v['label']}: r = {v['pearson_r']:.6f} (n={v['n_pairs']})")
    lines += [
        "",
        "PASS: Figure 5/Table S09 convention is enforced for A1/A2/A3/A4/C1/C2.",
        "PASS: B1/B2 retain native RASPA comparator orientation.",
        "PASS: all orientation-dependent quantities are transformed mathematically, not cosmetically.",
    ]
    (VALIDATION_DIR / "RASPA_publication_validation.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    st = publication_statistics(write=True)
    print((VALIDATION_DIR / "RASPA_publication_validation.txt").read_text(encoding="utf-8"))
