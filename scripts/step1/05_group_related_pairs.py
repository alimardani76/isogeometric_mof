#!/usr/bin/env python3
"""Define dependence families for stringent Project 7 chemistry comparisons.

Purpose
-------
Pairs that share a framework, or a clean/freeONLY representation of the same
named framework, are not independent evidence. This script keeps every raw pair
but assigns duplicate-aware evidence-unit and connected-family identifiers before
adsorption outcomes are introduced.

Scientific boundaries
---------------------
- Uses only stringent geometry matches.
- Metal pairs must be coordination-compatible under both tested CrystalNN settings.
- Uses no adsorption outcomes.
- Estimates no effects.
- Fills no missing scientific values.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha1
from pathlib import Path
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"

METAL_FILE = ANALYSIS / "metal_pairs_coordination_classified.parquet"
LINKER_FILE = ANALYSIS / "full_pair_rules" / "linker_family_change.parquet"
FUNCTIONAL_FILE = ANALYSIS / "full_pair_rules" / "functional_motif_change.parquet"

LEDGER_FILE = ANALYSIS / "stringent_pair_dependence_ledger.parquet"
EVIDENCE_FILE = ANALYSIS / "stringent_pair_evidence_units.csv"
FAMILY_FILE = ANALYSIS / "stringent_pair_families.csv"
SUMMARY_FILE = ANALYSIS / "stringent_pair_dependence_summary.csv"

N_JOBS = 1


def variant_family(value: str) -> str:
    """Group only explicit terminal clean/freeONLY representations."""
    text = str(value).strip()
    text = re.sub(r"(?i)_clean$", "", text)
    text = re.sub(r"(?i)_freeONLY$", "", text)
    return text


def stable_id(prefix: str, *parts: str) -> str:
    raw = prefix + "|" + "|".join(map(str, parts))
    return prefix + "_" + sha1(raw.encode("utf-8")).hexdigest()[:16]


def transition_label(row: pd.Series) -> str:
    if row["intervention"] == "metal_substitution":
        values = sorted([str(row["metals_a"]), str(row["metals_b"])])
        return values[0] + " <-> " + values[1]
    if row["intervention"] == "linker_family_change":
        values = sorted([str(int(row["linker_cluster_a"])), str(int(row["linker_cluster_b"]))])
        return values[0] + " <-> " + values[1]
    values = sorted([str(int(row["functional_cluster_a"])), str(int(row["functional_cluster_b"]))])
    return values[0] + " <-> " + values[1]


class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}

    def add(self, item):
        if item not in self.parent:
            self.parent[item] = item
            self.rank[item] = 0

    def find(self, item):
        root = item
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[item] != item:
            parent = self.parent[item]
            self.parent[item] = root
            item = parent
        return root

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


def load_pairs() -> pd.DataFrame:
    missing = [str(path) for path in [METAL_FILE, LINKER_FILE, FUNCTIONAL_FILE] if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required pair files:\n" + "\n".join(missing))

    metal = pd.read_parquet(METAL_FILE)
    metal = metal.loc[
        metal["geometry_tier"].eq("stringent")
        & metal["coordination_class"].eq("coordination_compatible")
    ].copy()
    metal["intervention"] = "metal_substitution"

    linker = pd.read_parquet(LINKER_FILE)
    linker = linker.loc[linker["geometry_tier"].eq("stringent")].copy()
    linker["intervention"] = "linker_family_change"

    functional = pd.read_parquet(FUNCTIONAL_FILE)
    functional = functional.loc[functional["geometry_tier"].eq("stringent")].copy()
    functional["intervention"] = "functional_motif_change"

    pairs = pd.concat([metal, linker, functional], ignore_index=True, sort=False)
    if pairs[["intervention", "pair_lo", "pair_hi"]].duplicated().any():
        raise RuntimeError("Duplicate raw unordered pairs within an intervention")
    return pairs


def main():
    pairs = load_pairs()
    pairs["variant_a"] = pairs["id_a"].map(variant_family)
    pairs["variant_b"] = pairs["id_b"].map(variant_family)
    pairs["variant_lo"] = pairs[["variant_a", "variant_b"]].min(axis=1)
    pairs["variant_hi"] = pairs[["variant_a", "variant_b"]].max(axis=1)
    pairs["transition"] = pairs.apply(transition_label, axis=1)

    pairs["evidence_unit_id"] = pairs.apply(
        lambda row: stable_id(
            "evidence",
            row["intervention"],
            row["variant_lo"],
            row["variant_hi"],
            row["transition"],
        ),
        axis=1,
    )

    # Connected components capture all dependence created by shared framework variants.
    family_ids = {}
    for intervention, group in pairs.groupby("intervention", sort=False):
        uf = UnionFind()
        for row in group.itertuples(index=False):
            uf.union(row.variant_lo, row.variant_hi)
        components = defaultdict(list)
        for node in uf.parent:
            components[uf.find(node)].append(node)
        root_to_family = {
            root: stable_id("family", intervention, *sorted(nodes))
            for root, nodes in components.items()
        }
        for node in uf.parent:
            family_ids[(intervention, node)] = root_to_family[uf.find(node)]

    pairs["dependence_family_id"] = pairs.apply(
        lambda row: family_ids[(row["intervention"], row["variant_lo"])], axis=1
    )

    # Endpoint reuse is reported, not corrected silently.
    endpoint_counts = Counter()
    for row in pairs.itertuples(index=False):
        endpoint_counts[(row.intervention, row.variant_a)] += 1
        endpoint_counts[(row.intervention, row.variant_b)] += 1
    pairs["reuse_count_a"] = pairs.apply(
        lambda row: endpoint_counts[(row["intervention"], row["variant_a"])], axis=1
    )
    pairs["reuse_count_b"] = pairs.apply(
        lambda row: endpoint_counts[(row["intervention"], row["variant_b"])], axis=1
    )
    pairs["maximum_endpoint_reuse"] = pairs[["reuse_count_a", "reuse_count_b"]].max(axis=1)

    evidence = (
        pairs.groupby(["intervention", "evidence_unit_id", "dependence_family_id", "transition"], as_index=False)
        .agg(
            raw_pair_rows=("pair_lo", "size"),
            variant_lo=("variant_lo", "first"),
            variant_hi=("variant_hi", "first"),
            maximum_endpoint_reuse=("maximum_endpoint_reuse", "max"),
        )
    )

    families = (
        evidence.groupby(["intervention", "dependence_family_id"], as_index=False)
        .agg(
            evidence_units=("evidence_unit_id", "nunique"),
            raw_pair_rows=("raw_pair_rows", "sum"),
            transitions=("transition", "nunique"),
            framework_variants=(
                "variant_lo",
                lambda values: len(set(values)),
            ),
        )
    )

    # Correct framework-variant counts using both endpoints.
    variant_sets = defaultdict(set)
    for row in pairs.itertuples(index=False):
        key = (row.intervention, row.dependence_family_id)
        variant_sets[key].update([row.variant_a, row.variant_b])
    families["framework_variants"] = families.apply(
        lambda row: len(variant_sets[(row["intervention"], row["dependence_family_id"])]),
        axis=1,
    )

    summary = (
        pairs.groupby("intervention", as_index=False)
        .agg(
            raw_pairs=("pair_lo", "size"),
            evidence_units=("evidence_unit_id", "nunique"),
            dependence_families=("dependence_family_id", "nunique"),
            framework_variants=("variant_a", lambda values: len(set(values))),
            maximum_endpoint_reuse=("maximum_endpoint_reuse", "max"),
        )
    )
    # Count unique variants over both endpoints.
    for index, row in summary.iterrows():
        group = pairs.loc[pairs["intervention"].eq(row["intervention"])]
        summary.loc[index, "framework_variants"] = len(
            set(group["variant_a"]) | set(group["variant_b"])
        )

    pairs.to_parquet(LEDGER_FILE, index=False)
    evidence.to_csv(EVIDENCE_FILE, index=False)
    families.to_csv(FAMILY_FILE, index=False)
    summary.to_csv(SUMMARY_FILE, index=False)

    print(f"N_JOBS={N_JOBS}; no parallel processing required")
    print(summary.to_string(index=False))
    print("\nFamily-size distribution:")
    print(
        families.groupby("intervention")["evidence_units"]
        .describe()[["count", "mean", "50%", "max"]]
        .to_string()
    )
    print(f"\nSaved pair ledger: {LEDGER_FILE}")
    print(f"Saved evidence units: {EVIDENCE_FILE}")
    print(f"Saved dependence families: {FAMILY_FILE}")
    print(f"Saved summary: {SUMMARY_FILE}")
    print("Adsorption outcomes were not used. No missing values were filled.")


if __name__ == "__main__":
    main()

