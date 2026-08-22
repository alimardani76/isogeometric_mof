#!/usr/bin/env python3
"""Project 7B Step 4 - Phase 1 existing-evidence exhaustion audit.

READ ONLY with respect to Steps 1-3.

Purpose
-------
Before adding any new chemistry/statistics/simulation, determine what the frozen
Project 7B run already proves, what coauthor-requested upgrades are already
satisfied, and which proposed additions would genuinely add scientific value.

This script does NOT recompute pair selection, matching, effect estimates,
bootstrap intervals, process metrics, or case selection.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = ROOT / "Step 4 results" / "01_existing_evidence"
RESULTS.mkdir(parents=True, exist_ok=True)
INVENTORY = ROOT / "Step 4 results" / "00_governance" / "phase0_frozen_input_inventory.csv"


def rel(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(p)


def load_table(path: Path) -> pd.DataFrame:
    suf = path.suffix.lower()
    if suf == ".csv":
        return pd.read_csv(path, low_memory=False)
    if suf in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported table type: {path}")


def choose_sources(inv: pd.DataFrame) -> dict[str, Path]:
    """Prefer the frozen handoff instance for every audited object."""
    out: dict[str, Path] = {}
    for obj, g in inv.groupby("object", sort=False):
        paths = [ROOT / str(x) for x in g["path"]]
        existing = [p for p in paths if p.exists()]
        if not existing:
            continue
        frozen = [p for p in existing if "Paper7B_Hosein_to_Shayan_Frozen_Source_Package" in str(p)]
        out[str(obj)] = frozen[0] if frozen else existing[0]
    return out


def find_prefer_frozen(name: str) -> Optional[Path]:
    matches = [p for p in ROOT.rglob(name) if "Step 4" not in str(p)]
    if not matches:
        return None
    frozen = [p for p in matches if "Paper7B_Hosein_to_Shayan_Frozen_Source_Package" in str(p)]
    return frozen[0] if frozen else matches[0]


def table_or_none(sources: dict[str, Path], key: str) -> Optional[pd.DataFrame]:
    p = sources.get(key)
    if p is None:
        return None
    try:
        return load_table(p)
    except Exception:
        return None


def finite_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(df[col], errors="coerce").dropna()


def ci_above_zero(df: pd.DataFrame, low_col: str) -> Optional[int]:
    s = finite_series(df, low_col)
    if s.empty:
        return None
    return int((s > 0).sum())


def summarize_existing(sources: dict[str, Path]) -> list[dict]:
    rows: list[dict] = []

    def add(evidence_id, object_name, statement, status, detail, source_key):
        p = sources.get(source_key)
        rows.append({
            "evidence_id": evidence_id,
            "object": object_name,
            "status": status,
            "frozen_source": rel(p) if p else "NOT FOUND",
            "supported_statement": statement,
            "audit_detail": detail,
        })

    counts = table_or_none(sources, "primary_pair_counts")
    if counts is not None:
        detail = f"rows={len(counts)}"
        if "raw_pairs" in counts:
            detail += f"; total_pairs={int(pd.to_numeric(counts['raw_pairs'], errors='coerce').fillna(0).sum())}"
        add("E01", "primary matched catalogue",
            "The final matched catalogue and intervention support are already frozen.",
            "EXISTS", detail, "primary_pair_counts")
    else:
        add("E01", "primary matched catalogue", "Primary catalogue could not be read.", "MISSING", "", "primary_pair_counts")

    sym = table_or_none(sources, "symmetric_control_results")
    if sym is not None:
        n = len(sym)
        above = ci_above_zero(sym, "bootstrap_95_low")
        detail = f"rows={n}" + (f"; intervals_low>0={above}" if above is not None else "")
        add("E02", "symmetric same-chemistry controls",
            "A direct same-chemistry background comparison already exists; a new generic null is not automatically superior.",
            "EXISTS", detail, "symmetric_control_results")
    else:
        add("E02", "symmetric same-chemistry controls", "Symmetric controls could not be read.", "MISSING", "", "symmetric_control_results")

    hoa = table_or_none(sources, "hoa_condition")
    if hoa is not None:
        detail = f"rows={len(hoa)}"
        if "bootstrap_95_low_rho" in hoa:
            detail += f"; rho_CI_low>0={int((pd.to_numeric(hoa['bootstrap_95_low_rho'], errors='coerce') > 0).sum())}"
        add("E03", "energetic association",
            "Heat-of-adsorption contrast is already an independent energetic correlate of adsorption separation.",
            "EXISTS", detail, "hoa_condition")
    else:
        add("E03", "energetic association", "HOA association table could not be read.", "MISSING", "", "hoa_condition")

    guest = table_or_none(sources, "guest_specificity")
    if guest is not None:
        add("E04", "guest specificity",
            "Paired CO2/co-guest and regime-specific contrasts already define guest/pressure boundaries.",
            "EXISTS", f"rows={len(guest)}", "guest_specificity")
    else:
        add("E04", "guest specificity", "Guest-specificity table could not be read.", "MISSING", "", "guest_specificity")

    adj = table_or_none(sources, "residual_adjustment")
    if adj is not None:
        add("E05", "residual measured geometry adjustment",
            "Residual measured geometry has already been challenged quantitatively; geometry was not claimed to be eliminated.",
            "EXISTS", f"rows={len(adj)}", "residual_adjustment")
    else:
        add("E05", "residual measured geometry adjustment", "Residual-adjustment table could not be read.", "MISSING", "", "residual_adjustment")

    fam = table_or_none(sources, "family_exclusion_summary")
    if fam is not None:
        vals = finite_series(fam, "median_abs_relative_change_excluding_top10")
        detail = f"rows={len(fam)}"
        if not vals.empty:
            detail += f"; max_median_abs_relative_change_top10={float(vals.max()):.6g}"
        add("E06", "family influence",
            "Largest-family/top-family sensitivity is already available and should not be replaced by a decorative transfer claim.",
            "EXISTS", detail, "family_exclusion_summary")
    else:
        add("E06", "family influence", "Family-exclusion summary could not be read.", "MISSING", "", "family_exclusion_summary")

    for eid, key, label in [
        ("E07", "reciprocal_matching", "reciprocal covariance matching"),
        ("E08", "topology_robustness", "topology robustness"),
    ]:
        df = table_or_none(sources, key)
        add(eid, label,
            f"{label.capitalize()} is already part of the frozen robustness evidence." if df is not None else f"{label.capitalize()} could not be read.",
            "EXISTS" if df is not None else "MISSING",
            f"rows={len(df)}" if df is not None else "", key)

    proc = table_or_none(sources, "process_summary")
    if proc is not None:
        est = finite_series(proc, "estimate")
        detail = f"rows={len(proc)}"
        if not est.empty:
            detail += f"; estimate_range=[{float(est.min()):.3f},{float(est.max()):.3f}]"
        add("E09", "process translation",
            "Working-capacity/selectivity translation already defines a bounded process domain.",
            "EXISTS", detail, "process_summary")
    else:
        add("E09", "process translation", "Process summary could not be read.", "MISSING", "", "process_summary")

    cases = table_or_none(sources, "case_set")
    atoms = table_or_none(sources, "atom_charge_rows")
    audit = table_or_none(sources, "charge_mapping_audit")
    detail_bits = []
    if cases is not None:
        detail_bits.append(f"selected_cases={len(cases)}")
    if atoms is not None:
        detail_bits.append(f"atom_charge_rows={len(atoms)}")
    if audit is not None:
        detail_bits.append(f"charge_audit_rows={len(audit)}")
    add("E10", "selected CIF/charge chemistry",
        "Real selected structures and aligned REPEAT charge rows already support case-level chemical fingerprints, but not a global charge mechanism.",
        "EXISTS" if cases is not None and atoms is not None else "PARTIAL",
        "; ".join(detail_bits), "atom_charge_rows")

    return rows


def upgrade_registry() -> pd.DataFrame:
    """Scientific decision map for the coauthor/manual proposals.

    The classifications are intentionally conservative. Phase 1 does not turn an
    unavailable analysis into evidence merely because it was requested in a manual.
    """
    data = [
        ("U01", "Stronger conceptual natural-experiment framing", "USE_NOW", "HIGH", "No new science", "Current evidence already supports this and the manuscript largely uses it."),
        ("U02", "Compact cohort/evidence-support Table 1", "USE_NOW", "MEDIUM_HIGH", "Existing frozen counts", "Useful compression; clarify independent evidence units and limitations."),
        ("U03", "CIF-resolved local coordination close-ups", "SMALL_NEW_ANALYSIS", "HIGH", "Existing CIFs + existing coordination outputs", "Chemically meaningful if coordination identity/quality are audited and no adsorption site is inferred."),
        ("U04", "Selected-case heteroatom/local-environment descriptors", "SMALL_NEW_ANALYSIS", "MEDIUM_HIGH", "Existing CIFs; descriptor definition must be frozen", "Potentially useful as structural context. Must separate simple counts from any pore-accessibility claim."),
        ("U05", "Selected-case charge distribution/localization descriptors", "SMALL_NEW_ANALYSIS", "MEDIUM", "Existing aligned REPEAT charges", "Case-level electrostatic fingerprint only unless a predeclared global hypothesis and validation are added."),
        ("U06", "Bounded intervention/process evidence map", "USE_NOW", "HIGH", "Existing claims + process tables", "Strong final synthesis if it reports supported/conditional/exploratory/outside-domain states, not directional substitution rules."),
        ("U07", "Directional chemical rule cards", "REJECT", "LOW", "Would require oriented interventions and stronger mechanism evidence", "Primary transitions are unordered. A directional synthesis recipe would exceed the estimand."),
        ("U08", "Shuffled-label/permutation falsification", "CONDITIONAL_NEW_ANALYSIS", "MEDIUM", "Requires dependence-preserving randomization design", "Could strengthen inference, but naive row shuffling is invalid. Advance only after exchangeability audit."),
        ("U09", "Loose-match negative control", "REJECT_UNLESS_JUSTIFIED", "LOW", "Requires scientifically meaningful null definition", "Loosening geometry deliberately changes the estimand and may create an uninterpretable null."),
        ("U10", "True held-out linker/metal/topology transfer", "EXTENDED_ONLY", "MEDIUM_HIGH", "New analysis and explicit transfer estimand", "Potentially valuable, but it is not the same as robustness and would reopen the statistical scope."),
        ("U11", "Permutation p-values and FDR across conditions", "CONDITIONAL_NEW_ANALYSIS", "MEDIUM", "Valid dependence-aware null + multiplicity plan", "Not needed merely to decorate bootstrap results; useful only if tied to a predeclared inferential question."),
        ("U12", "Global pore-accessible heteroatom intervention", "EXTENDED_ONLY", "MEDIUM", "New descriptor, accessibility definition, validation, matching/estimand", "Do not infer pore accessibility from element counts alone."),
        ("U13", "Global charge-localization intervention", "EXTENDED_ONLY", "MEDIUM", "New descriptor/estimand and validation", "REPEAT charge fingerprints exist, but global localization as an explanatory intervention was not tested."),
        ("U14", "GCMC adsorption-density/site-occupancy maps for selected cases", "EXTENDED_ONLY", "HIGH", "Reproduce original force-field/charge adsorption first", "Potentially the highest-value mechanistic extension if reproduction passes and the map answers a specific case-level hypothesis."),
        ("U15", "Framework-guest energy decomposition", "EXTENDED_ONLY", "HIGH", "Validated selected-case host-guest simulations", "Useful only if electrostatic versus dispersion contrast directly tests a Phase-2/4 hypothesis."),
        ("U16", "DFT binding/site validation", "EXTENDED_ONLY", "HIGH", "One sharp hypothesis after classical reproduction", "Use on 1-2 pairs only; not a new screening project."),
        ("U17", "SHAP/UMAP/t-SNE expansion", "REJECT", "LOW", "None", "Would dilute the controlled-comparison chemistry story unless it uniquely answers a transfer/domain question."),
        ("U18", "Expand to 7 main figures and 16-19 SI figures", "REJECT", "LOW", "None", "More panels are not more evidence. Add a figure only if a new scientific object survives a gate."),
    ]
    return pd.DataFrame(data, columns=["upgrade_id", "proposal", "phase1_decision", "potential_value", "required_new_object", "reason"])


def make_claim_audit() -> pd.DataFrame:
    p = find_prefer_frozen("06_claim_evidence_matrix.csv")
    if p is None:
        return pd.DataFrame(columns=["claim_id", "claim", "status", "boundary", "main_text", "source"])
    df = pd.read_csv(p, low_memory=False)
    keep = [c for c in ["claim_id", "claim", "status", "primary_evidence", "step2_support", "boundary", "main_text", "prohibited_wording"] if c in df.columns]
    out = df[keep].copy()
    out["source"] = rel(p)
    return out


def searchable_context_inventory() -> pd.DataFrame:
    """Locate richer original objects that may support Phase 2 without claiming they are evidence yet."""
    patterns = {
        "coordination": ["*coordination*.csv", "*coordination*.parquet"],
        "cif_audit": ["*cif*audit*.csv", "*chemistry*audit*.csv"],
        "case_inspection": ["candidate_*", "*structure_case*"],
        "cohort": ["*cohort*.csv", "*cohort*.parquet"],
        "topology": ["*topology*.csv", "*topology*.parquet"],
        "charge": ["*charge*.csv", "*charge*.parquet"],
    }
    rows = []
    seen = set()
    for category, globs in patterns.items():
        for pat in globs:
            for p in ROOT.rglob(pat):
                if "Step 4" in str(p) or not p.is_file():
                    continue
                key = str(p.resolve())
                if key in seen:
                    continue
                seen.add(key)
                rows.append({"category": category, "path": rel(p), "size_bytes": p.stat().st_size})
    return pd.DataFrame(rows).sort_values(["category", "path"]) if rows else pd.DataFrame(columns=["category", "path", "size_bytes"])


def main():
    if not INVENTORY.exists():
        raise FileNotFoundError(
            f"Phase 0 inventory not found: {INVENTORY}\nRun 01_phase0_frozen_audit.py first."
        )
    inv = pd.read_csv(INVENTORY, low_memory=False)
    required = {"object", "path"}
    if not required.issubset(inv.columns):
        raise RuntimeError(f"Phase 0 inventory missing columns {sorted(required - set(inv.columns))}")

    sources = choose_sources(inv)
    source_df = pd.DataFrame([
        {"object": k, "canonical_step4_read_source": rel(v)} for k, v in sorted(sources.items())
    ])
    source_df.to_csv(RESULTS / "01_canonical_source_map.csv", index=False)

    evidence = pd.DataFrame(summarize_existing(sources))
    evidence.to_csv(RESULTS / "02_existing_evidence_map.csv", index=False)

    upgrades = upgrade_registry()
    upgrades.to_csv(RESULTS / "03_upgrade_decision_map.csv", index=False)

    claims = make_claim_audit()
    claims.to_csv(RESULTS / "04_frozen_claim_boundary_map.csv", index=False)

    context = searchable_context_inventory()
    context.to_csv(RESULTS / "05_richer_context_inventory.csv", index=False)

    missing = evidence[evidence["status"].eq("MISSING")]
    decision = "PASS" if missing.empty else "CONDITIONAL"

    # Priority shortlist is intentionally small.
    shortlist_ids = ["U02", "U03", "U04", "U06", "U08", "U14"]
    shortlist = upgrades[upgrades["upgrade_id"].isin(shortlist_ids)].copy()
    shortlist["sequence"] = shortlist["upgrade_id"].map({
        "U02": 1, "U03": 2, "U04": 3, "U06": 4, "U08": 5, "U14": 6
    })
    shortlist = shortlist.sort_values("sequence")
    shortlist.to_csv(RESULTS / "06_phase1_shortlist.csv", index=False)

    report = []
    report += [
        "# PROJECT 7B STEP 4 - PHASE 1 EXISTING-EVIDENCE EXHAUSTION AUDIT",
        "",
        f"Decision: **{decision}**",
        "",
        "## Source policy",
        "",
        "Step 4 reads the hash-identical frozen handoff copy by default. Original analysis/Step 2 copies are retained as provenance mirrors or richer context when an object was intentionally reduced in the handoff.",
        "",
        "## What the frozen project already contains",
        "",
    ]
    for r in evidence.itertuples(index=False):
        report.append(f"- **{r.evidence_id} {r.object}: {r.status}.** {r.supported_statement} ({r.audit_detail})")

    report += [
        "",
        "## Phase-1 scientific decision",
        "",
        "The project does not need a broad re-analysis. The strongest plausible upgrade path is narrow: improve the evidence-support table; audit and enrich selected CIF cases using real coordination/local-environment information; produce a non-directional bounded evidence/domain map; and only then decide whether one rigorous falsification or selected-case host-guest simulation is worth opening.",
        "",
        "### Shortlist, in order",
        "",
    ]
    for r in shortlist.itertuples(index=False):
        report.append(f"{int(r.sequence)}. **{r.proposal}** — `{r.phase1_decision}` / value `{r.potential_value}`. {r.reason}")

    report += [
        "",
        "## Hard stops",
        "",
        "- No directional linker/metal substitution rules from unordered pair effects.",
        "- No pore-accessible-heteroatom claim from raw N/O/S/halogen counts alone.",
        "- No oxidation-state, charge-transfer, or adsorption-site claim from REPEAT charges alone.",
        "- No shuffled-row null unless exchangeability under shared-framework/dependence structure is justified.",
        "- No DFT or new GCMC until an explicit selected-case hypothesis and reproduction gate exist.",
        "- No SHAP/UMAP/t-SNE or extra figure merely to make the paper look more complex.",
        "",
        "## Next gate",
        "",
        "Proceed to Phase 2 only for U03/U04/U05 after inspecting the richer coordination/CIF/charge objects listed in `05_richer_context_inventory.csv`. Phase 2 must freeze descriptor definitions before correlating any new structural-chemistry quantity with adsorption.",
    ]
    (RESULTS / "07_phase1_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    manifest = {
        "phase": "Step 4 Phase 1 existing-evidence exhaustion audit",
        "decision": decision,
        "read_only_upstream": True,
        "canonical_objects": len(sources),
        "existing_evidence_objects": len(evidence),
        "missing_evidence_objects": int(len(missing)),
        "upgrade_proposals_classified": int(len(upgrades)),
        "shortlisted_proposals": shortlist_ids,
        "outputs": [
            "01_canonical_source_map.csv",
            "02_existing_evidence_map.csv",
            "03_upgrade_decision_map.csv",
            "04_frozen_claim_boundary_map.csv",
            "05_richer_context_inventory.csv",
            "06_phase1_shortlist.csv",
            "07_phase1_report.md",
        ],
        "python": sys.version,
        "pandas": pd.__version__,
    }
    (RESULTS / "08_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("PROJECT 7B STEP 4 - PHASE 1 EXISTING-EVIDENCE EXHAUSTION AUDIT")
    print("=" * 72)
    print(f"Decision: {decision}")
    print(f"Canonical frozen objects mapped: {len(sources)}")
    print(f"Existing evidence objects audited: {len(evidence)}")
    print(f"Missing evidence objects: {len(missing)}")
    print(f"Upgrade proposals classified: {len(upgrades)}")
    print("\nPriority shortlist:")
    for r in shortlist.itertuples(index=False):
        print(f"  {int(r.sequence)}. {r.proposal} -> {r.phase1_decision}")
    print("\nNo new scientific effect, matching, pair selection, bootstrap, or process metric was computed.")
    print(f"Outputs: {RESULTS}")


if __name__ == "__main__":
    main()
