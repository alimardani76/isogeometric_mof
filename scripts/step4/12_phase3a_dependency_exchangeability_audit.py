#!/usr/bin/env python3
"""
Project 7B Step 4 - Phase 3A
Dependency and exchangeability audit for any proposed permutation/randomization test.

Purpose
-------
Before shuffling anything, establish the actual dependence structure of the frozen
Project 7B primary pairs, repeated adsorption conditions, and same-chemistry controls.

This phase DOES NOT:
- permute labels,
- calculate a p-value,
- recompute pair effects,
- change matching,
- select new pairs,
- alter any Step 1-3 object.

The audit asks whether a scientifically defensible randomization group exists.
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd

TITLE = "PROJECT 7B STEP 4 - PHASE 3A DEPENDENCY / EXCHANGEABILITY AUDIT"


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
    # conservative substring resolution only for terms >= 4 chars
    for actual in df.columns:
        al = str(actual).lower()
        for c in candidates:
            cc = c.lower()
            if len(cc) >= 4 and cc in al:
                return actual
    if required:
        raise RuntimeError(
            f"Could not resolve {candidates}. Available columns: {list(df.columns)}"
        )
    return None


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path, low_memory=False)


def find_unique_by_basename(base: Path, basename: str) -> Path:
    hits = list(base.rglob(basename))
    if not hits:
        raise FileNotFoundError(f"Could not find {basename} under {base}")
    # Frozen package should contain one canonical copy. If more than one, prefer shortest path.
    hits = sorted(hits, key=lambda p: (len(p.parts), str(p)))
    return hits[0]


class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}

    def add(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x):
        p = self.parent[x]
        if p != x:
            self.parent[x] = self.find(p)
        return self.parent[x]

    def union(self, a, b):
        self.add(a)
        self.add(b)
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


def graph_audit(pairs: pd.DataFrame, a_col: str, b_col: str, intervention_col: str | None):
    x = pairs.copy()
    x["_a"] = x[a_col].astype(str).map(norm_id)
    x["_b"] = x[b_col].astype(str).map(norm_id)
    x = x[(x["_a"] != "") & (x["_b"] != "") & (x["_a"] != x["_b"])].copy()

    uf = UnionFind()
    degree = Counter()
    edge_keys = []
    for a, b in zip(x["_a"], x["_b"]):
        uf.union(a, b)
        degree[a] += 1
        degree[b] += 1
        edge_keys.append(tuple(sorted((a, b))))

    nodes = sorted(degree)
    comp_nodes = defaultdict(list)
    for n in nodes:
        comp_nodes[uf.find(n)].append(n)

    comp_edges = Counter()
    for a, b in edge_keys:
        comp_edges[uf.find(a)] += 1

    comp_rows = []
    for root_id, ns in comp_nodes.items():
        ds = [degree[n] for n in ns]
        comp_rows.append({
            "component_id": str(root_id),
            "n_frameworks": len(ns),
            "n_pair_edges": int(comp_edges[root_id]),
            "max_framework_degree": int(max(ds)) if ds else 0,
            "mean_framework_degree": float(np.mean(ds)) if ds else np.nan,
        })

    comp_df = pd.DataFrame(comp_rows).sort_values(
        ["n_pair_edges", "n_frameworks"], ascending=False
    ) if comp_rows else pd.DataFrame()

    deg_values = np.array(list(degree.values()), dtype=float)
    summary = {
        "pair_rows": int(len(x)),
        "unique_undirected_pair_edges": int(len(set(edge_keys))),
        "duplicate_undirected_edge_rows": int(len(edge_keys) - len(set(edge_keys))),
        "unique_frameworks": int(len(nodes)),
        "frameworks_used_in_more_than_one_pair": int(sum(v > 1 for v in degree.values())),
        "fraction_frameworks_used_in_more_than_one_pair": (
            float(np.mean(deg_values > 1)) if len(deg_values) else np.nan
        ),
        "framework_degree_median": float(np.median(deg_values)) if len(deg_values) else np.nan,
        "framework_degree_p95": float(np.quantile(deg_values, 0.95)) if len(deg_values) else np.nan,
        "framework_degree_max": int(max(degree.values())) if degree else 0,
        "connected_components": int(len(comp_nodes)),
        "largest_component_frameworks": int(comp_df.iloc[0]["n_frameworks"]) if len(comp_df) else 0,
        "largest_component_pair_edges": int(comp_df.iloc[0]["n_pair_edges"]) if len(comp_df) else 0,
    }

    intervention_df = pd.DataFrame()
    if intervention_col and intervention_col in x.columns:
        rows = []
        for label, g in x.groupby(intervention_col, dropna=False):
            d = Counter()
            e = set()
            for a, b in zip(g["_a"], g["_b"]):
                d[a] += 1
                d[b] += 1
                e.add(tuple(sorted((a, b))))
            vals = np.array(list(d.values()), dtype=float)
            rows.append({
                "intervention": str(label),
                "pair_rows": len(g),
                "unique_pair_edges": len(e),
                "unique_frameworks": len(d),
                "frameworks_degree_gt1": int(sum(v > 1 for v in d.values())),
                "max_framework_degree": int(max(d.values())) if d else 0,
            })
        intervention_df = pd.DataFrame(rows)

    deg_df = pd.DataFrame([
        {"framework_id": k, "pair_degree": v}
        for k, v in sorted(degree.items(), key=lambda kv: (-kv[1], kv[0]))
    ])

    return summary, deg_df, comp_df, intervention_df


def effect_repetition_audit(effects: pd.DataFrame, pair_col: str):
    condition_candidates = [
        "condition", "condition_id", "adsorption_condition", "guest_pressure",
        "gas_pressure", "state_point", "condition_label"
    ]
    cond_col = resolve_col(effects, condition_candidates, required=False)

    grouped = effects.groupby(pair_col, dropna=False).size()
    out = {
        "effect_rows": int(len(effects)),
        "unique_pairs_in_effects": int(effects[pair_col].nunique(dropna=True)),
        "rows_per_pair_min": int(grouped.min()) if len(grouped) else 0,
        "rows_per_pair_median": float(grouped.median()) if len(grouped) else np.nan,
        "rows_per_pair_max": int(grouped.max()) if len(grouped) else 0,
        "pairs_with_repeated_rows": int((grouped > 1).sum()),
        "condition_column": cond_col,
        "unique_conditions": int(effects[cond_col].nunique(dropna=True)) if cond_col else None,
    }

    per_pair = grouped.rename("effect_rows_per_pair").reset_index()
    if cond_col:
        nc = effects.groupby(pair_col)[cond_col].nunique(dropna=True).rename("unique_conditions_per_pair")
        per_pair = per_pair.merge(nc.reset_index(), on=pair_col, how="left")
    return out, per_pair


def schema_audit(name: str, df: pd.DataFrame, primary_pair_values: set[str]):
    interesting_terms = [
        "pair", "target", "control", "match", "set", "group", "block",
        "chem", "intervention", "condition", "guest", "pressure",
        "framework", "mof", "id_a", "id_b"
    ]
    interesting_cols = [
        c for c in df.columns
        if any(t in str(c).lower() for t in interesting_terms)
    ]

    pairlike_cols = [
        c for c in interesting_cols if "pair" in str(c).lower()
    ]
    grouplike_cols = [
        c for c in interesting_cols
        if any(t in str(c).lower() for t in ["set", "group", "block", "match"])
    ]
    targetlike_cols = [
        c for c in interesting_cols
        if any(t in str(c).lower() for t in ["target", "primary", "focal"])
    ]

    overlap_rows = []
    for c in pairlike_cols + targetlike_cols:
        vals = set(df[c].dropna().astype(str))
        overlap = len(vals & primary_pair_values)
        overlap_rows.append({
            "table": name,
            "column": str(c),
            "unique_values": len(vals),
            "primary_pair_id_overlap": overlap,
        })

    return {
        "table": name,
        "rows": len(df),
        "columns": json.dumps([str(c) for c in df.columns]),
        "interesting_columns": json.dumps([str(c) for c in interesting_cols]),
        "pairlike_columns": json.dumps([str(c) for c in pairlike_cols]),
        "grouplike_columns": json.dumps([str(c) for c in grouplike_cols]),
        "targetlike_columns": json.dumps([str(c) for c in targetlike_cols]),
        "has_explicit_group_or_match_column": bool(grouplike_cols),
        "has_target_or_primary_column": bool(targetlike_cols),
    }, overlap_rows


def candidate_scheme_map(
    graph_summary,
    effect_summary,
    control_schema_rows,
):
    shared_frameworks = graph_summary["frameworks_used_in_more_than_one_pair"] > 0
    repeated_conditions = effect_summary["pairs_with_repeated_rows"] > 0

    has_control_grouping = any(r["has_explicit_group_or_match_column"] for r in control_schema_rows)
    has_target_link = any(r["has_target_or_primary_column"] for r in control_schema_rows)

    rows = []

    rows.append({
        "scheme": "shuffle_pair_condition_rows_globally",
        "status": "REJECT",
        "reason": (
            "Pair-condition rows are not independent: the same frozen pair appears at repeated "
            "adsorption conditions, and frameworks can participate in multiple pair edges."
        ),
        "would_test": "undefined mixture of condition, pair, and framework structure",
    })

    rows.append({
        "scheme": "shuffle_chemistry_or_control_labels_across_pairs",
        "status": "REJECT_AS_CURRENTLY_DEFINED" if shared_frameworks else "CONDITIONAL",
        "reason": (
            "Pair edges share framework nodes, so independent edge-label exchangeability does not hold. "
            "Even without node reuse, chemistry class is observed structural metadata rather than a randomized assignment."
        ),
        "would_test": "distributional label exchangeability, not the frozen matched natural-experiment estimand",
    })

    rows.append({
        "scheme": "shuffle_conditions_within_pair",
        "status": "REJECT",
        "reason": (
            "Chemistry intervention is constant within a pair. Reordering pressure/guest conditions "
            "does not generate a null for chemistry-versus-control separation."
        ),
        "would_test": "condition ordering, not chemistry",
    })

    rows.append({
        "scheme": "sign_flip_absolute_pair_effects",
        "status": "REJECT",
        "reason": (
            "The primary effect object is magnitude-based/unordered. Sign flipping non-negative "
            "magnitudes has no valid symmetry interpretation for the chemistry-versus-control claim."
        ),
        "would_test": "artificial symmetry around zero",
    })

    rows.append({
        "scheme": "connected_component_block_permutation",
        "status": "CONDITIONAL_NOT_YET_JUSTIFIED",
        "reason": (
            "Connected components can preserve shared-framework dependence, but component independence "
            "does not by itself make chemistry labels exchangeable across components."
        ),
        "would_test": "component-level label exchangeability if a defensible assignment model existed",
    })

    rows.append({
        "scheme": "node_label_or_QAP_style_permutation",
        "status": "REJECT_UNLESS_FULL_PAIR_CONSTRUCTION_CAN_BE_REGENERATED",
        "reason": (
            "The intervention is an edge-level chemistry comparison under strict geometric/matching rules. "
            "Permuting framework/node labels would generally destroy those eligibility constraints unless the "
            "entire candidate-pair construction were regenerated under the null."
        ),
        "would_test": "graph-label invariance under a reconstructed null pair-generation process",
    })

    rows.append({
        "scheme": "matched_set_treatment_control_swap",
        "status": (
            "CONDITIONAL_REQUIRES_ASSIGNMENT_JUSTIFICATION"
            if (has_control_grouping and has_target_link)
            else "NO_IMPLEMENTABLE_MATCHED_SET_OBJECT_DETECTED_YET"
        ),
        "reason": (
            "A within-matched-set permutation is only defensible if the frozen controls contain an explicit "
            "focal/control set and if chemistry/control labels are exchangeable under a stated observational "
            "assignment model. Matching alone does not supply random assignment."
        ),
        "would_test": "focal-versus-control label exchangeability within pre-specified matched sets",
    })

    rows.append({
        "scheme": "blocked_residual_permutation_model",
        "status": "CONDITIONAL_EXTENDED_METHOD",
        "reason": (
            "Restricted residual permutation can accommodate structured dependence only after a "
            "pre-specified statistical model and valid exchangeability blocks are defined. This would "
            "be a new inferential layer, not a simple robustness check."
        ),
        "would_test": "a model coefficient under blockwise exchangeable residuals",
    })

    rows.append({
        "scheme": "dependency_cluster_bootstrap_or_sandwich_sensitivity",
        "status": "POSSIBLE_NON_RANDOMIZATION_FALLBACK",
        "reason": (
            "Clustering by framework-connected component could preserve observed dependence for an "
            "asymptotic sensitivity analysis, but it would not be an exact shuffled-label null and "
            "would require enough independent components."
        ),
        "would_test": "sampling uncertainty under a cluster-level approximation",
    })

    return pd.DataFrame(rows)


def main():
    print(TITLE)
    print("=" * 72)

    root = find_root(Path.cwd())
    frozen = root / "Step 3 results" / "Paper7B_Hosein_to_Shayan_Frozen_Source_Package"
    out = root / "Step 4 results" / "03_falsification" / "phase3a_dependency_exchangeability_audit"
    out.mkdir(parents=True, exist_ok=True)

    sources = {
        "primary_pairs": find_unique_by_basename(frozen, "final_primary_pairs.parquet"),
        "pair_effects": find_unique_by_basename(frozen, "final_primary_pair_effect_magnitudes.parquet"),
        "primary_controls": find_unique_by_basename(frozen, "step3_same_chemistry_control_results.csv"),
        "symmetric_controls": find_unique_by_basename(frozen, "step5b_symmetric_control_results.csv"),
    }

    primary = read_table(sources["primary_pairs"])
    effects = read_table(sources["pair_effects"])
    primary_controls = read_table(sources["primary_controls"])
    symmetric_controls = read_table(sources["symmetric_controls"])

    a_col = resolve_col(
        primary,
        ["id_a", "mof_a", "mof_id_a", "framework_a", "framework_id_a"],
        required=True,
    )
    b_col = resolve_col(
        primary,
        ["id_b", "mof_b", "mof_id_b", "framework_b", "framework_id_b"],
        required=True,
    )
    pair_col_primary = resolve_col(
        primary,
        ["pair_id", "pair_key", "pair"],
        required=True,
    )
    intervention_col = resolve_col(
        primary,
        ["intervention", "intervention_class", "change_type", "pair_type"],
        required=False,
    )

    pair_col_effects = resolve_col(
        effects,
        ["pair_id", "pair_key", "pair"],
        required=True,
    )

    graph_summary, deg_df, comp_df, intervention_df = graph_audit(
        primary, a_col, b_col, intervention_col
    )
    effect_summary, effect_per_pair = effect_repetition_audit(
        effects, pair_col_effects
    )

    primary_pair_values = set(primary[pair_col_primary].dropna().astype(str))

    control_schema_rows = []
    overlap_rows = []
    for name, df in [
        ("primary_controls", primary_controls),
        ("symmetric_controls", symmetric_controls),
    ]:
        rec, overlaps = schema_audit(name, df, primary_pair_values)
        control_schema_rows.append(rec)
        overlap_rows.extend(overlaps)

    schemes = candidate_scheme_map(
        graph_summary, effect_summary, control_schema_rows
    )

    # Save audit outputs.
    pd.DataFrame([graph_summary]).to_csv(out / "phase3a_primary_pair_graph_summary.csv", index=False)
    deg_df.to_csv(out / "phase3a_framework_pair_degree.csv", index=False)
    comp_df.to_csv(out / "phase3a_framework_connected_components.csv", index=False)
    intervention_df.to_csv(out / "phase3a_intervention_dependency_summary.csv", index=False)
    pd.DataFrame([effect_summary]).to_csv(out / "phase3a_effect_repetition_summary.csv", index=False)
    effect_per_pair.to_csv(out / "phase3a_effect_rows_per_pair.csv", index=False)
    pd.DataFrame(control_schema_rows).to_csv(out / "phase3a_control_table_schema_audit.csv", index=False)
    pd.DataFrame(overlap_rows).to_csv(out / "phase3a_control_primary_pair_linkage.csv", index=False)
    schemes.to_csv(out / "phase3a_candidate_randomization_schemes.csv", index=False)

    # Source schema for exact follow-up.
    schemas = []
    for name, df in [
        ("primary_pairs", primary),
        ("pair_effects", effects),
        ("primary_controls", primary_controls),
        ("symmetric_controls", symmetric_controls),
    ]:
        schemas.append({
            "object": name,
            "path": str(sources[name].relative_to(root)),
            "rows": len(df),
            "columns": json.dumps([str(c) for c in df.columns]),
        })
    pd.DataFrame(schemas).to_csv(out / "phase3a_source_schema.csv", index=False)

    # Conservative conclusion.
    explicit_control_groups = any(
        r["has_explicit_group_or_match_column"] for r in control_schema_rows
    )
    explicit_target_links = any(
        r["has_target_or_primary_column"] for r in control_schema_rows
    )

    if explicit_control_groups and explicit_target_links:
        decision = "CONDITIONAL_MATCHED_SET_DESIGN_REQUIRES_INSPECTION"
        next_step = "INSPECT_EXACT CONTROL MATCH-SET SEMANTICS BEFORE ANY PERMUTATION"
    else:
        decision = "NO_VALID_SHUFFLED_LABEL_TEST_ESTABLISHED"
        next_step = "DO NOT PERMUTE; EXISTING CONTROL DISTRIBUTIONS REMAIN THE DEFENSIBLE NULL REFERENCE"

    summary = {
        "decision": decision,
        "primary_pair_rows": graph_summary["pair_rows"],
        "unique_frameworks": graph_summary["unique_frameworks"],
        "frameworks_used_in_more_than_one_pair": graph_summary["frameworks_used_in_more_than_one_pair"],
        "connected_components": graph_summary["connected_components"],
        "largest_component_frameworks": graph_summary["largest_component_frameworks"],
        "largest_component_pair_edges": graph_summary["largest_component_pair_edges"],
        "effect_rows": effect_summary["effect_rows"],
        "pairs_with_repeated_effect_rows": effect_summary["pairs_with_repeated_rows"],
        "rows_per_pair_median": effect_summary["rows_per_pair_median"],
        "effect_condition_column": effect_summary["condition_column"],
        "explicit_control_group_columns_detected": explicit_control_groups,
        "explicit_target_link_columns_detected": explicit_target_links,
        "next_step": next_step,
    }
    (out / "phase3a_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    report = [
        "PROJECT 7B STEP 4 - PHASE 3A DEPENDENCY / EXCHANGEABILITY AUDIT",
        "=" * 72,
        "",
        f"Decision: {decision}",
        "",
        "Core principle:",
        "A permutation/randomization test is only valid under a transformation that preserves",
        "the joint null distribution. Shared frameworks, repeated conditions, and observational",
        "chemistry labels therefore cannot be ignored.",
        "",
        "This audit does not claim that connected components or matched sets are automatically",
        "exchangeability blocks. It only identifies them as possible dependence-preserving units.",
        "",
        f"Next: {next_step}",
    ]
    (out / "phase3a_report.md").write_text("\n".join(report), encoding="utf-8")

    print(f"Decision: {decision}")
    print(f"Primary pair rows: {graph_summary['pair_rows']}")
    print(f"Unique frameworks in primary pair graph: {graph_summary['unique_frameworks']}")
    print(
        "Frameworks reused across >1 primary pair: "
        f"{graph_summary['frameworks_used_in_more_than_one_pair']} "
        f"({graph_summary['fraction_frameworks_used_in_more_than_one_pair']:.1%})"
    )
    print(f"Framework-pair connected components: {graph_summary['connected_components']}")
    print(
        "Largest connected component: "
        f"{graph_summary['largest_component_frameworks']} frameworks / "
        f"{graph_summary['largest_component_pair_edges']} pair edges"
    )
    print(f"Pair-effect rows: {effect_summary['effect_rows']}")
    print(f"Pairs with repeated effect rows: {effect_summary['pairs_with_repeated_rows']}")
    print(f"Median effect rows per pair: {effect_summary['rows_per_pair_median']}")
    print(f"Resolved condition column: {effect_summary['condition_column']}")
    print(f"Explicit control grouping/match columns detected: {explicit_control_groups}")
    print(f"Explicit target/primary linkage columns detected: {explicit_target_links}")

    print("\nCandidate randomization schemes:")
    for _, r in schemes.iterrows():
        print(f"  {r['scheme']} -> {r['status']}")

    print(f"\nNext: {next_step}")
    print("No labels were shuffled and no p-value or new scientific effect was computed.")
    print(f"Outputs: {out}")


if __name__ == "__main__":
    main()
