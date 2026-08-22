#!/usr/bin/env python3
"""Create an outcome-transparent shortlist of structure-resolved Project 7 cases.

This is the second and final raw-results task. It does not choose visually
attractive structures or redefine the scientific claims. It applies fixed,
auditable criteria to produce ranked shortlists for:

1. strong linker contrast with process alignment;
2. strong coordination-compatible metal contrast with process alignment;
3. Cu-Zn pressure exception;
4. near-null matched comparison;
5. process-discordant comparison;
6. functional-motif example.

The script produces shortlists rather than silently declaring one final figure
case. Final case choice may use chemical interpretability and visual clarity,
but must be made from these recorded shortlists and documented.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import platform
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"

PAIRS = ANALYSIS / "final_primary_pairs.parquet"
ADSORPTION = ANALYSIS / "final_primary_pair_effect_magnitudes.parquet"
PROCESS = ANALYSIS / "process_translation_pair_results_final.parquet"
CIF_QUALITY = ANALYSIS / "step4_cif_quality_for_primary_pairs.csv"

SHORTLIST_OUTPUT = ANALYSIS / "final_structure_case_shortlist.csv"
PAIR_SUMMARY_OUTPUT = ANALYSIS / "final_structure_case_pair_summary.parquet"
SELECTION_OUTPUT = ANALYSIS / "final_structure_case_selection_summary.csv"
MANIFEST_OUTPUT = ANALYSIS / "final_structure_case_selection_manifest.json"
UNAVAILABLE_OUTPUT = ANALYSIS / "final_structure_case_pairs_without_adsorption_summary.csv"

N_JOBS = 1
TOP_N_PER_CATEGORY = 8

CATEGORIES = [
    "strong_linker_process_aligned",
    "strong_metal_process_aligned",
    "cu_zn_pressure_exception",
    "near_null_comparison",
    "process_discordant_comparison",
    "functional_motif_example",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_id(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"(?i)\.cif$", "", regex=True)
        .str.replace(r"(?i)_repeat$", "", regex=True)
    )


def pair_key(frame: pd.DataFrame) -> pd.Series:
    lo = frame[["id_a", "id_b"]].min(axis=1).astype("string")
    hi = frame[["id_a", "id_b"]].max(axis=1).astype("string")
    return lo + " || " + hi


def normalize_transition(value) -> str:
    text = (
        str(value)
        .replace("â†”", "<->")
        .replace("&lt;-&gt;", "<->")
        .replace("↔", "<->")
    )

    pieces = [piece.strip() for piece in text.split("<->")]

    if len(pieces) != 2:
        return text.strip()

    return " <-> ".join(sorted(pieces))


def robust_rank(series: pd.Series, ascending: bool) -> pd.Series:
    return series.rank(method="average", pct=True, ascending=ascending)


def load_cif_quality() -> pd.DataFrame:
    if not CIF_QUALITY.exists():
        return pd.DataFrame(columns=["mof_id", "strict_decode_ok", "disordered_sites"])
    quality = pd.read_csv(CIF_QUALITY, low_memory=False)
    id_col = next((c for c in ["mof_id", "filename", "id"] if c in quality.columns), None)
    if id_col is None:
        return pd.DataFrame(columns=["mof_id", "strict_decode_ok", "disordered_sites"])
    quality["mof_id"] = canonical_id(quality[id_col])
    decode_col = next((c for c in quality.columns if "decode" in c.lower() and "fail" not in c.lower()), None)
    disorder_col = next((c for c in quality.columns if "disorder" in c.lower()), None)
    out = quality[["mof_id"]].drop_duplicates().copy()
    if decode_col:
        mapping = quality.drop_duplicates("mof_id").set_index("mof_id")[decode_col]
        out["strict_decode_ok"] = out["mof_id"].map(mapping)
    else:
        out["strict_decode_ok"] = pd.NA
    if disorder_col:
        mapping = quality.drop_duplicates("mof_id").set_index("mof_id")[disorder_col]
        out["disordered_sites"] = pd.to_numeric(out["mof_id"].map(mapping), errors="coerce")
    else:
        out["disordered_sites"] = pd.NA
    return out


def main() -> None:
    for path in [PAIRS, ADSORPTION, PROCESS]:
        if not path.exists():
            raise FileNotFoundError(path)

    pairs = pd.read_parquet(PAIRS)
    pairs["id_a"] = canonical_id(pairs["id_a"])
    pairs["id_b"] = canonical_id(pairs["id_b"])
    if "pair_key" not in pairs.columns:
        pairs["pair_key"] = pair_key(pairs)
    if "transition" in pairs.columns:
        pairs["transition"] = pairs["transition"].map(normalize_transition)
    else:
        pairs["transition"] = pd.NA

    adsorption = pd.read_parquet(ADSORPTION)
    if "pair_key" not in adsorption.columns:
        if {"id_a", "id_b"}.issubset(adsorption.columns):
            adsorption["id_a"] = canonical_id(adsorption["id_a"])
            adsorption["id_b"] = canonical_id(adsorption["id_b"])
            adsorption["pair_key"] = pair_key(adsorption)
        else:
            raise ValueError("Adsorption effects lack pair identifiers")

    required_ads = {
        "pair_key",
        "absolute_log_difference",
        "standardized_absolute_difference",
    }
    missing = sorted(required_ads - set(adsorption.columns))
    if missing:
        raise ValueError(f"Adsorption effect table lacks columns: {missing}")

    ads_summary = (
        adsorption.groupby("pair_key", as_index=False)
        .agg(
            median_absolute_log_difference=(
                "absolute_log_difference",
                "median",
            ),
            maximum_absolute_log_difference=(
                "absolute_log_difference",
                "max",
            ),
            median_standardized_difference=(
                "standardized_absolute_difference",
                "median",
            ),
            maximum_standardized_difference=(
                "standardized_absolute_difference",
                "max",
            ),
            adsorption_conditions=(
                "absolute_log_difference",
                "count",
            ),
        )
    )

    pressure_rows = []

    for keys, group in adsorption.groupby(
        ["pair_key", "target", "T/K"],
        sort=False,
        dropna=False,
    ):
        pair_key_value, target, temperature = keys

        group = group.loc[
            group["standardized_absolute_difference"].notna()
        ].sort_values("p/bar")

        if len(group) != 2:
            continue

        low = group.iloc[0]
        high = group.iloc[1]

        pressure_rows.append(
            {
                "pair_key": pair_key_value,
                "target": target,
                "T/K": temperature,
                "standardized_pressure_change": (
                    high["standardized_absolute_difference"]
                    - low["standardized_absolute_difference"]
                ),
            }
        )

    pair_pressure = pd.DataFrame(pressure_rows)

    if pair_pressure.empty:
        raise RuntimeError(
            "No pair-level low-to-high-pressure comparisons "
            "could be constructed"
        )

    pressure_summary = (
        pair_pressure.groupby("pair_key", as_index=False)
        .agg(
            pressure_comparisons=(
                "standardized_pressure_change",
                "size",
            ),
            standardized_pressure_increases=(
                "standardized_pressure_change",
                lambda values: int((values > 0).sum()),
            ),
            standardized_pressure_decreases=(
                "standardized_pressure_change",
                lambda values: int((values < 0).sum()),
            ),
            median_standardized_pressure_change=(
                "standardized_pressure_change",
                "median",
            ),
            maximum_standardized_pressure_increase=(
                "standardized_pressure_change",
                "max",
            ),
        )
    )

    process = pd.read_parquet(PROCESS)
    if "pair_key" not in process.columns:
        raise ValueError("Final process pair results lack pair_key")

    process_summary = (
        process.groupby("pair_key", as_index=False)
        .agg(
            median_wc_oriented=("working_capacity_change_oriented_by_uptake", "median"),
            minimum_wc_oriented=("working_capacity_change_oriented_by_uptake", "min"),
            mean_wc_concordance=("uptake_working_capacity_concordant", "mean"),
            median_selectivity_oriented=("selectivity_change_oriented_by_uptake", "median"),
            minimum_selectivity_oriented=("selectivity_change_oriented_by_uptake", "min"),
            mean_selectivity_concordance=("uptake_selectivity_concordant", "mean"),
            valid_process_working_capacity=("working_capacity_change_oriented_by_uptake", "count"),
            valid_process_selectivity=("selectivity_change_oriented_by_uptake", "count"),
        )
    )

    merged = (
        pairs.merge(
            ads_summary,
            on="pair_key",
            how="left",
            validate="one_to_one",
        )
        .merge(
            pressure_summary,
            on="pair_key",
            how="left",
            validate="one_to_one",
        )
        .merge(
            process_summary,
            on="pair_key",
            how="left",
            validate="one_to_one",
        )
    )

    unavailable = merged.loc[
        merged["median_absolute_log_difference"].isna()
    ].copy()
    unavailable_columns = [
        column for column in [
            "pair_key",
            "id_a",
            "id_b",
            "intervention",
            "transition",
            "topology",
        ]
        if column in unavailable.columns
    ]
    unavailable[unavailable_columns].to_csv(UNAVAILABLE_OUTPUT, index=False)

    # A structure-resolved case requires an observed adsorption summary. Pairs
    # absent from the earlier effect file remain in the frozen scientific
    # catalogue, are written to an explicit ledger, and are excluded only from
    # case-study ranking. No scientific result or cohort count is changed.
    merged["case_ranking_eligible"] = merged[
        "median_absolute_log_difference"
    ].notna()
    ranking = merged.loc[merged["case_ranking_eligible"]].copy()

    if ranking.empty:
        raise RuntimeError("No frozen pair has an adsorption summary for case ranking")

    # Restrict only the case-ranking table to pairs with observed adsorption
    # summaries. The full frozen pair ledger remains preserved separately.
    merged = ranking.copy()

    # Normalize process columns explicitly to numeric dtype. This removes the
    # pandas object-downcasting warnings without changing missing-data handling.
    for column in [
        "mean_wc_concordance",
        "mean_selectivity_concordance",
        "minimum_wc_oriented",
        "minimum_selectivity_oriented",
    ]:
        merged[column] = pd.to_numeric(merged[column], errors="coerce")

    # Outcome-transparent summary scores. These are used only to rank within
    # predeclared categories, not to change the scientific cohort.
    merged["adsorption_strength_percentile"] = robust_rank(
        merged["median_absolute_log_difference"], ascending=True
    )
    merged["adsorption_null_percentile"] = robust_rank(
        merged["median_absolute_log_difference"], ascending=False
    )

    wc_concordance = merged["mean_wc_concordance"].fillna(0.0)
    selectivity_concordance = merged["mean_selectivity_concordance"].where(
        merged["mean_selectivity_concordance"].notna(), wc_concordance
    )
    merged["process_alignment_score"] = (
        wc_concordance + selectivity_concordance
    ) / 2.0

    merged["process_discordance_score"] = (
        (1.0 - merged["mean_wc_concordance"].fillna(1.0))
        + (1.0 - merged["mean_selectivity_concordance"].fillna(1.0))
        + merged["minimum_wc_oriented"].lt(0).astype(float)
        + merged["minimum_selectivity_oriented"].lt(0).astype(float)
    )

    quality = load_cif_quality()
    if not quality.empty:
        qa = quality.add_suffix("_a").rename(columns={"mof_id_a": "id_a"})
        qb = quality.add_suffix("_b").rename(columns={"mof_id_b": "id_b"})
        merged = merged.merge(qa, on="id_a", how="left", validate="many_to_one")
        merged = merged.merge(qb, on="id_b", how="left", validate="many_to_one")

    # The eligible pair summary, including ranking scores, is written below.
    merged.to_parquet(PAIR_SUMMARY_OUTPUT, index=False)

    shortlists = []

    def add_category(category, frame, score, ascending=False, rationale=""):
        selected = frame.sort_values(
            [score, "pair_key"], ascending=[ascending, True], kind="mergesort"
        ).head(TOP_N_PER_CATEGORY).copy()
        selected["selection_category"] = category
        selected["selection_score"] = selected[score]
        selected["selection_rationale"] = rationale
        selected["rank_within_category"] = np.arange(1, len(selected) + 1)
        shortlists.append(selected)

    linker = merged.loc[merged["intervention"].eq("linker_family_change")].copy()
    linker["strong_aligned_score"] = (
        linker["adsorption_strength_percentile"]
        + linker["process_alignment_score"]
    )
    add_category(
        "strong_linker_process_aligned",
        linker,
        "strong_aligned_score",
        ascending=False,
        rationale="Large cross-condition adsorption separation with aligned working-capacity and selectivity behavior.",
    )

    metal = merged.loc[merged["intervention"].eq("metal_substitution")].copy()
    metal["strong_aligned_score"] = (
        metal["adsorption_strength_percentile"]
        + metal["process_alignment_score"]
    )
    add_category(
        "strong_metal_process_aligned",
        metal,
        "strong_aligned_score",
        ascending=False,
        rationale="Large adsorption separation in a coordination-compatible metal pair with aligned process behavior.",
    )

    cuzn = metal.loc[
        metal["transition"].eq("Cu <-> Zn")
        & metal["pressure_comparisons"].eq(9)
        & metal["standardized_pressure_increases"].gt(0)
    ].copy()

    if cuzn.empty:
        raise RuntimeError(
            "No Cu-Zn pair has nine complete pressure comparisons "
            "and an increasing standardized pressure contrast"
        )

    cuzn["cu_zn_exception_score"] = (
        cuzn["standardized_pressure_increases"].rank(
            method="average",
            pct=True,
        )
        + cuzn["median_standardized_pressure_change"].rank(
            method="average",
            pct=True,
        )
        + cuzn["process_alignment_score"]
    )

    add_category(
        "cu_zn_pressure_exception",
        cuzn,
        "cu_zn_exception_score",
        ascending=False,
        rationale=(
            "Cu-Zn pair whose standardized adsorption separation "
            "increases from low to high pressure, with retained "
            "process support."
        ),
    )

    eligible_null = merged.loc[
        merged["intervention"].isin(["linker_family_change", "metal_substitution"])
        & merged["valid_process_working_capacity"].ge(4)
    ].copy()
    add_category(
        "near_null_comparison",
        eligible_null,
        "median_absolute_log_difference",
        ascending=True,
        rationale="Geometry-matched chemistry change with minimal adsorption separation across evaluated conditions.",
    )

    discordant = merged.loc[
        merged["intervention"].isin(["linker_family_change", "metal_substitution"])
        & (
            merged["minimum_wc_oriented"].lt(0)
            | merged["minimum_selectivity_oriented"].lt(0)
            | merged["mean_wc_concordance"].lt(0.5)
            | merged["mean_selectivity_concordance"].lt(0.5)
        )
    ].copy()
    add_category(
        "process_discordant_comparison",
        discordant,
        "process_discordance_score",
        ascending=False,
        rationale="Higher uptake fails to align with working capacity or selectivity in at least one process condition.",
    )

    functional = merged.loc[
        merged["intervention"].eq("functional_motif_change")
    ].copy()
    functional["functional_example_score"] = (
        functional["adsorption_strength_percentile"]
        + functional["process_alignment_score"]
    )
    add_category(
        "functional_motif_example",
        functional,
        "functional_example_score",
        ascending=False,
        rationale="Individual functional-motif example; not evidence for a class-level functional claim.",
    )

    shortlist = pd.concat(shortlists, ignore_index=True, sort=False)
    keep_columns = [
        "selection_category",
        "rank_within_category",
        "selection_score",
        "selection_rationale",
        "pair_key",
        "id_a",
        "id_b",
        "intervention",
        "transition",
        "median_absolute_log_difference",
        "maximum_absolute_log_difference",
        "median_standardized_difference",
        "maximum_standardized_difference",
        "median_wc_oriented",
        "minimum_wc_oriented",
        "mean_wc_concordance",
        "median_selectivity_oriented",
        "minimum_selectivity_oriented",
        "mean_selectivity_concordance",
        "valid_process_working_capacity",
        "valid_process_selectivity",
    ]
    for optional in [
        "topology",
        "dimensionality",
        "metals_a",
        "metals_b",
        "linker_cluster_a",
        "linker_cluster_b",
        "functional_cluster_a",
        "functional_cluster_b",
        "covariance_distance",
    ]:
        if optional in shortlist.columns:
            keep_columns.append(optional)
    shortlist[keep_columns].to_csv(SHORTLIST_OUTPUT, index=False)

    selection_summary = (
        shortlist.groupby("selection_category", as_index=False)
        .agg(
            candidates=("pair_key", "size"),
            interventions=("intervention", lambda x: " | ".join(sorted(set(map(str, x))))),
            transitions=("transition", lambda x: " | ".join(sorted(set(x.dropna().astype(str))))),
            median_adsorption_separation=("median_absolute_log_difference", "median"),
            median_wc_alignment=("mean_wc_concordance", "median"),
            median_selectivity_alignment=("mean_selectivity_concordance", "median"),
        )
    )
    selection_summary.to_csv(SELECTION_OUTPUT, index=False)

    manifest = {
        "stage": "Structure-resolved case shortlist",
        "purpose": "Second and final raw-results task before production",
        "pair_input": str(PAIRS),
        "pair_input_sha256": sha256(PAIRS),
        "adsorption_input": str(ADSORPTION),
        "adsorption_input_sha256": sha256(ADSORPTION),
        "process_input": str(PROCESS),
        "process_input_sha256": sha256(PROCESS),
        "categories": CATEGORIES,
        "top_n_per_category": TOP_N_PER_CATEGORY,
        "frozen_primary_pairs": int(len(pairs)),
        "case_ranking_eligible_pairs": int(len(ranking)),
        "pairs_without_adsorption_summary": int(len(unavailable)),
        "n_jobs": N_JOBS,
        "pair_selection_changed": False,
        "chemistry_direction_assigned": False,
        "visual_appearance_used": False,
        "missing_values_filled": False,
        "predictive_model_fitted": False,
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
    }
    MANIFEST_OUTPUT.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

    print(
        f"N_JOBS={N_JOBS}; vectorized ranking; parallel processing would not help"
    )
    print()
    print("CASE-RANKING COVERAGE")
    print(f"frozen_primary_pairs={len(pairs):,}")
    print(f"case_ranking_eligible_pairs={len(ranking):,}")
    print(f"pairs_without_adsorption_summary={len(unavailable):,}")
    if len(unavailable):
        print("Unavailable pairs by intervention:")
        print(
            unavailable["intervention"]
            .value_counts(dropna=False)
            .rename_axis("intervention")
            .reset_index(name="pairs")
            .to_string(index=False)
        )

    print()
    print("STRUCTURE CASE SHORTLIST SUMMARY")
    print(selection_summary.to_string(index=False))
    print()
    print("TOP-RANKED CASE IN EACH CATEGORY")
    print(
        shortlist.loc[
            shortlist["rank_within_category"].eq(1),
            [
                "selection_category",
                "pair_key",
                "intervention",
                "transition",
                "median_absolute_log_difference",
                "mean_wc_concordance",
                "mean_selectivity_concordance",
            ],
        ].to_string(index=False)
    )
    print()
    print("Outputs:")
    for path in [
        SHORTLIST_OUTPUT,
        PAIR_SUMMARY_OUTPUT,
        SELECTION_OUTPUT,
        UNAVAILABLE_OUTPUT,
        MANIFEST_OUTPUT,
    ]:
        print(path)
    print(
        "No pair was added to or removed from the scientific cohort. Pairs "
        "without an adsorption summary were excluded only from case ranking "
        "and preserved in an explicit ledger. The output is an auditable "
        "shortlist, not a silent final case choice."
    )


if __name__ == "__main__":
    main()

