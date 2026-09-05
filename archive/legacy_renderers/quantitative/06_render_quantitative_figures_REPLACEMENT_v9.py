#!/usr/bin/env python3
"""Project 7B2 Step 3, file 06: render quantitative main figures.

Rendering-only replacement focused on visual cleanup.
Uses the same frozen packaged CSV sources and does not refit any scientific result.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "Step 3 results" / "figure_source_data"
OUT = ROOT / "Step 3 results" / "main_figures"
OUT.mkdir(parents=True, exist_ok=True)
DPI = 600

C = {
    "linker": "#8ECae6",       # light blue
    "metal": "#F6B6C8",        # light pink
    "functional": "#B8B8C8",   # soft grey-lilac
    "control": "#C9CDD6",
    "linker_dark": "#4F97BF",
    "metal_dark": "#D77FA1",
    "functional_dark": "#7E7D90",
    "navy": "#496A81",
    "text": "#27313A",
    "muted": "#6B7480",
    "grid": "#E7EBF0",
    "green": "#5E9C76",
    "red": "#C36B6B",
    "soft_box": "#F6F7FA",
    "border": "#C8CFD8",
}

ILAB = {
    "linker_family_change": "Linker family",
    "metal_substitution": "Metal substitution",
    "functional_motif_change": "Functional motif",
}
ICOL = {
    "linker_family_change": C["linker"],
    "metal_substitution": C["metal"],
    "functional_motif_change": C["functional"],
}
IDARK = {
    "linker_family_change": C["linker_dark"],
    "metal_substitution": C["metal_dark"],
    "functional_motif_change": C["functional_dark"],
}
TLAB = {
    "landfill_CH4": "Landfill CH$_4$",
    "landfill_CO2": "Landfill CO$_2$",
    "methane_purification_CH4": "Purification CH$_4$",
    "methane_purification_CO2": "Purification CO$_2$",
    "methane_storage_CH4": "Storage CH$_4$",
    "post_combustion_CO2": "Post-comb. CO$_2$",
    "post_combustion_N2": "Post-comb. N$_2$",
    "pre_combustion_CO2": "Pre-comb. CO$_2$",
    "pre_combustion_H2": "Pre-comb. H$_2$",
}
COMPARE_LAB = {
    "landfill_CO2_vs_CH4": "Landfill CO$_2$ vs CH$_4$",
    "methane_purification_CO2_vs_CH4": "Purification CO$_2$ vs CH$_4$",
    "post_combustion_CO2_vs_N2": "Post-comb. CO$_2$ vs N$_2$",
    "pre_combustion_CO2_vs_H2": "Pre-comb. CO$_2$ vs H$_2$",
}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def load(fig, name):
    expected_name = f"04_{name}"
    matches = sorted(p for p in SRC.glob("Figure_*/" + expected_name) if p.is_file())
    if not matches:
        available = sorted(p.name for p in SRC.glob("Figure_*/*") if p.is_file())
        raise FileNotFoundError(
            f"Packaged source not found anywhere: {expected_name}. "
            f"Available packaged files: {available}"
        )
    if len(matches) > 1:
        hashes = {sha(p) for p in matches}
        if len(hashes) != 1:
            raise RuntimeError(
                f"Conflicting packaged copies for {expected_name}: "
                + ", ".join(str(p) for p in matches)
            )
    source = matches[0]
    if source.suffix.lower() != ".csv":
        raise ValueError(f"Unsupported quantitative source type: {source}")
    return pd.read_csv(source, low_memory=False), source


def require(df, cols, name):
    miss = set(cols) - set(df.columns)
    if miss:
        raise RuntimeError(f"{name} missing columns: {sorted(miss)}; available={list(df.columns)}")


def style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "font.size": 8.8,
        "font.weight": "bold",
        "axes.labelweight": "bold",
        "axes.titlesize": 9.7,
        "axes.labelsize": 8.6,
        "xtick.labelsize": 7.6,
        "ytick.labelsize": 7.6,
        "legend.fontsize": 7.4,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": C["border"],
        "axes.linewidth": 0.8,
        "text.color": C["text"],
        "axes.labelcolor": C["text"],
        "xtick.color": C["text"],
        "ytick.color": C["text"],
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
    })


def panel(ax, letter, title=None, grid=True, y=1.11):
    ax.text(-0.12, y, letter.upper(), transform=ax.transAxes,
            fontweight="bold", fontsize=17.3, va="top")
    if title:
        ax.set_title(title, loc="left", fontweight="bold", pad=7)
    if grid:
        ax.grid(axis="y", color=C["grid"], lw=0.6, alpha=0.8)
        ax.set_axisbelow(True)


def point_intervals(ax, x, lo, hi, y, colors, ms=4.2, alpha=1.0, zorder=3):
    for xi, li, hi_i, yi, ci in zip(x, lo, hi, y, colors):
        if not all(np.isfinite([xi, li, hi_i])):
            continue
        ax.errorbar(
            float(xi), float(yi),
            xerr=[[float(xi - li)], [float(hi_i - xi)]],
            fmt="o", color=ci, ecolor=ci, capsize=2.2, ms=ms,
            alpha=alpha, lw=0.9, zorder=zorder,
        )


def add_top_legend(ax, handles, ncol=2, y=1.12):
    return ax.legend(handles=handles, frameon=False, ncol=ncol,
                     loc="lower center", bbox_to_anchor=(0.5, y),
                     handletextpad=0.6, columnspacing=1.2)


def finish(fig, n):
    paths = []
    for ext in ["pdf", "svg", "png"]:
        p = OUT / f"Figure_{n:02d}.{ext}"
        fig.savefig(p, dpi=DPI if ext == "png" else None, bbox_inches="tight")
        paths.append(str(p))
    plt.close(fig)
    return paths


def figure1():
    counts, p1 = load(1, "final_primary_pair_counts.csv")
    cal, p2 = load(1, "caliper_sensitivity_support.csv")
    require(counts, ["intervention", "raw_pairs"], "pair counts")
    require(cal, ["tier", "tier_order", "intervention", "raw_pairs", "related_groups"], "caliper support")
    primary = cal[cal.tier.eq("primary")][["intervention", "related_groups"]]
    counts = counts.merge(primary, on="intervention", how="left", validate="one_to_one")

    fig, axs = plt.subplots(2, 2, figsize=(10.7, 7.6))
    a, b, c, d = axs.ravel()

    panel(a, "A", None, False)
    a.axis("off")
    # Panel A enlarged for readability: box dimensions and text are ~1.3x
    # the prior production version while preserving the same workflow.
    vertical_boxes = [
        (0.175, 0.700, 0.650, 0.182, "Chemistry Changes", C["linker"], C["linker_dark"]),
        (0.175, 0.460, 0.650, 0.182, "Measured geometry constrained", C["control"], C["border"]),
        (0.175, 0.220, 0.650, 0.182, "Adsorption and HOA contrasts", C["metal"], C["metal_dark"]),
    ]
    for x0, y0, w0, h0, txt, face, edge in vertical_boxes:
        a.add_patch(FancyBboxPatch((x0, y0), w0, h0,
                                   boxstyle="round,pad=0.03,rounding_size=0.03",
                                   linewidth=1.0, edgecolor=edge,
                                   facecolor=face, alpha=0.35))
        a.text(x0 + w0 / 2, y0 + h0 / 2, txt, ha="center", va="center", fontweight="bold", fontsize=13.52)
    a.annotate("", xy=(0.50, 0.655), xytext=(0.50, 0.695), arrowprops=dict(arrowstyle="-|>", lw=1.35, color=C["muted"]))
    a.annotate("", xy=(0.50, 0.415), xytext=(0.50, 0.455), arrowprops=dict(arrowstyle="-|>", lw=1.35, color=C["muted"]))
    a.annotate("", xy=(0.50, 0.188), xytext=(0.50, 0.215), arrowprops=dict(arrowstyle="-|>", lw=1.35, color=C["muted"]))
    a.add_patch(FancyBboxPatch((0.03, 0.00), 0.94, 0.18,
                               boxstyle="round,pad=0.03,rounding_size=0.03",
                               linewidth=0.9, edgecolor=C["border"],
                               facecolor=C["soft_box"]))
    a.text(0.50, 0.09,
           "Exact topology and dimensionality\nSeven measured geometry controls",
           ha="center", va="center", fontsize=12.48, linespacing=1.18)

    panel(b, "B", None)
    x = np.arange(len(counts))
    cols = [ICOL[i] for i in counts.intervention]
    b.bar(x, counts.raw_pairs, color=cols, width=0.36, edgecolor=[IDARK[i] for i in counts.intervention], linewidth=0.7)
    b.set_yscale("symlog", linthresh=10)
    b.set_ylabel("Pairs", fontsize=12.9)
    b.set_xticks(x, [ILAB[i] for i in counts.intervention], rotation=20, ha="right")
    for i, v in enumerate(counts.raw_pairs):
        b.text(i, v, f"{int(v):,}", ha="center", va="bottom", fontsize=9.2)

    panel(c, "C", None)
    for inter, g in cal.sort_values("tier_order").groupby("intervention"):
        c.plot(g.tier_order, g.raw_pairs, "o-", lw=1.5, ms=4.2, color=IDARK[inter],
               markerfacecolor=ICOL[inter], label=ILAB[inter])
    ticks = cal[["tier_order", "tier"]].drop_duplicates().sort_values("tier_order")
    c.set_xticks(ticks.tier_order, [x.replace("_", " ").title() for x in ticks.tier], rotation=18)
    c.set_yscale("log")
    c.set_ylabel("Accepted pairs", fontsize=12.9)
    c.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.26), fontsize=11.1)

    panel(d, "D", None)
    y = np.arange(len(counts))
    d.barh(y + 0.15, counts.raw_pairs, height=0.24, color=C["control"], edgecolor=C["border"], label="Raw pairs")
    d.barh(y - 0.15, counts.related_groups, height=0.24, color=C["navy"], edgecolor=C["navy"], label="Related groups")
    d.set_yticks(y, [ILAB[i] for i in counts.intervention])
    d.set_xscale("log")
    d.set_xlabel("Count", fontsize=12.9)
    d.legend(frameon=False, ncol=1, loc="lower right", fontsize=11.1)

    for ax in [b, c, d]:
        ax.xaxis.label.set_size(12.9)
        ax.yaxis.label.set_size(12.9)
        for lab in ax.get_xticklabels() + ax.get_yticklabels():
            lab.set_fontsize(11.4)
        leg = ax.get_legend()
        if leg is not None:
            for t in leg.get_texts():
                t.set_fontsize(11.1)

    fig.subplots_adjust(left=0.09, right=0.985, bottom=0.12, top=0.95, wspace=0.39, hspace=0.64)
    return fig, [p1, p2]


def _short_condition_labels(df):
    return df.target.map(TLAB).fillna(df.target) + " | " + df["p/bar"].astype(str) + " bar"


def figure2():
    sym, p1 = load(2, "step5b_symmetric_control_results.csv")
    heat, p2 = load(2, "heat_adsorption_condition_results.csv")
    adj, p3 = load(2, "03_results.csv")
    require(sym, ["intervention", "effect_measure", "target", "p/bar", "median_chemistry_minus_control", "bootstrap_95_low", "bootstrap_95_high"], "symmetric controls")
    require(heat, ["intervention", "effect_measure", "p/bar", "spearman_rho_heat_vs_adsorption_separation", "bootstrap_95_low_rho", "bootstrap_95_high_rho"], "heat associations")
    require(adj, ["target", "p/bar", "effect_measure", "unadjusted_linker_minus_control", "adjusted_linker_minus_control", "adjusted_bootstrap_95_low", "adjusted_bootstrap_95_high"], "adjustment")

    fig, axs = plt.subplots(2, 2, figsize=(11.2, 7.8), gridspec_kw={"width_ratios": [1.12, 1.0]})
    a, b, c, d = axs.ravel()
    panel(a, "A", None, y=1.16)
    panel(b, "B", None, y=1.16)
    panel(c, "C", None, y=1.16)
    panel(d, "D", None, y=1.16)

    for ax, inter in [(a, "linker_family_change"), (b, "metal_substitution")]:
        g = sym[(sym.intervention == inter) & (sym.effect_measure == "absolute_log_difference")].sort_values(["target", "p/bar"]).copy()
        y = np.arange(len(g))
        labels = _short_condition_labels(g)
        point_intervals(ax, g.median_chemistry_minus_control, g.bootstrap_95_low, g.bootstrap_95_high, y, [IDARK[inter]] * len(g), ms=3.8)
        ax.axvline(0, color=C["muted"], lw=0.8)
        ax.set_yticks(y, labels)
        ax.invert_yaxis()
        ax.set_xlabel("Chemistry minus control |Δlog q|", fontsize=12.9)
        ax.text(0.01, 1.03, ILAB[inter], transform=ax.transAxes, fontweight="bold", color=IDARK[inter], fontsize=10.6)
        ax.tick_params(axis='x', labelsize=10.6)
    a.set_xlim(0.0, 0.075)

    h = heat[heat.effect_measure.eq("absolute_log_difference")].copy()
    for inter, mark, size in [("linker_family_change", "o", 34), ("metal_substitution", "s", 34)]:
        g = h[h.intervention.eq(inter)]
        c.scatter(g.spearman_rho_heat_vs_adsorption_separation, g["p/bar"], s=size,
                  marker=mark, color=ICOL[inter], edgecolor=IDARK[inter], lw=0.7, label=ILAB[inter], zorder=3)
    c.axvline(0, color=C["muted"], lw=0.8)
    c.set_yscale("log")
    c.set_xlabel("Spearman ρ: |ΔHOA| vs |Δlog q|", fontsize=12.9)
    c.set_ylabel("Pressure / bar", fontsize=12.9)
    c.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.22), fontsize=11.1)
    c.tick_params(axis='x', labelsize=10.6)
    c.tick_params(axis='y', labelsize=10.6)

    g = adj[adj.effect_measure.eq("absolute_log_difference")].sort_values(["target", "p/bar"]).copy()
    y = np.arange(len(g))
    labels = _short_condition_labels(g)
    d.scatter(g.unadjusted_linker_minus_control, y, color=C["control"], edgecolor=C["border"], s=22, zorder=2)
    point_intervals(d, g.adjusted_linker_minus_control, g.adjusted_bootstrap_95_low, g.adjusted_bootstrap_95_high, y, [IDARK["linker_family_change"]] * len(g), ms=4.0, zorder=3)
    for yi, u, v in zip(y, g.unadjusted_linker_minus_control, g.adjusted_linker_minus_control):
        d.plot([u, v], [yi, yi], color="#B9C2CB", lw=0.8, zorder=1)
    d.axvline(0, color=C["muted"], lw=0.8)
    d.set_yticks(y, labels)
    d.invert_yaxis()
    d.set_xlabel("Linker minus control |Δlog q|", fontsize=12.9)
    d.legend(handles=[
        Line2D([0], [0], marker='o', color='none', markerfacecolor=C["control"], markeredgecolor=C["border"], markersize=5, label='Unadjusted'),
        Line2D([0], [0], marker='o', color=IDARK["linker_family_change"], markerfacecolor=IDARK["linker_family_change"], markersize=5, label='Adjusted')
    ], frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.22), fontsize=11.1)
    d.tick_params(axis='x', labelsize=10.6)

    fig.subplots_adjust(left=0.13, right=0.99, bottom=0.11, top=0.94, wspace=0.42, hspace=0.61)
    return fig, [p1, p2, p3]


def figure3():
    pr, p1 = load(3, "heat_adsorption_pressure_results.csv")
    guest, p2 = load(3, "05_results.csv")
    require(pr, ["intervention", "target", "effect_measure", "median_heat_low", "median_heat_high", "median_adsorption_low", "median_adsorption_high"], "pressure results")
    require(guest, ["quantity", "intervention", "comparison", "regime", "measure", "median_paired_difference_CO2_minus_coguest", "median_bootstrap_95_low", "median_bootstrap_95_high"], "guest results")

    fig, axs = plt.subplots(2, 2, figsize=(10.8, 7.6), gridspec_kw={"width_ratios": [1.1, 1.0]})
    a, b, c, d = axs.ravel()
    panel(a, "A", None, y=1.16)
    panel(b, "B", None, y=1.16)
    panel(c, "C", None, y=1.16)
    panel(d, "D", None, y=1.16)

    g = pr[(pr.intervention == "linker_family_change") & (pr.effect_measure == "absolute_log_difference")].sort_values("target")
    y = np.arange(len(g))
    ylab = [TLAB.get(x, x) for x in g.target]
    for ax, lo, hi, xlab in [
        (a, "median_adsorption_low", "median_adsorption_high", "Median |Δlog q|"),
        (b, "median_heat_low", "median_heat_high", "Median |ΔHOA| / kcal mol$^{-1}$"),
    ]:
        for yi, (_, r) in enumerate(g.iterrows()):
            ax.plot([r[lo], r[hi]], [yi, yi], color="#C4CBD4", lw=1.0, zorder=1)
            ax.scatter(r[lo], yi, color=C["linker"], edgecolor=C["linker_dark"], s=28, label="Low" if yi == 0 else None, zorder=2)
            ax.scatter(r[hi], yi, color=C["metal"], edgecolor=C["metal_dark"], s=28, label="High" if yi == 0 else None, zorder=2)
        ax.set_yticks(y, ylab)
        ax.invert_yaxis()
        ax.set_xlabel(xlab, fontsize=12.9)
        ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.18), fontsize=11.1)
        ax.tick_params(axis='x', labelsize=11.4)

    gg = guest[(guest.quantity == "adsorption_separation") & (guest.measure == "absolute_log_difference")].copy()
    comp_order = ["landfill_CO2_vs_CH4", "methane_purification_CO2_vs_CH4", "post_combustion_CO2_vs_N2", "pre_combustion_CO2_vs_H2"]
    reg_order = ["low", "high"]
    rows = [(comp, reg) for comp in comp_order for reg in reg_order]
    y_positions = np.arange(len(rows))
    y_map = {row: i for i, row in enumerate(rows)}
    labels = [f"{COMPARE_LAB.get(comp, comp)} | {reg}" for comp, reg in rows]

    for inter, offset in [("linker_family_change", -0.10), ("metal_substitution", 0.10)]:
        sub = gg[gg.intervention.eq(inter)].copy()
        yv = [y_map[(r.comparison, r.regime)] + offset for r in sub.itertuples()]
        point_intervals(c, sub.median_paired_difference_CO2_minus_coguest,
                        sub.median_bootstrap_95_low, sub.median_bootstrap_95_high,
                        yv, [IDARK[inter]] * len(sub), ms=3.7)
    c.axvline(0, color=C["muted"], lw=0.8)
    c.set_yticks(y_positions, labels)
    c.invert_yaxis()
    c.set_xlabel("CO$_2$ minus co-guest |Δlog q|", fontsize=12.9)
    c.legend(handles=[
        Line2D([0], [0], marker='o', color=IDARK["linker_family_change"], markerfacecolor=IDARK["linker_family_change"], markersize=5, label='Linker family'),
        Line2D([0], [0], marker='o', color=IDARK["metal_substitution"], markerfacecolor=IDARK["metal_substitution"], markersize=5, label='Metal substitution'),
    ], frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.20), fontsize=11.1)
    c.tick_params(axis='x', labelsize=11.4)

    bd = guest[(guest.comparison == "pre_combustion_CO2_vs_H2") & (guest.regime == "high")].copy()
    order = []
    for inter in ["linker_family_change", "metal_substitution"]:
        sub = bd[bd.intervention.eq(inter)]
        for quantity in ["adsorption_separation", "heat_contrast"]:
            q = sub[sub.quantity.eq(quantity)]
            if not q.empty:
                order.append(q.iloc[0])
    bdd = pd.DataFrame(order)
    y = np.arange(len(bdd))
    vals = bdd.median_paired_difference_CO2_minus_coguest.values
    los = bdd.median_bootstrap_95_low.values
    his = bdd.median_bootstrap_95_high.values
    cols = [C["red"] if v < 0 else C["green"] for v in vals]
    labs = [f"{ILAB[i]} | {'Adsorption' if q == 'adsorption_separation' else 'HOA'}" for i, q in zip(bdd.intervention, bdd.quantity)]
    point_intervals(d, vals, los, his, y, cols, ms=4.0)
    d.axvline(0, color=C["muted"], lw=0.8)
    d.set_yticks(y, labs)
    d.invert_yaxis()
    d.set_xlabel("CO$_2$ minus H$_2$", fontsize=12.9)
    d.text(0.02, 1.07, "Left: H$_2$ larger adsorption separation", transform=d.transAxes,
           ha="left", va="bottom", fontsize=7.3, color=C["red"], fontweight="bold")
    d.text(0.98, 1.07, "Right: CO$_2$ larger contrast", transform=d.transAxes,
           ha="right", va="bottom", fontsize=7.3, color=C["green"], fontweight="bold")
    d.tick_params(axis='x', labelsize=11.4)

    fig.subplots_adjust(left=0.14, right=0.99, bottom=0.12, top=0.95, wspace=0.44, hspace=0.66)
    return fig, [p1, p2]


def figure4():
    cal, p1 = load(4, "caliper_sensitivity_support.csv")
    res, p2 = load(4, "step2_residual_geometry_summary.csv")
    bal, p3 = load(4, "04_balance.csv")
    fam, p4 = load(4, "04_family_exclusion_summary.csv")
    require(cal, ["tier", "tier_order", "intervention", "raw_pairs"], "caliper")
    require(res, ["intervention", "effect_measure", "median_absolute_rho"], "residual")
    require(bal, ["intervention", "geometry_variable", "absolute_global_smd"], "balance")
    require(fam, ["intervention", "effect_measure", "median_abs_relative_change_excluding_largest", "median_abs_relative_change_excluding_top10"], "family")

    fig = plt.figure(figsize=(9.7, 8.2))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.0, 0.82])
    a = fig.add_subplot(gs[0, 0])
    b = fig.add_subplot(gs[0, 1])
    c = fig.add_subplot(gs[1, 0])
    d = fig.add_subplot(gs[1, 1])
    e = fig.add_subplot(gs[2, :])

    panel(a, "A", None, y=1.16)
    panel(b, "B", None, y=1.16)
    panel(c, "C", None, y=1.16)
    panel(d, "D", None, y=1.16)
    panel(e, "E", None, False)

    for inter, g in cal.sort_values("tier_order").groupby("intervention"):
        a.plot(g.tier_order, g.raw_pairs, "o-", color=IDARK[inter], markerfacecolor=ICOL[inter], ms=4.5, lw=1.5, label=ILAB[inter])
    ticks = cal[["tier_order", "tier"]].drop_duplicates().sort_values("tier_order")
    a.set_xticks(ticks.tier_order, [x.replace("_", " ").title() for x in ticks.tier], rotation=18)
    a.set_yscale("log")
    a.set_ylabel("Pairs", fontsize=12.0)

    rr = res[res.effect_measure.isin(["absolute_log_difference", "standardized_absolute_difference"])].copy()
    rr["measure_lab"] = rr.effect_measure.map({
        "absolute_log_difference": r"Absolute $\Delta \log q$",
        "standardized_absolute_difference": r"Standardized $\Delta q$",
    })
    rr = rr.sort_values(["intervention", "measure_lab"])
    y = np.arange(len(rr))
    b.barh(y, rr.median_absolute_rho,
           color=[ICOL[i] for i in rr.intervention],
           edgecolor=[IDARK[i] for i in rr.intervention], height=0.58)
    b.set_yticks(y, rr.measure_lab)
    b.invert_yaxis()
    b.set_xlabel("Median |Spearman ρ|", fontsize=12.0)
    b.legend(handles=[
        Patch(facecolor=C["linker"], edgecolor=C["linker_dark"], label="Linker family"),
        Patch(facecolor=C["metal"], edgecolor=C["metal_dark"], label="Metal substitution"),
        Patch(facecolor=C["functional"], edgecolor=C["functional_dark"], label="Functional motif"),
    ], frameon=False, ncol=1, loc="lower right")

    bb = bal[bal.intervention.isin(["linker_family_change", "metal_substitution"])]
    pv = bb.pivot(index="geometry_variable", columns="intervention", values="absolute_global_smd")
    pv = pv.loc[[i for i in ["AVAf_diff", "Density_diff", "Df_diff", "Di_diff", "Dif_diff", "POAVAf_diff", "UC_volume_diff"] if i in pv.index]]
    xx = np.arange(len(pv.index))
    width = 0.34
    c.bar(xx - width / 2, pv["linker_family_change"].values, width, color=C["linker"], edgecolor=C["linker_dark"], label="Linker family")
    c.bar(xx + width / 2, pv["metal_substitution"].values, width, color=C["metal"], edgecolor=C["metal_dark"], label="Metal substitution")
    c.axhline(.1, color=C["muted"], ls="--", lw=.8)
    c.set_ylabel("|Global SMD|", fontsize=12.0)
    c.set_xticks(xx, pv.index, rotation=32, ha="right")
    c.legend(frameon=False, ncol=1, loc="upper right")

    ff = fam.copy().sort_values(["intervention", "effect_measure"])
    x = np.arange(len(ff))
    short_ticks = [
        (r"Linker | $\Delta \log q$" if i == "linker_family_change" and m == "absolute_log_difference" else
         r"Linker | std. $\Delta q$" if i == "linker_family_change" else
         r"Metal | $\Delta \log q$" if m == "absolute_log_difference" else
         r"Metal | std. $\Delta q$")
        for i, m in zip(ff.intervention, ff.effect_measure)
    ]
    d.scatter(100 * ff.median_abs_relative_change_excluding_largest, x,
              color=C["control"], edgecolor=C["border"], s=34, label="Exclude largest group", zorder=3)
    d.scatter(100 * ff.median_abs_relative_change_excluding_top10, x,
              color=[IDARK[i] for i in ff.intervention], s=36, label="Exclude top 10 groups", zorder=3)
    for yi, u, v in zip(x, 100 * ff.median_abs_relative_change_excluding_largest, 100 * ff.median_abs_relative_change_excluding_top10):
        d.plot([u, v], [yi, yi], color="#C5CCD4", lw=0.8, zorder=2)
    d.set_yticks(x, short_ticks)
    d.invert_yaxis()
    d.set_xlabel("Median absolute change / %", fontsize=12.0)
    d.legend(frameon=False, ncol=1, loc="upper right")

    for ax in [a, b, c, d]:
        ax.xaxis.label.set_size(12.0)
        ax.yaxis.label.set_size(12.0)
        ax.tick_params(axis='both', labelsize=10.6)

    e.axis("off")
    items = [
        ("Fixed calipers", "Broad directions stable"),
        ("Reciprocal", "27/27 class directions"),
        ("Topology", "45/45 exact metal directions"),
        ("Adjustment", "18/18 log positive"),
        ("Family exclusion", "≤3% maximum change"),
    ]
    for i, (head, sub) in enumerate(items):
        x0 = 0.02 + i * 0.194
        e.add_patch(FancyBboxPatch((x0, 0.22), 0.17, 0.58,
                                   boxstyle="round,pad=0.02,rounding_size=0.03",
                                   facecolor=C["soft_box"], edgecolor=C["border"], linewidth=1.0))
        e.text(x0 + 0.085, 0.58, head, ha="center", va="center", fontweight="bold", fontsize=13.8)
        e.text(x0 + 0.085, 0.39, sub, ha="center", va="center", fontsize=12.5, fontweight="bold", color=C["muted"], alpha=0.7)

    fig.subplots_adjust(left=0.10, right=0.985, bottom=0.09, top=0.95, wspace=0.37, hspace=0.65)
    return fig, [p1, p2, p3, p4]


def figure6():
    proc, p1 = load(6, "process_translation_summary_final.csv")
    require(proc, ["intervention", "process", "metric", "statistic", "estimate", "bootstrap_95_low", "bootstrap_95_high"], "process")
    fig, axs = plt.subplots(1, 3, figsize=(10.6, 4.3), sharey=False, gridspec_kw={"width_ratios": [1.05, 1.05, 0.95]})
    a, b, c = axs
    panel(a, "A", None)
    panel(b, "B", None)
    panel(c, "C", None, False)

    def rows(metric_name):
        x = proc.loc[proc["metric"].eq(metric_name)].copy()
        x = x[x.intervention.isin(["linker_family_change", "metal_substitution"])]
        if x.empty:
            raise RuntimeError(f"No rows for exact process metric {metric_name!r}; available metrics={sorted(proc.metric.unique())}")
        x = x.dropna(subset=["estimate"])
        if x.empty:
            raise RuntimeError(f"All estimates are missing for {metric_name!r}")
        return x

    proc_order = ["landfill-gas-vpsa", "methane-storage-psa", "natural-gas-purification", "post-combustion-vsa", "pre-combustion-40-40"]
    process_labels = {
        "landfill-gas-vpsa": "Landfill gas",
        "methane-storage-psa": "CH$_4$ storage",
        "natural-gas-purification": "Natural-gas purification",
        "post-combustion-vsa": "Post-combustion",
        "pre-combustion-40-40": "Pre-combustion",
    }
    centers = np.arange(len(proc_order))
    y_map = {p: i for i, p in enumerate(proc_order)}
    labels = [process_labels[p] for p in proc_order]

    def draw(ax, x, show_ticks=True):
        x = x.copy()
        x["process_order"] = x["process"].map({p: i for i, p in enumerate(proc_order)})
        x = x.sort_values(["process_order", "intervention"])
        for inter, offset in [("linker_family_change", -0.11), ("metal_substitution", 0.11)]:
            sub = x[x.intervention.eq(inter)]
            y = [y_map[p] + offset for p in sub.process]
            point_intervals(ax, sub.estimate, sub.bootstrap_95_low, sub.bootstrap_95_high, y,
                            [IDARK[inter]] * len(sub), ms=3.8)
        ax.set_yticks(centers)
        if show_ticks:
            ax.set_yticklabels(labels)
        else:
            ax.set_yticklabels([])
        ax.invert_yaxis()
        ax.set_xlim(0, 1.02)
        ax.set_xlabel("Concordance fraction", fontsize=12.9)
        ax.axvline(.5, color=C["muted"], ls="--", lw=.8)
        ax.tick_params(axis='both', labelsize=11.4)

    draw(a, rows("uptake_working_capacity_concordant"), show_ticks=True)
    draw(b, rows("uptake_selectivity_concordant"), show_ticks=False)

    shared_handles = [
        Line2D([0], [0], marker='o', color=IDARK["linker_family_change"], markerfacecolor=IDARK["linker_family_change"], markersize=5, label='Linker family'),
        Line2D([0], [0], marker='o', color=IDARK["metal_substitution"], markerfacecolor=IDARK["metal_substitution"], markersize=5, label='Metal substitution'),
    ]
    fig.legend(handles=shared_handles, frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.43, -0.03), fontsize=11.1)

    c.axis("off")
    y = 0.88
    summary_rows = [
        ("Linker family", "Strong", "Adsorption + energetic separation", "Residual geometry modifies magnitude", C["linker_dark"]),
        ("Metal identity", "Conditional", "Coordination-compatible subset", "Context dependent", C["metal_dark"]),
        ("Functional motif", "Unsupported class", "Illustrative cases only", "Six primary pairs", C["functional_dark"]),
        ("Process translation", "Bounded", "Working capacity often aligns", "Selectivity can diverge", C["navy"]),
    ]
    for factor, status, evidence, boundary, col in summary_rows:
        c.add_patch(FancyBboxPatch((0.02, y - 0.14), 0.95, 0.16,
                                   boxstyle="round,pad=0.02,rounding_size=0.03",
                                   facecolor=C["soft_box"], edgecolor=C["border"], linewidth=0.9))
        c.text(0.05, y, factor, fontweight="bold", fontsize=8.4)
        c.text(0.95, y, status, fontweight="bold", fontsize=8.3, color=col, ha="right")
        c.text(0.05, y - 0.055, evidence, fontsize=7.3)
        c.text(0.05, y - 0.102, "Boundary: " + boundary, fontsize=7.1, color=C["muted"])
        y -= 0.205

    fig.subplots_adjust(left=0.08, right=0.99, bottom=0.23, top=0.90, wspace=0.30)
    return fig, [p1]


def main():
    style()
    outputs = []
    sources = []
    done = []
    for n, fn in [(1, figure1), (2, figure2), (3, figure3), (4, figure4), (6, figure6)]:
        fig, src = fn()
        outputs += finish(fig, n)
        sources += src
        done.append(n)
    report = [
        "PROJECT 7B2 QUANTITATIVE FIGURE RENDERING",
        "=" * 72,
        "Decision: FIGURES 1, 2, 3, 4, AND 6 RENDERED",
        f"Figures rendered: {done}",
        f"Output files: {len(outputs)}",
        f"Unique source files: {len(set(sources))}",
        "",
        "Figure 5 remains separate because it requires CIF rendering.",
        "No scientific estimate, imputation, pair selection, or directional rule was introduced.",
    ]
    (OUT / "06_render_report.txt").write_text("\n".join(report), encoding="utf-8", newline="\n")
    man = {
        "stage": "quantitative main-figure rendering",
        "created": datetime.now().isoformat(timespec="seconds"),
        "script": "06_render_quantitative_figures.py",
        "figures": done,
        "outputs": outputs,
        "sources": [{"path": str(p), "sha256": sha(p)} for p in sorted(set(sources))],
        "new_analysis": False,
        "python": sys.version,
        "pandas": pd.__version__,
        "matplotlib": plt.matplotlib.__version__,
    }
    (OUT / "06_manifest.json").write_text(json.dumps(man, indent=2), encoding="utf-8", newline="\n")
    print("\n".join(report))
    print(f"\nOutputs: {OUT}")


if __name__ == "__main__":
    main()
