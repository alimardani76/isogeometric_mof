#!/usr/bin/env python3
"""Project 7B2 Step 3, file 10: build the lean SI evidence package.

Place inside: Step 3 production/
Run from the 7B2 root:
    python "Step 3 production/10_build_lean_si_package.py"

This script creates only evidence-bearing SI assets from frozen outputs.
It performs no new matching, estimation, imputation, pair selection, or
mechanistic inference.

Outputs
-------
Step 3 results/si_figures/
    Figure_S01_Additional_Controls.pdf/.png
    Figure_S02_HOA_Associations.pdf/.png
    Figure_S03_Guest_Pressure_Specificity.pdf/.png
Step 3 results/si_tables/
    Table_S01_Condition_Coverage.tex
    Table_S02_Control_Summary.tex
    Table_S03_HOA_Summary.tex
    Table_S04_Guest_Specificity.tex
    Table_S05_Residual_Adjustment.tex
    Table_S06_Balance.tex
    Table_S07_Family_Exclusion.tex
    Table_S08_Process_Translation.tex
    Table_S09_Final_Cases_Charges.tex
Step 3 results/si_source_data/
    complete CSV copies used by the printed figures and tables
Step 3 results/si_production/
    10_report.txt
    10_manifest.json
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STEP2 = ROOT / "Step 2 results"
STEP3 = ROOT / "Step 3 results"
FIG_OUT = STEP3 / "si_figures"
TAB_OUT = STEP3 / "si_tables"
DATA_OUT = STEP3 / "si_source_data"
PROD_OUT = STEP3 / "si_production"
for p in [FIG_OUT, TAB_OUT, DATA_OUT, PROD_OUT]:
    p.mkdir(parents=True, exist_ok=True)

DPI = 600
COL = {
    "linker": "#4F97BF",
    "linker_fill": "#8ECAE6",
    "metal": "#D77FA1",
    "metal_fill": "#F6B6C8",
    "functional": "#7E7D90",
    "functional_fill": "#B8B8C8",
    "control": "#C9CDD6",
    "positive": "#5E9C76",
    "negative": "#C36B6B",
    "navy": "#496A81",
    "grid": "#E7EBF0",
    "text": "#27313A",
}
ILABEL = {
    "linker_family_change": "Linker family",
    "metal_substitution": "Metal substitution",
    "functional_motif_change": "Functional motif",
}
ICOLOR = {
    "linker_family_change": COL["linker"],
    "metal_substitution": COL["metal"],
    "functional_motif_change": COL["functional"],
}

SOURCE_NAMES = {
    "controls_primary": "step3_same_chemistry_control_results.csv",
    "controls_symmetric": "step5b_symmetric_control_results.csv",
    "hoa_condition": "heat_adsorption_condition_results.csv",
    "hoa_pressure": "heat_adsorption_pressure_results.csv",
    "guest": "05_results.csv",
    "guest_summary": "05_summary.csv",
    "adjustment": "03_results.csv",
    "adjustment_summary": "03_summary.csv",
    "balance": "04_balance.csv",
    "family": "04_family_exclusion_summary.csv",
    "process": "process_translation_summary_final.csv",
    "cases": "02_final_case_set.csv",
    "charge": "03_element_charge_summaries.csv",
    "heat_coverage": "7B2_heat_pair_coverage.csv",
    "condition_scales": "adsorption_condition_scales.csv",
}

EXCLUDE = {"archive", "full_pair_rules_work", "si_source_data", "si_figures", "si_tables"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def resolve(name: str) -> Path:
    matches = []
    for path in ROOT.rglob(name):
        if not path.is_file():
            continue
        rel = {part.lower() for part in path.relative_to(ROOT).parts}
        if rel & EXCLUDE:
            continue
        matches.append(path)
    if not matches:
        raise FileNotFoundError(f"Required frozen source not found: {name}")
    def priority(p: Path):
        s = str(p.relative_to(ROOT)).lower()
        if "step 3 results" in s: return 0
        if "step 2 results" in s: return 1
        if "analysis" in s: return 2
        return 3
    matches.sort(key=lambda p: (priority(p), len(p.parts), str(p)))
    best = priority(matches[0])
    peers = [p for p in matches if priority(p) == best]
    hashes = {sha256(p) for p in peers}
    if len(hashes) > 1:
        raise RuntimeError(f"Conflicting active sources for {name}: {peers}")
    return peers[0]


def setup_plotting():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "font.size": 8.8,
        "axes.titlesize": 9.8,
        "axes.labelsize": 8.8,
        "xtick.labelsize": 7.8,
        "ytick.labelsize": 7.8,
        "legend.fontsize": 7.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "text.color": "#000000",
        "axes.labelcolor": "#000000",
        "axes.titlecolor": "#000000",
        "xtick.color": "#000000",
        "ytick.color": "#000000",
        "font.weight": "bold",
        "axes.labelweight": "bold",
        "axes.titleweight": "bold",
    })


def panel(ax, letter: str, title: str):
    if letter:
        ax.text(-0.13, 1.08, letter, transform=ax.transAxes, fontweight="bold", fontsize=11.2, va="top", color="black")
    ax.set_title(title, loc="left", pad=8, fontweight="bold", color="black")
    ax.grid(axis="y", color=COL["grid"], lw=0.55, alpha=0.7)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight("bold")
        label.set_color("black")


def _bold_all(ax):
    ax.xaxis.label.set_fontweight("bold")
    ax.yaxis.label.set_fontweight("bold")
    ax.xaxis.label.set_color("black")
    ax.yaxis.label.set_color("black")
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight("bold")
        label.set_color("black")


def save_figure(fig, stem: str, *, left=0.10, right=0.98, bottom=0.22, top=0.91, wspace=0.35, hspace=0.42):
    fig.subplots_adjust(left=left, right=right, bottom=bottom, top=top, wspace=wspace, hspace=hspace)
    pdf = FIG_OUT / f"{stem}.pdf"
    png = FIG_OUT / f"{stem}.png"
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return [pdf, png]


def copy_source(key: str, path: Path):
    target = DATA_OUT / f"{key}__{path.name}"
    shutil.copy2(path, target)
    return target


def latex_escape(value) -> str:
    text = "" if pd.isna(value) else str(value)
    repl = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
        "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
    }
    for a, b in repl.items():
        text = text.replace(a, b)
    return text


def write_longtable(df: pd.DataFrame, path: Path, caption: str, label: str, columns: list[str], headers: list[str], formats=None):
    formats = formats or {}
    lines = [
        r"\begin{landscape}",
        r"\begin{longtable}{" + "l" * len(columns) + "}",
        rf"\caption{{{caption}}}\label{{{label}}}\\",
        r"\toprule",
        " & ".join(headers) + r" \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        " & ".join(headers) + r" \\",
        r"\midrule",
        r"\endhead",
    ]
    for _, row in df.iterrows():
        vals = []
        for col in columns:
            val = row.get(col, "")
            if col in formats and pd.notna(val):
                try:
                    val = formats[col].format(val)
                except Exception:
                    pass
            vals.append(latex_escape(val))
        lines.append(" & ".join(vals) + r" \\")
    lines += [r"\bottomrule", r"\end{longtable}", r"\end{landscape}", ""]
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _forest_conditions(ax, df: pd.DataFrame, measure: str, title: str):
    panel(ax, "", title)
    x = df[df["effect_measure"].eq(measure)].copy()
    x = x.sort_values(["intervention", "target", "p/bar"])
    y = np.arange(len(x))
    for yi, (_, row) in enumerate(x.iterrows()):
        est = row["median_chemistry_minus_control"]
        lo = row["bootstrap_95_low"]
        hi = row["bootstrap_95_high"]
        color = ICOLOR.get(row["intervention"], COL["functional"])
        ax.errorbar(est, yi, xerr=[[est-lo], [hi-est]], fmt="o",
                    color=color, capsize=2, ms=3.2, lw=.9)
    ax.axvline(0, color="#666666", lw=.8)
    ax.set_yticks([])
    ax.set_xlabel("Chemistry minus control")
    handles = [
        plt.Line2D([], [], marker="o", ls="", color=ICOLOR[k], label=ILABEL[k])
        for k in ["linker_family_change", "metal_substitution", "functional_motif_change"]
        if k in set(x["intervention"])
    ]
    ax.legend(handles=handles, frameon=False, loc="best")


def figure_s01_additional_controls(primary: pd.DataFrame, symmetric: pd.DataFrame):
    """Only control views not already shown in main Figure 2."""
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 4.2))
    specs = [
        (primary, "absolute_log_difference", "A", "Primary design: |Δlog q|"),
        (primary, "standardized_absolute_difference", "B", "Primary design: standardized |Δq|"),
        (symmetric, "standardized_absolute_difference", "C", "Symmetric design: standardized |Δq|"),
    ]
    for ax, (df, measure, letter, title) in zip(axes, specs):
        panel(ax, letter, title)
        x = df[df["effect_measure"].eq(measure)].copy()
        x = x.sort_values(["intervention", "target", "p/bar"])
        y = np.arange(len(x))
        for yi, (_, row) in enumerate(x.iterrows()):
            est = row["median_chemistry_minus_control"]
            lo = row["bootstrap_95_low"]
            hi = row["bootstrap_95_high"]
            color = ICOLOR.get(row["intervention"], COL["functional"])
            ax.errorbar(est, yi, xerr=[[est - lo], [hi - est]], fmt="o",
                        color=color, capsize=2, ms=3.1, lw=.85)
        ax.axvline(0, color="#666666", lw=.8)
        ax.set_yticks([])
        ax.set_xlabel("Chemistry minus control", fontweight="bold", color="black")
        _bold_all(ax)
    legend_order = ["linker_family_change", "metal_substitution", "functional_motif_change"]
    handles = [plt.Line2D([], [], marker="o", ls="", color=ICOLOR[k], label=ILABEL[k]) for k in legend_order]
    leg = fig.legend(handles=handles, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 0.04), ncol=3)
    for t in leg.get_texts():
        t.set_fontweight("bold")
        t.set_color("black")
    return save_figure(fig, "Figure_S01_Additional_Controls")

def figure_s02_hoa(hoa: pd.DataFrame):
    """Full HOA association intervals; main Figure 2 shows only the compact overview."""
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 4.7))
    for ax, measure, letter, title in [
        (axes[0], "absolute_log_difference", "A", "Absolute-log adsorption separation"),
        (axes[1], "standardized_absolute_difference", "B", "Standardized adsorption separation"),
    ]:
        panel(ax, letter, title)
        x = hoa[hoa["effect_measure"].eq(measure)].copy()
        x = x[x["intervention"].isin(["linker_family_change", "metal_substitution"])]
        x = x.sort_values(["intervention", "target", "p/bar"])
        y = np.arange(len(x))
        for yi, (_, row) in enumerate(x.iterrows()):
            est = row["spearman_rho_heat_vs_adsorption_separation"]
            lo = row["bootstrap_95_low_rho"]
            hi = row["bootstrap_95_high_rho"]
            color = ICOLOR[row["intervention"]]
            ax.errorbar(est, yi, xerr=[[est - lo], [hi - est]], fmt="o",
                        color=color, capsize=2, ms=3.2, lw=.9)
        ax.axvline(0, color="#666666", lw=.8)
        ax.set_yticks([])
        ax.set_xlabel(r"Spearman $\rho$: $|\Delta HOA|$ vs adsorption separation", fontweight="bold", color="black")
        _bold_all(ax)
    handles = [plt.Line2D([], [], marker="o", ls="", color=ICOLOR[k], label=ILABEL[k]) for k in ["linker_family_change", "metal_substitution"]]
    leg = fig.legend(handles=handles, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 0.04), ncol=2)
    for t in leg.get_texts():
        t.set_fontweight("bold")
        t.set_color("black")
    return save_figure(fig, "Figure_S02_HOA_Associations")

def figure_s03_guest(guest: pd.DataFrame, pressure: pd.DataFrame):
    """Guest/pressure results complementary to main Figure 3.

    The absolute-log guest panel is omitted because it is already in main Figure 3C.
    Color represents intervention class.
    """
    fig = plt.figure(figsize=(10.8, 10.8))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.92], hspace=0.62, wspace=0.34)
    axes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])]

    specs = [
        ("adsorption_separation", "standardized_absolute_difference", "A", "CO$_2$ minus co-guest standardized separation"),
        ("heat_contrast", "absolute_hoa_difference", "B", "CO$_2$ minus co-guest energetic contrast"),
    ]
    comp_lab = {
        "landfill_CO2_vs_CH4": "Landfill",
        "methane_purification_CO2_vs_CH4": "CH$_4$ purification",
        "post_combustion_CO2_vs_N2": "Post-combustion",
        "pre_combustion_CO2_vs_H2": "Pre-combustion",
    }
    reg_lab = {"low": "low", "high": "high"}
    for ax, (quantity, measure, letter, title) in zip(axes[:2], specs):
        panel(ax, letter, title)
        x = guest[(guest["quantity"].eq(quantity)) & (guest["measure"].eq(measure))].copy()
        x = x.sort_values(["comparison", "regime", "intervention"])
        x["row_label"] = (
            x["comparison"].map(comp_lab).fillna(x["comparison"].astype(str)) +
            " | " + x["regime"].map(reg_lab).fillna(x["regime"].astype(str)) +
            " | " + x["intervention"].map(ILABEL).fillna(x["intervention"].astype(str))
        )
        y = np.arange(len(x))
        for yi, (_, row) in enumerate(x.iterrows()):
            est = row["median_paired_difference_CO2_minus_coguest"]
            lo = row["median_bootstrap_95_low"]
            hi = row["median_bootstrap_95_high"]
            color = ICOLOR.get(row["intervention"], COL["functional"])
            ax.errorbar(est, yi, xerr=[[est - lo], [hi - est]], fmt="o",
                        color=color, capsize=2, ms=3.1, lw=.85)
        ax.axvline(0, color="#666666", lw=.8)
        ax.set_yticks(y)
        if letter == "A":
            ax.set_yticklabels(x["row_label"], fontsize=6.3)
            ax.set_ylabel("Comparison | regime | intervention", fontweight="bold", color="black")
        else:
            ax.set_yticklabels([])
            ax.set_ylabel("")
        ax.invert_yaxis()
        ax.set_xlabel("Paired CO$_2$ minus co-guest difference", fontweight="bold", color="black")
        _bold_all(ax)

    top_handles = [
        plt.Line2D([], [], marker="o", ls="", color=ICOLOR[k], label=ILABEL[k])
        for k in ["linker_family_change", "metal_substitution"]
    ]
    leg = fig.legend(top_handles, [h.get_label() for h in top_handles], frameon=False,
                     loc="center", bbox_to_anchor=(0.5, 0.49), ncol=2)
    for t in leg.get_texts():
        t.set_fontweight("bold")
        t.set_color("black")

    ax = axes[2]
    panel(ax, "C", "Linker pressure-change association")
    x = pressure[(pressure["intervention"].eq("linker_family_change")) & (pressure["effect_measure"].eq("absolute_log_difference"))].copy().sort_values("target")
    est_col = "spearman_rho_pressure_change_heat_vs_adsorption"
    if est_col not in x.columns:
        raise RuntimeError(f"Missing pressure-change association column: {est_col}")
    x = x.dropna(subset=[est_col]).copy()
    y = np.arange(len(x))
    for yi, (_, row) in enumerate(x.iterrows()):
        est = row[est_col]
        lo = row["bootstrap_95_low_rho"]
        hi = row["bootstrap_95_high_rho"]
        ax.errorbar(est, yi, xerr=[[est - lo], [hi - est]], fmt="o", color=COL["linker"], ecolor=COL["linker"], capsize=2, ms=3.2, lw=.9)
    ax.axvline(0, color="#666666", lw=.8)
    labels = [str(t).replace("_", " ") for t in x["target"]]
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_ylabel("Adsorption condition", fontweight="bold", color="black")
    ax.set_xlabel(r"Spearman $\rho$: pressure change in HOA vs adsorption", fontweight="bold", color="black")
    _bold_all(ax)
    return save_figure(fig, "Figure_S03_Guest_Pressure_Specificity", bottom=0.10, top=0.95, wspace=0.34, hspace=0.50)

def build_tables(src: dict[str, Path], dfs: dict[str, pd.DataFrame]):
    """Build readable, publication-facing SI tables from frozen outputs.

    Full source CSVs are already copied separately to si_source_data, so the
    printed tables can use compact labels and non-redundant columns without
    discarding provenance.
    """
    target_lab = {
        "landfill_CH4": r"Landfill CH$_4$", "landfill_CO2": r"Landfill CO$_2$",
        "methane_purification_CH4": r"Purification CH$_4$",
        "methane_purification_CO2": r"Purification CO$_2$",
        "methane_storage_CH4": r"Storage CH$_4$",
        "post_combustion_CO2": r"Post-comb. CO$_2$", "post_combustion_N2": r"Post-comb. N$_2$",
        "pre_combustion_CO2": r"Pre-comb. CO$_2$", "pre_combustion_H2": r"Pre-comb. H$_2$",
    }
    measure_lab = {
        "absolute_log_difference": r"$|\Delta\log q|$",
        "absolute_uptake_difference": r"$|\Delta q|$",
        "standardized_absolute_difference": r"Std. $|\Delta q|$",
        "absolute_hoa_difference": r"$|\Delta\mathrm{HOA}|$",
    }
    process_lab = {
        "landfill-gas-vpsa": "Landfill gas", "methane-storage-psa": r"CH$_4$ storage",
        "natural-gas-purification": "Natural-gas purification",
        "post-combustion-vsa": "Post-combustion", "pre-combustion-40-40": "Pre-combustion",
    }
    metric_lab = {
        "absolute_uptake_difference": r"$|\Delta q|$",
        "absolute_working_capacity_difference": r"$|\Delta WC|$",
        "absolute_selectivity_difference": r"$|\Delta S|$",
        "working_capacity_change_oriented_by_uptake": r"WC $\Delta$ (uptake-oriented)",
        "selectivity_change_oriented_by_uptake": r"Sel. $\Delta$ (uptake-oriented)",
        "uptake_working_capacity_concordant": "Uptake--WC concord.",
        "uptake_selectivity_concordant": "Uptake--sel. concord.",
    }
    comparison_lab = {
        "landfill_CO2_vs_CH4": r"Landfill CO$_2$/CH$_4$",
        "methane_purification_CO2_vs_CH4": r"Purification CO$_2$/CH$_4$",
        "post_combustion_CO2_vs_N2": r"Post-comb. CO$_2$/N$_2$",
        "pre_combustion_CO2_vs_H2": r"Pre-comb. CO$_2$/H$_2$",
    }
    geom_lab = {"Di_diff": r"$D_i$", "Df_diff": r"$D_f$", "Dif_diff": r"$D_{if}$",
                "Density_diff": "Density", "UC_volume_diff": "Cell volume",
                "AVAf_diff": "AVAf", "POAVAf_diff": "POAVAf"}
    role_lab = {
        "strong_linker_process_aligned": "Strong linker", "strong_metal_process_aligned": "Strong metal",
        "cu_zn_pressure_exception": "Cu--Zn exception", "near_null_comparison": "Near-null linker",
        "process_discordant_comparison": "Process-discordant", "functional_motif_example": "Functional motif",
    }

    def fnum(x, nd=3):
        if pd.isna(x): return "--"
        return f"{float(x):.{nd}f}"

    def fci(est, lo, hi, nd=3):
        return f"{fnum(est, nd)} [{fnum(lo, nd)}, {fnum(hi, nd)}]"

    def clean_text(x):
        return "" if pd.isna(x) else str(x)

    def write_compact(df, filename, caption, label, headers, widths, row_builder, note=None, size="scriptsize"):
        spec = "@{}" + "".join(r">{\raggedright\arraybackslash}p{" + w + "}" for w in widths) + "@{}"
        lines = [r"\begin{landscape}", rf"\{size}", r"\setlength{\tabcolsep}{2pt}",
                 r"\setlength{\LTleft}{0pt}", r"\setlength{\LTright}{0pt}",
                 r"\emergencystretch=1.5em", r"\sloppy",
                 r"\renewcommand{\arraystretch}{1.06}", rf"\begin{{longtable}}{{{spec}}}",
                 rf"\caption{{{caption}}}\label{{{label}}}\\", r"\toprule",
                 " & ".join(headers) + r" \\", r"\midrule", r"\endfirsthead", r"\toprule",
                 " & ".join(headers) + r" \\", r"\midrule", r"\endhead"]
        for _, row in df.iterrows():
            lines.append(" & ".join(row_builder(row)) + r" \\")
        lines += [r"\bottomrule", r"\end{longtable}"]
        if note:
            lines += [rf"\vspace{{-0.4em}}\noindent\footnotesize\textit{{Note:}} {note}"]
        lines += [r"\end{landscape}", ""]
        (TAB_OUT / filename).write_text("\n".join(lines), encoding="utf-8", newline="\n")

    # S1: one row per physical condition. The previous merge produced three
    # visually duplicate rows because intervention-specific HOA coverage was
    # joined without printing intervention. Pivot coverage instead.
    scales = dfs["condition_scales"].copy()
    heat = dfs["heat_coverage"].copy()
    cov = heat.pivot_table(index=["target", "T/K", "p/bar"], columns="intervention",
                           values="hoa_pair_coverage", aggfunc="first").reset_index()
    s01 = scales.merge(cov, on=["target", "T/K", "p/bar"], how="left", validate="one_to_one")
    write_compact(
        s01, "Table_S01_Condition_Coverage.tex",
        "Adsorption-condition definitions, robust scales, and pair-level HOA coverage.",
        "tab:si_condition_coverage",
        ["Condition", r"$T$ / K", r"$p$ / bar", r"$\epsilon$", "Robust scale", "HOA cov. linker", "HOA cov. metal", "HOA cov. func."],
        ["1.55in", ".55in", ".65in", ".70in", ".90in", ".85in", ".85in", ".85in"],
        lambda r: [target_lab.get(r["target"], clean_text(r["target"])), fnum(r["T/K"], 0), fnum(r["p/bar"], 2),
                   f"{r['epsilon_primary']:.1e}", fnum(r["robust_scale_iqr_over_1_349"], 3),
                   fnum(r.get("linker_family_change", np.nan), 3), fnum(r.get("metal_substitution", np.nan), 3),
                   fnum(r.get("functional_motif_change", np.nan), 3)],
        note="HOA coverage is the fraction of expected Primary pair rows with observed HOA at both endpoints."
    )
    s01.to_csv(DATA_OUT / "Table_S01_Condition_Coverage.csv", index=False)

    # S2: control summary.
    rows = []
    for design, df in [("Primary", dfs["controls_primary"]), ("Symmetric", dfs["controls_symmetric"])]:
        for (intervention, measure), g in df.groupby(["intervention", "effect_measure"]):
            rows.append({"design": design, "intervention": ILABEL.get(intervention, intervention), "measure": measure,
                         "conditions": len(g), "positive_medians": int((g["median_chemistry_minus_control"] > 0).sum()),
                         "intervals_above_zero": int((g["bootstrap_95_low"] > 0).sum()),
                         "intervals_below_zero": int((g["bootstrap_95_high"] < 0).sum())})
    s02 = pd.DataFrame(rows)
    write_compact(s02, "Table_S02_Control_Summary.tex", "Primary and symmetric same-chemistry control summaries.",
                  "tab:si_control_summary", ["Design", "Intervention", "Measure", "Conditions", "Median $>0$", "CI $>0$", "CI $<0$"],
                  [".75in", "1.20in", "1.25in", ".70in", ".75in", ".65in", ".65in"],
                  lambda r: [clean_text(r.design), clean_text(r.intervention), measure_lab.get(r.measure, clean_text(r.measure)),
                             str(int(r.conditions)), str(int(r.positive_medians)), str(int(r.intervals_above_zero)), str(int(r.intervals_below_zero))],
                  size="footnotesize")
    s02.to_csv(DATA_OUT / "Table_S02_Control_Summary.csv", index=False)

    # S3: supported quantitative HOA classes only.
    rows = []
    for (intervention, measure), g in dfs["hoa_condition"].groupby(["intervention", "effect_measure"]):
        if intervention not in {"linker_family_change", "metal_substitution"}: continue
        rho = g["spearman_rho_heat_vs_adsorption_separation"]
        rows.append({"intervention": ILABEL.get(intervention, intervention), "measure": measure, "conditions": len(g),
                     "positive_rho": int((rho > 0).sum()), "intervals_above_zero": int((g["bootstrap_95_low_rho"] > 0).sum()),
                     "median_rho": rho.median(), "maximum_absolute_rho": rho.abs().max()})
    s03 = pd.DataFrame(rows)
    write_compact(s03, "Table_S03_HOA_Summary.tex",
                  "Summary of matched heat-of-adsorption associations for supported quantitative intervention classes.",
                  "tab:si_hoa_summary", ["Intervention", "Adsorption scale", "Conditions", r"$\rho>0$", "CI $>0$", r"Median $\rho$", r"Max. $|\rho|$"],
                  ["1.35in", "1.45in", ".70in", ".65in", ".65in", ".80in", ".80in"],
                  lambda r: [clean_text(r.intervention), measure_lab.get(r.measure, clean_text(r.measure)), str(int(r.conditions)),
                             str(int(r.positive_rho)), str(int(r.intervals_above_zero)), fnum(r.median_rho, 3), fnum(r.maximum_absolute_rho, 3)],
                  size="footnotesize")
    s03.to_csv(DATA_OUT / "Table_S03_HOA_Summary.csv", index=False)

    # S4: complete linker/metal guest-specificity estimates with compact CI column.
    s04 = dfs["guest"].copy()
    write_compact(s04, "Table_S04_Guest_Specificity.tex", r"Paired CO$_2$ guest-specificity estimates in corresponding process regimes.",
                  "tab:si_guest_specificity",
                  ["Qty.", "Interv.", "Comp.", "Reg.", "Measure", "N", r"Median [95\% CI]", r"Frac."],
                  [".40in", ".78in", ".92in", ".34in", ".66in", ".34in", "1.08in", ".46in"],
                  lambda r: [("Ads." if r.quantity == "adsorption_separation" else "HOA"), ILABEL.get(r.intervention, clean_text(r.intervention)),
                             comparison_lab.get(r.comparison, clean_text(r.comparison)), clean_text(r.regime).title(),
                             measure_lab.get(r.measure, clean_text(r.measure)), str(int(r.paired_groups)),
                             fci(r.median_paired_difference_CO2_minus_coguest, r.median_bootstrap_95_low, r.median_bootstrap_95_high, 2),
                             fnum(r.fraction_groups_CO2_greater, 2)], size="tiny")
    s04.to_csv(DATA_OUT / "Table_S04_Guest_Specificity.csv", index=False)

    # S5: residual adjustment.
    s05 = dfs["adjustment"].copy()
    write_compact(s05, "Table_S05_Residual_Adjustment.tex", "Residual-geometry-adjusted linker-versus-control estimates.",
                  "tab:si_residual_adjustment",
                  ["Condition", r"$T$/K", r"$p$/bar", "Measure", "Cells", r"Unadjusted [95\% CI]", r"Adjusted [95\% CI]", r"$\Delta$ rel."],
                  ["1.12in", ".38in", ".45in", ".78in", ".38in", "1.20in", "1.20in", ".58in"],
                  lambda r: [target_lab.get(r.target, clean_text(r.target)), fnum(r["T/K"], 0), fnum(r["p/bar"], 3),
                             measure_lab.get(r.effect_measure, clean_text(r.effect_measure)), str(int(r.mixed_support_cells)),
                             fci(r.unadjusted_linker_minus_control, r.unadjusted_bootstrap_95_low, r.unadjusted_bootstrap_95_high, 3),
                             fci(r.adjusted_linker_minus_control, r.adjusted_bootstrap_95_low, r.adjusted_bootstrap_95_high, 3),
                             f"{100*r.relative_adjustment_change:.1f}\\%"], size="tiny")
    s05.to_csv(DATA_OUT / "Table_S05_Residual_Adjustment.csv", index=False)

    # S6: balance, avoiding redundant signed/absolute duplicate columns.
    s06 = dfs["balance"].copy()
    write_compact(s06, "Table_S06_Balance.tex", "Post hoc componentwise balance diagnostics for the symmetric design.",
                  "tab:si_balance",
                  ["Intervention", "Geometry", "Global SMD", "Median cell $|$SMD$|$", "Max. cell $|$SMD$|$", r"Frac. $<0.10$", r"Frac. $<0.20$"],
                  ["1.05in", ".72in", ".62in", ".92in", ".92in", ".64in", ".64in"],
                  lambda r: [ILABEL.get(r.intervention, clean_text(r.intervention)), geom_lab.get(r.geometry_variable, clean_text(r.geometry_variable)),
                             fnum(r.global_smd, 2), fnum(r.median_absolute_cell_smd, 2), fnum(r.maximum_absolute_cell_smd, 2),
                             fnum(r.fraction_cells_abs_smd_below_0_10, 2), fnum(r.fraction_cells_abs_smd_below_0_20, 2)], size="tiny")
    s06.to_csv(DATA_OUT / "Table_S06_Balance.csv", index=False)

    # S7: family exclusion.
    s07 = dfs["family"].copy()
    write_compact(s07, "Table_S07_Family_Exclusion.tex", "Sensitivity to exclusion of the largest and ten largest dependence groups.",
                  "tab:si_family_exclusion",
                  ["Intervention", "Measure", "N", "All +", "After max", "After top 10", r"Largest med./max. $\Delta$", r"Top 10 med./max. $\Delta$"],
                  ["1.00in", ".92in", ".35in", ".52in", ".62in", ".68in", ".92in", ".92in"],
                  lambda r: [ILABEL.get(r.intervention, clean_text(r.intervention)), measure_lab.get(r.effect_measure, clean_text(r.effect_measure)),
                             str(int(r.conditions)), str(int(r.all_positive)), str(int(r.exclude_largest_positive)), str(int(r.exclude_top10_positive)),
                             f"{100*r.median_abs_relative_change_excluding_largest:.1f}/{100*r.max_abs_relative_change_excluding_largest:.1f}\\%",
                             f"{100*r.median_abs_relative_change_excluding_top10:.1f}/{100*r.max_abs_relative_change_excluding_top10:.1f}\\%"], size="tiny")
    s07.to_csv(DATA_OUT / "Table_S07_Family_Exclusion.csv", index=False)

    # S8: process summary, linker and metal only.
    s08 = dfs["process"].copy()
    s08 = s08[s08["intervention"].isin(["linker_family_change", "metal_substitution"])].copy()
    write_compact(s08, "Table_S08_Process_Translation.tex", "Complete linker and metal process-translation summaries.",
                  "tab:si_process_translation", ["Interv.", "Process", "Metric", "Summary", r"Estimate [95\% CI]", "N"],
                  [".78in", ".82in", "1.22in", ".42in", "1.00in", ".32in"],
                  lambda r: [ILABEL.get(r.intervention, clean_text(r.intervention)), process_lab.get(r.process, clean_text(r.process)),
                             metric_lab.get(r.metric, clean_text(r.metric)), "Median" if r.statistic == "equal_weight_group_median" else "Mean",
                             fci(r.estimate, r.bootstrap_95_low, r.bootstrap_95_high, 2), str(int(r.groups))], size="tiny")
    s08.to_csv(DATA_OUT / "Table_S08_Process_Translation.csv", index=False)

    # S9: selected cases. Pair key is preserved in source CSVs but omitted from
    # print because it duplicates endpoint IDs and creates an unreadable table.
    cases = dfs["cases"].copy(); charge = dfs["charge"].copy(); rows = []
    for _, case in cases.iterrows():
        for endpoint in ["id_a", "id_b"]:
            mof = str(case[endpoint]); x = charge[(charge["mof_id"].astype(str).eq(mof)) & (charge["is_metal"].eq(True))]
            if x.empty:
                rows.append({"role": case["selection_category"], "endpoint": endpoint[-1].upper(), "mof_id": mof, "metal": "", "mean_metal_charge": np.nan})
            else:
                for _, rr in x.iterrows():
                    rows.append({"role": case["selection_category"], "endpoint": endpoint[-1].upper(), "mof_id": mof,
                                 "metal": rr["element"], "mean_metal_charge": rr["charge_mean"]})
    s09 = pd.DataFrame(rows)
    def breakable_mof_id(x):
        # Preserve the full identifier but permit line breaks after separators.
        s = str(x).replace("_", r"\_\allowbreak ").replace(".", r".\allowbreak ")
        return r"\texttt{" + s + "}"
    def s09row(r):
        return [role_lab.get(r.role, clean_text(r.role)), clean_text(r.endpoint), breakable_mof_id(r.mof_id),
                clean_text(r.metal), fnum(r.mean_metal_charge, 3)]
    write_compact(s09, "Table_S09_Final_Cases_Charges.tex", "Frozen structure cases and selected-case metal-charge fingerprints.",
                  "tab:si_cases_charges", ["Case", "End.", "MOF ID", "Metal", r"Mean REPEAT $q/e$"],
                  [".90in", ".34in", "3.95in", ".38in", ".68in"], s09row, size="tiny")
    s09.to_csv(DATA_OUT / "Table_S09_Final_Cases_Charges.csv", index=False)


def main():
    setup_plotting()

    # Remove stale SI figures from previous builds so deleted duplicate figures
    # do not survive in the output directory.
    for old in FIG_OUT.glob("Figure_S*.pdf"):
        old.unlink()
    for old in FIG_OUT.glob("Figure_S*.png"):
        old.unlink()

    src = {key: resolve(name) for key, name in SOURCE_NAMES.items()}
    dfs = {key: pd.read_csv(path, low_memory=False) for key, path in src.items()}
    copied = {key: copy_source(key, path) for key, path in src.items()}

    outputs = []
    outputs += figure_s01_additional_controls(dfs["controls_primary"], dfs["controls_symmetric"])
    outputs += figure_s02_hoa(dfs["hoa_condition"])
    outputs += figure_s03_guest(dfs["guest"], dfs["hoa_pressure"])
    build_tables(src, dfs)

    report = [
        "PROJECT 7B2 LEAN SI PACKAGE", "=" * 72,
        "Decision: THREE COMPLEMENTARY SI FIGURES AND NINE EVIDENCE TABLES BUILT",
        "",
        "SI figures retained:",
        "- S1 additional control diagnostics not already plotted in main Figure 2",
        "- S2 full condition-level HOA association intervals",
        "- S3 standardized guest specificity, energetic guest contrast, and pressure-change association",
        "",
        "Removed as redundant with main figures:",
        "- old S1 robustness: exact copy of main Figure 4",
        "- old S4 absolute-log guest panel: already shown in main Figure 3C",
        "- old S5 process translation: already shown in main Figure 6A-B",
        "- old S6 selected-case charge figure: charge fingerprints now shown in main Figure 5",
        "- symmetric absolute-log control panels already shown in main Figure 2A-B",
        "",
        "Printed SI tables: S1-S9",
        "Complete source CSVs copied to si_source_data.",
        "Tables are retained because they provide full numerical evidence/provenance rather than duplicate artwork.",
        "",
        "No new scientific estimate, imputation, matching, or pair selection was performed.",
    ]
    (PROD_OUT / "10_report.txt").write_text("\n".join(report), encoding="utf-8", newline="\n")
    manifest = {
        "stage": "lean SI package",
        "created": datetime.now().isoformat(timespec="seconds"),
        "script": "10_build_lean_si_package.py",
        "inputs": {key: {"path": str(path), "sha256": sha256(path)} for key, path in src.items()},
        "si_figure_count": 3,
        "si_table_count": 9,
        "removed_duplicate_main_figure_artwork": True,
        "new_analysis": False,
        "outputs": [str(p) for p in outputs],
        "python": sys.version,
        "pandas": pd.__version__,
        "matplotlib": plt.matplotlib.__version__,
    }
    (PROD_OUT / "10_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
    print("\n".join(report))
    print(f"\nFigures: {FIG_OUT}")
    print(f"Tables: {TAB_OUT}")
    print(f"Source data: {DATA_OUT}")


# ---------------------------------------------------------------------------
# COAUTHOR HANDOFF EXTENSION
# ---------------------------------------------------------------------------
# This extension implements the source-data package requested in the two
# Project 7B handoff manuals. It intentionally distinguishes AVAILABLE,
# NOT_COMPUTED, and NOT_APPLICABLE objects. No unavailable analysis is created.

HANDOFF_ROOT = STEP3 / "Paper7B_Hosein_to_Shayan_Frozen_Source_Package"

HANDOFF_SPECS = {
    "00_manifest": [
        ("step2_claim_matrix", "06_claim_evidence_matrix.csv", False),
        ("step2_figure_architecture", "06_figure_architecture.csv", False),
        ("figure_source_registry", "04_source_registry.csv", False),
        ("figure_blueprint", "05_panel_blueprint.csv", False),
    ],
    "01_master": [
        ("condition_registry", "adsorption_condition_scales.csv", True),
        ("primary_pair_counts", "final_primary_pair_counts.csv", True),
        ("primary_pairs", "final_primary_pairs.parquet", True),
    ],
    "02_matching": [
        ("symmetric_control_design", "step5b_symmetric_control_design.parquet", True),
        ("primary_control_design", "step3_control_common_support_design.parquet", True),
        ("same_chemistry_control_pairs", "step3_same_chemistry_control_pairs.parquet", True),
        ("balance_by_variable", "04_balance.csv", True),
        ("caliper_support", "caliper_sensitivity_support.csv", True),
    ],
    "03_effects": [
        ("pair_effects", "final_primary_pair_effect_magnitudes.parquet", True),
        ("group_effects", "corrected_group_effect_magnitudes.parquet", True),
        ("hoa_condition_results", "heat_adsorption_condition_results.csv", True),
        ("hoa_pressure_results", "heat_adsorption_pressure_results.csv", True),
        ("guest_specificity", "05_results.csv", True),
        ("residual_adjustment", "03_results.csv", True),
    ],
    "04_controls": [
        ("primary_control_results", "step3_same_chemistry_control_results.csv", True),
        ("symmetric_control_results", "step5b_symmetric_control_results.csv", True),
    ],
    "05_robustness_transfer": [
        ("reciprocal_matching", "reciprocal_covariance_matching_summary.csv", True),
        ("topology_robustness", "step1_topology_robustness_summary.csv", True),
        ("residual_geometry", "step2_residual_geometry_summary.csv", True),
        ("family_exclusion", "04_family_exclusion_results.csv", True),
        ("family_exclusion_summary", "04_family_exclusion_summary.csv", True),
    ],
    "06_cif_chemistry": [
        ("charge_mapping_audit", "03_charge_mapping_audit.csv", True),
        ("atom_level_case_data", "03_atom_charge_rows.csv", True),
        ("framework_charge_summaries", "03_framework_charge_summaries.csv", True),
        ("element_charge_summaries", "03_element_charge_summaries.csv", True),
        ("pair_charge_contrasts", "03_pair_charge_contrasts.csv", True),
    ],
    "07_process": [
        ("process_summary", "process_translation_summary_final.csv", True),
        ("process_pair_results", "process_translation_pair_results_final.parquet", False),
    ],
    "08_structures": [
        ("final_case_set", "02_final_case_set.csv", True),
        ("final_case_frameworks", "02_final_case_frameworks.csv", True),
        ("case_review_sheet", "final_case_review_sheet.csv", True),
        ("case_pair_audit", "candidate_pair_audit.csv", True),
        ("case_adsorption", "candidate_adsorption_conditions.csv", True),
        ("case_process", "candidate_process_results.csv", True),
    ],
}

UNAVAILABLE_OBJECTS = [
    {
        "object": "shuffled_chemistry_negative_controls",
        "status": "NOT_COMPUTED",
        "reason": "No dependence-preserving shuffled-label control was executed; same-chemistry controls are the implemented falsification baseline.",
    },
    {
        "object": "loose_match_negative_controls",
        "status": "NOT_COMPUTED",
        "reason": "No dedicated loose-match null was executed; fixed caliper tiers were used as sensitivity analyses, not null controls.",
    },
    {
        "object": "true_held_out_family_transfer",
        "status": "NOT_COMPUTED",
        "reason": "Reciprocal matching and topology filtering test robustness within observed support, not prediction into unseen families.",
    },
    {
        "object": "permutation_p_values_and_fdr",
        "status": "NOT_COMPUTED",
        "reason": "The frozen analysis reports effect estimates and dependence-aware bootstrap intervals rather than a formal p-value family.",
    },
    {
        "object": "accessible_heteroatom_intervention",
        "status": "NOT_COMPUTED",
        "reason": "No outcome-independent accessible-heteroatom intervention class was validated.",
    },
    {
        "object": "charge_localization_intervention",
        "status": "NOT_COMPUTED",
        "reason": "Charge data were used for selected-case fingerprints only, not as a global intervention class.",
    },
    {
        "object": "higher_fidelity_mechanism_validation",
        "status": "NOT_AVAILABLE",
        "reason": "No adsorption-density map, energy decomposition, site scan, or new experimental validation was performed.",
    },
    {
        "object": "directional_rule_cards",
        "status": "NOT_APPLICABLE",
        "reason": "Primary chemistry transitions are unordered and do not support universal directional substitution rules.",
    },
]


def build_coauthor_handoff():
    if HANDOFF_ROOT.exists():
        shutil.rmtree(HANDOFF_ROOT)
    HANDOFF_ROOT.mkdir(parents=True, exist_ok=True)

    inventory_rows = []
    for folder, specs in HANDOFF_SPECS.items():
        destination = HANDOFF_ROOT / folder
        destination.mkdir(parents=True, exist_ok=True)
        for object_name, basename, required in specs:
            try:
                source = resolve(basename)
            except FileNotFoundError:
                if required:
                    raise
                inventory_rows.append({
                    "object": object_name, "folder": folder, "basename": basename,
                    "status": "OPTIONAL_SOURCE_NOT_FOUND", "source_path": "",
                    "packaged_path": "", "sha256": "", "size_bytes": np.nan,
                })
                continue
            target = destination / source.name
            shutil.copy2(source, target)
            inventory_rows.append({
                "object": object_name, "folder": folder, "basename": basename,
                "status": "PACKAGED", "source_path": str(source),
                "packaged_path": str(target.relative_to(HANDOFF_ROOT)),
                "sha256": sha256(source), "size_bytes": source.stat().st_size,
            })

    # Selected original CIFs are mandatory for independent reconstruction.
    case_file = resolve("02_final_case_set.csv")
    cases = pd.read_csv(case_file)
    cif_folder = HANDOFF_ROOT / "08_structures" / "cifs_selected"
    cif_folder.mkdir(parents=True, exist_ok=True)
    active_cif_dirs = [p for p in ROOT.rglob("cifs") if p.is_dir() and "final_structure_case_inspection" in str(p)]
    if len(active_cif_dirs) != 1:
        raise RuntimeError(f"Expected one active selected-case CIF directory, found: {active_cif_dirs}")
    cif_source_dir = active_cif_dirs[0]
    case_ids = set(cases["id_a"].astype(str)) | set(cases["id_b"].astype(str))
    copied_cifs = 0
    for mof_id in sorted(case_ids):
        candidates = list(cif_source_dir.glob(f"{mof_id}*.cif"))
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one selected CIF for {mof_id}, found: {candidates}")
        source = candidates[0]
        target = cif_folder / source.name
        shutil.copy2(source, target)
        copied_cifs += 1
        inventory_rows.append({
            "object": "selected_cif", "folder": "08_structures/cifs_selected",
            "basename": source.name, "status": "PACKAGED", "source_path": str(source),
            "packaged_path": str(target.relative_to(HANDOFF_ROOT)),
            "sha256": sha256(source), "size_bytes": source.stat().st_size,
        })

    # Plot-ready and SI source folders are copied after they are built.
    figure_source = STEP3 / "figure_source_data"
    si_source = DATA_OUT
    for folder_name, source_dir in [("09_figure_source", figure_source), ("10_si_source", si_source)]:
        destination = HANDOFF_ROOT / folder_name
        if not source_dir.exists():
            raise FileNotFoundError(source_dir)
        shutil.copytree(source_dir, destination)
        for path in destination.rglob("*"):
            if path.is_file():
                inventory_rows.append({
                    "object": folder_name, "folder": folder_name,
                    "basename": path.name, "status": "PACKAGED",
                    "source_path": str(source_dir / path.relative_to(destination)),
                    "packaged_path": str(path.relative_to(HANDOFF_ROOT)),
                    "sha256": sha256(path), "size_bytes": path.stat().st_size,
                })

    manifest_dir = HANDOFF_ROOT / "00_manifest"
    manifest_dir.mkdir(exist_ok=True)
    inventory = pd.DataFrame(inventory_rows)
    inventory.to_csv(manifest_dir / "output_hash_manifest.csv", index=False)
    pd.DataFrame(UNAVAILABLE_OBJECTS).to_csv(manifest_dir / "availability_matrix.csv", index=False)

    readme = f"""# Project 7B frozen source-data handoff

This package was created from the frozen Project 7B2 outputs for independent
figure, table, and manuscript reconstruction.

## Scientific boundary

The package supports geometry-controlled, observational chemistry contrasts.
It does not support formal causality, universal directional substitution rules,
periodic metal trends, unseen-family predictive transfer, or a resolved global
charge/site mechanism.

## Included

- frozen primary pair and pair-condition effect tables;
- primary and symmetric same-chemistry controls;
- heat-of-adsorption, guest-specificity, pressure, residual-adjustment,
  balance, family-exclusion, reciprocal, topology, and process outputs;
- six-case selection ledger, original CIFs, atom-level charge rows, and
  framework/element charge summaries;
- complete main-figure and SI source-data folders;
- SHA-256 output manifest and explicit availability matrix.

## Explicitly unavailable

See `00_manifest/availability_matrix.csv`. Objects not computed are marked
rather than fabricated.

## Selected CIFs

{copied_cifs} original CIF files were copied for the 12 frozen framework endpoints.

## Reproducibility rule

Every number shown in a figure or table should be traced to a packaged source
file and cross-checked against `00_manifest/output_hash_manifest.csv`.
"""
    (HANDOFF_ROOT / "README_HOSEIN_HANDOFF.md").write_text(readme, encoding="utf-8", newline="\n")

    run_manifest = {
        "package": "Paper7B_Hosein_to_Shayan_Frozen_Source_Package",
        "created": datetime.now().isoformat(timespec="seconds"),
        "builder": "10_build_lean_si_package.py",
        "frozen": True,
        "selected_case_pairs": int(len(cases)),
        "selected_frameworks": int(len(case_ids)),
        "selected_cifs": copied_cifs,
        "packaged_files": int(len(inventory)),
        "unavailable_objects": len(UNAVAILABLE_OBJECTS),
        "scientific_values_changed": False,
        "new_analysis": False,
    }
    (manifest_dir / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2), encoding="utf-8", newline="\n")
    return run_manifest, inventory


# Save the original main entrypoint and extend it without changing prior logic.
_original_main = main

def main():
    _original_main()
    run_manifest, inventory = build_coauthor_handoff()
    report_path = PROD_OUT / "10_report.txt"
    prior = report_path.read_text(encoding="utf-8")
    extra = [
        "", "COAUTHOR HANDOFF PACKAGE", "-" * 72,
        f"Package: {HANDOFF_ROOT}",
        f"Packaged files: {run_manifest['packaged_files']}",
        f"Selected CIFs: {run_manifest['selected_cifs']}",
        f"Explicitly unavailable objects: {run_manifest['unavailable_objects']}",
        "Unavailable analyses were documented, not generated.",
    ]
    report_path.write_text(prior + "\n" + "\n".join(extra), encoding="utf-8", newline="\n")
    print("\n".join(extra))


if __name__ == "__main__":
    main()
