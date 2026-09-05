from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from .style import (
    apply_style, clean_axis, panel_label, title_left, save_figure,
    COLORS, INTERVENTION_COLOR, INTERVENTION_LABEL, PROCESS_LABEL,
    TARGET_LABEL, TARGET_ORDER, ROLE_LABEL, legend_handles_interventions,
)
from .utils import (
    DATA_MAIN, DATA_RASPA, OUT_MAIN, read_main, read_raspa,
    ordered_conditions, write_panel_source, write_manifest, symmetric_limits,
)


def _errorbar_rows(ax, df, x, lo, hi, y, color, marker="o", label=None,
                   offset=0.0, ms=5.0, open_marker=False, zorder=3):
    yy = np.asarray(df[y] if isinstance(y, str) else y, dtype=float) + offset
    face = "white" if open_marker else color
    xv = df[x].to_numpy(dtype=float)
    lov = df[lo].to_numpy(dtype=float)
    hiv = df[hi].to_numpy(dtype=float)
    ax.errorbar(
        xv, yy, xerr=[xv - lov, hiv - xv], fmt=marker,
        color=color, ecolor=color, elinewidth=1.15, capsize=2.3,
        ms=ms, markerfacecolor=face, markeredgewidth=1.0,
        label=label, zorder=zorder,
    )


def _condition_table(df):
    d = ordered_conditions(df)
    return d.drop_duplicates(["target", "T/K", "p/bar"])[
        ["target", "T/K", "p/bar", "condition_label"]
    ].reset_index(drop=True)


def _comparison_label(comp: str) -> str:
    return {
        "landfill_CO2_vs_CH4": r"Landfill $\mathrm{CO_2-CH_4}$",
        "methane_purification_CO2_vs_CH4": r"Purification $\mathrm{CO_2-CH_4}$",
        "post_combustion_CO2_vs_N2": r"Post-comb. $\mathrm{CO_2-N_2}$",
        "pre_combustion_CO2_vs_H2": r"Pre-comb. $\mathrm{CO_2-H_2}$",
    }.get(comp, comp)


def render_figure_01():
    apply_style(10.0)
    counts = read_main("04_final_primary_pair_counts.csv")
    cal = read_main("04_caliper_sensitivity_support.csv")
    primary = cal[cal["tier"].eq("primary")][["intervention", "related_groups", "exact_changes"]]
    counts = counts.merge(primary, on="intervention", how="left", validate="one_to_one")
    order = ["linker_family_change", "metal_substitution", "functional_motif_change"]
    counts["intervention"] = pd.Categorical(counts["intervention"], order, ordered=True)
    counts = counts.sort_values("intervention")
    cal["intervention"] = pd.Categorical(cal["intervention"], order, ordered=True)
    cal = cal.sort_values(["intervention", "tier_order"])

    fig, axs = plt.subplots(
        2, 2, figsize=(11.6, 7.5),
        gridspec_kw={"wspace": 0.38, "hspace": 0.35},
    )
    a, b, c, d = axs.ravel()

    # A — publication-style box/arrow workflow (no loose caveat text).
    a.set_axis_off()
    panel_label(a, "A", x=-0.10, y=1.08)
    title_left(a, "Matched-contrast design")
    steps = [
        ("MOF population", "linked structure + adsorption", COLORS["linker"], "#F3F7FC"),
        ("Exact context", "topology + dimensionality", COLORS["control"], "#F6F7F9"),
        ("Measured geometry", "seven fixed calipers", COLORS["control"], "#F6F7F9"),
        ("Chemistry change", "linker / metal / motif", COLORS["metal"], "#FFF6EF"),
        ("Evidence unit", "contrast → dependence family", COLORS["linker"], "#F3F7FC"),
    ]
    x0, w, h = 0.08, 0.83, 0.108
    ys = [0.815, 0.635, 0.455, 0.275, 0.095]
    for i, ((head, sub, edge, fill), y0) in enumerate(zip(steps, ys)):
        box = FancyBboxPatch(
            (x0, y0), w, h,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            transform=a.transAxes, facecolor=fill, edgecolor=edge,
            linewidth=1.35, clip_on=False,
        )
        a.add_patch(box)
        # Thin semantic color strip gives hierarchy without a dashboard look.
        a.add_patch(FancyBboxPatch(
            (x0, y0), 0.018, h,
            boxstyle="round,pad=0.0,rounding_size=0.009",
            transform=a.transAxes, facecolor=edge, edgecolor=edge,
            linewidth=0, clip_on=False,
        ))
        a.text(x0 + 0.055, y0 + h * 0.74, head, transform=a.transAxes,
               ha="left", va="center", fontsize=10.8, fontweight="bold")
        a.text(x0 + 0.055, y0 + h * 0.25, sub, transform=a.transAxes,
               ha="left", va="center", fontsize=9.2, color=COLORS["muted"])
        if i < len(ys) - 1:
            xmid = x0 + w / 2
            y_top = y0 - 0.024
            y_bot = ys[i + 1] + h + 0.030
            a.plot([xmid, xmid], [y_top, y_bot], transform=a.transAxes,
                   color="#8B929C", lw=1.45, solid_capstyle="round", clip_on=False, zorder=3)
            a.scatter([xmid], [y_bot], transform=a.transAxes,
                      marker="v", s=42, color="#8B929C", clip_on=False, zorder=4)
    a.set_xlim(0, 1); a.set_ylim(0, 1)

    # B — thinner bars and cleaner count labels.
    title_left(b, "Primary chemistry-changing support"); panel_label(b, "B")
    y = np.arange(len(counts))[::-1]
    for yi, (_, r) in zip(y, counts.iterrows()):
        inter = str(r["intervention"])
        val = float(r["raw_pairs"])
        b.barh(yi, val, color=INTERVENTION_COLOR[inter], height=0.30, zorder=2)
        xpos = val * 1.07 if val > 10 else val + 0.55
        b.text(xpos, yi, f"{int(val):,}", va="center", fontsize=9.5, fontweight="bold")
    b.set_xscale("log")
    b.set_xlabel("Primary matched pairs (log scale)")
    b.set_yticks(y, [INTERVENTION_LABEL[str(i)] for i in counts["intervention"]])
    b.set_xlim(1, max(counts["raw_pairs"]) * 3.0)
    clean_axis(b, "x")

    # C — direct line labels remove the legend from the data region.
    title_left(c, "Support contracts as geometry limits tighten"); panel_label(c, "C")
    tier_tbl = cal[["tier_order", "tier"]].drop_duplicates().sort_values("tier_order")
    for inter in order:
        g = cal[cal["intervention"].astype(str).eq(inter)].sort_values("tier_order")
        c.plot(g["tier_order"], g["raw_pairs"], "-o", lw=1.8, ms=5.4,
               color=INTERVENTION_COLOR[inter])
        last = g.iloc[-1]
        c.annotate(
            INTERVENTION_LABEL[inter],
            (float(last["tier_order"]), float(last["raw_pairs"])),
            xytext=(8, 0), textcoords="offset points", ha="left", va="center",
            color=INTERVENTION_COLOR[inter], fontsize=9.2, fontweight="bold",
            clip_on=False,
        )
    c.set_yscale("log")
    c.set_ylabel("Accepted pairs")
    c.set_xticks(tier_tbl["tier_order"], [str(t).replace("_", " ").title() for t in tier_tbl["tier"]])
    c.tick_params(axis="x", rotation=12)
    c.set_xlim(float(tier_tbl.tier_order.min()) - 0.18, float(tier_tbl.tier_order.max()) + 0.95)
    clean_axis(c, "y")

    # D — keep the strong dumbbell design, only clean styling/legend.
    title_left(d, "Dependence families define the evidence units"); panel_label(d, "D")
    y = np.arange(len(counts))[::-1]
    for yi, (_, r) in zip(y, counts.iterrows()):
        inter = str(r["intervention"])
        x1, x2 = float(r["raw_pairs"]), float(r["related_groups"])
        d.plot([x2, x1], [yi, yi], color=COLORS["control_light"], lw=3.2, solid_capstyle="round")
        d.scatter([x1], [yi], s=48, color=INTERVENTION_COLOR[inter], zorder=3)
        d.scatter([x2], [yi], s=48, facecolor="white", edgecolor=INTERVENTION_COLOR[inter], linewidth=1.35, zorder=3)
    d.set_xscale("log")
    d.set_xlabel("Count (log scale)")
    d.set_yticks(y, [INTERVENTION_LABEL[str(i)] for i in counts["intervention"]])
    clean_axis(d, "x")
    d.legend(
        handles=[
            Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORS["control"], markeredgecolor=COLORS["control"], markersize=7, label="Raw pairs"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor="white", markeredgecolor=COLORS["control"], markersize=7, label="Dependence families"),
        ],
        frameon=False, loc="lower right", borderaxespad=0.2,
    )

    fig.subplots_adjust(left=0.11, right=0.95, top=0.94, bottom=0.09)
    fig_dir = OUT_MAIN / "Figure_01"; fig_dir.mkdir(parents=True, exist_ok=True)
    outputs = save_figure(fig, fig_dir / "Figure_01")
    plt.close(fig)
    pA = write_panel_source(counts, fig_dir, "A_support")
    pB = write_panel_source(counts, fig_dir, "B")
    pC = write_panel_source(cal, fig_dir, "C")
    pD = write_panel_source(counts[["intervention", "raw_pairs", "related_groups", "exact_changes"]], fig_dir, "D")
    inputs = [DATA_MAIN / "04_final_primary_pair_counts.csv", DATA_MAIN / "04_caliper_sensitivity_support.csv"]
    write_manifest(fig_dir, "Figure_01", inputs, outputs, [pA, pB, pC, pD], {"science": "frozen support only; no refitting"})
    return outputs


def render_figure_02():
    apply_style(9.75)
    primary = read_main("04_step3_same_chemistry_control_results.csv")
    symmetric = read_main("04_step5b_symmetric_control_results.csv")
    hoa = read_main("04_heat_adsorption_condition_results.csv")
    adj = read_main("04_03_results.csv")
    ints = ["linker_family_change", "metal_substitution"]

    p = primary[(primary.effect_measure == "absolute_log_difference") & primary.intervention.isin(ints)].copy()
    s = symmetric[(symmetric.effect_measure == "absolute_log_difference") & symmetric.intervention.isin(ints)].copy()
    h = hoa[(hoa.effect_measure == "absolute_log_difference") & hoa.intervention.isin(ints)].copy()
    j = adj[adj.effect_measure == "absolute_log_difference"].copy()
    cond = _condition_table(p)
    key = ["target", "T/K", "p/bar"]
    ymap = {tuple(r[k] for k in key): i for i, r in cond.iterrows()}
    for df in [p, s, h, j]:
        df["y"] = [ymap[tuple(r[k] for k in key)] for _, r in df.iterrows()]
    n = len(cond)

    fig, axs = plt.subplots(
        2, 2, figsize=(12.45, 9.6), sharey=False,
        gridspec_kw={"wspace": 0.25, "hspace": 0.31},
    )
    a, b, c, d = axs.ravel()
    for ax in axs.ravel():
        ax.axvline(0, color=COLORS["control"], lw=0.85, zorder=1)

    title_left(a, "Primary same-chemistry background"); panel_label(a, "A")
    for inter, off in zip(ints, [-0.16, 0.16]):
        g = p[p.intervention == inter].sort_values("y")
        _errorbar_rows(a, g, "median_chemistry_minus_control", "bootstrap_95_low", "bootstrap_95_high", "y",
                       INTERVENTION_COLOR[inter], offset=off)
    a.set_xlabel(r"Chemistry minus control · $|\Delta\log q|$")
    a.set_yticks(range(n), cond["condition_label"]); a.invert_yaxis(); clean_axis(a, "x")

    title_left(b, "Symmetric nearest-pair confirmation"); panel_label(b, "B")
    for inter, off in zip(ints, [-0.16, 0.16]):
        g = s[s.intervention == inter].sort_values("y")
        _errorbar_rows(b, g, "median_chemistry_minus_control", "bootstrap_95_low", "bootstrap_95_high", "y",
                       INTERVENTION_COLOR[inter], offset=off)
    b.set_xlabel(r"Chemistry minus control · $|\Delta\log q|$")
    b.set_yticks(range(n), []); b.set_ylim(n - 0.5, -0.5); clean_axis(b, "x")

    title_left(c, "Energetic association"); panel_label(c, "C")
    for inter, off in zip(ints, [-0.16, 0.16]):
        g = h[h.intervention == inter].sort_values("y")
        _errorbar_rows(c, g, "spearman_rho_heat_vs_adsorption_separation", "bootstrap_95_low_rho", "bootstrap_95_high_rho", "y",
                       INTERVENTION_COLOR[inter], offset=off)
    c.set_xlabel(r"Spearman $\rho$: $|\Delta HOA|$ vs $|\Delta\log q|$")
    c.set_yticks(range(n), cond["condition_label"]); c.set_ylim(n - 0.5, -0.5); clean_axis(c, "x")

    title_left(d, "Residual measured-geometry adjustment"); panel_label(d, "D")
    g = j.sort_values("y")
    for _, r in g.iterrows():
        yv = r["y"]
        d.plot([r["adjusted_linker_minus_control"], r["unadjusted_linker_minus_control"]], [yv, yv],
               color=COLORS["control_light"], lw=2.5, zorder=1)
    _errorbar_rows(d, g, "unadjusted_linker_minus_control", "unadjusted_bootstrap_95_low", "unadjusted_bootstrap_95_high", "y",
                   COLORS["control"], open_marker=True)
    _errorbar_rows(d, g, "adjusted_linker_minus_control", "adjusted_bootstrap_95_low", "adjusted_bootstrap_95_high", "y",
                   COLORS["linker"])
    d.set_xlabel(r"Linker minus control · $|\Delta\log q|$")
    d.set_yticks(range(n), []); d.set_ylim(n - 0.5, -0.5); clean_axis(d, "x")

    # One clean figure-level legend; no legends sitting on the data.
    handles = legend_handles_interventions(False) + [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="white", markeredgecolor=COLORS["control"], markersize=6.8, label="Unadjusted (panel D)"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORS["linker"], markeredgecolor=COLORS["linker"], markersize=6.8, label="Adjusted (panel D)"),
    ]
    fig.legend(handles=handles, frameon=False, ncol=4, loc="lower center", bbox_to_anchor=(0.58, 0.012), columnspacing=1.4, handletextpad=0.5)

    fig.subplots_adjust(left=0.235, right=0.985, top=0.955, bottom=0.100)
    fig_dir = OUT_MAIN / "Figure_02"; fig_dir.mkdir(parents=True, exist_ok=True)
    outputs = save_figure(fig, fig_dir / "Figure_02"); plt.close(fig)
    pA = write_panel_source(p, fig_dir, "A"); pB = write_panel_source(s, fig_dir, "B")
    pC = write_panel_source(h, fig_dir, "C"); pD = write_panel_source(j, fig_dir, "D")
    inputs = [DATA_MAIN / "04_step3_same_chemistry_control_results.csv", DATA_MAIN / "04_step5b_symmetric_control_results.csv",
              DATA_MAIN / "04_heat_adsorption_condition_results.csv", DATA_MAIN / "04_03_results.csv"]
    write_manifest(fig_dir, "Figure_02", inputs, outputs, [pA, pB, pC, pD], {"focus": "absolute-log main-text evidence; standardized detail moved to SI"})
    return outputs


def render_figure_03():
    apply_style(9.95)
    hp = read_main("04_heat_adsorption_pressure_results.csv")
    guest = read_main("04_05_results.csv")
    link = hp[(hp.intervention == "linker_family_change") & (hp.effect_measure == "absolute_log_difference")].copy()
    rank = {t: i for i, t in enumerate(TARGET_ORDER)}
    link["rank"] = link.target.map(rank); link = link.sort_values("rank")
    y = np.arange(len(link))

    fig, axs = plt.subplots(2, 2, figsize=(11.9, 8.35), gridspec_kw={"wspace": 0.40, "hspace": 0.34})
    a, b, c, d = axs.ravel()

    title_left(a, "Pressure response of adsorption separation"); panel_label(a, "A")
    for yi, (_, r) in zip(y, link.iterrows()):
        a.plot([r.median_adsorption_low, r.median_adsorption_high], [yi, yi], color=COLORS["control_light"], lw=2.8, solid_capstyle="round")
        a.scatter(r.median_adsorption_low, yi, s=48, facecolor="white", edgecolor=COLORS["linker"], lw=1.35, zorder=3)
        a.scatter(r.median_adsorption_high, yi, s=48, color=COLORS["linker"], zorder=3)
    a.set_yticks(y, [TARGET_LABEL[t] for t in link.target]); a.invert_yaxis()
    a.set_xlabel(r"Median $|\Delta\log q|$"); clean_axis(a, "x")

    title_left(b, "Pressure response of energetic contrast"); panel_label(b, "B")
    for yi, (_, r) in zip(y, link.iterrows()):
        b.plot([r.median_heat_low, r.median_heat_high], [yi, yi], color=COLORS["control_light"], lw=2.8, solid_capstyle="round")
        b.scatter(r.median_heat_low, yi, s=48, facecolor="white", edgecolor=COLORS["co2"], lw=1.35, zorder=3)
        b.scatter(r.median_heat_high, yi, s=48, color=COLORS["co2"], zorder=3)
    b.set_yticks(y, []); b.set_ylim(len(y) - 0.5, -0.5)
    b.set_xlabel(r"Median $|\Delta HOA|$"); clean_axis(b, "x")

    title_left(c, "Guest specificity within paired process regimes"); panel_label(c, "C")
    g = guest[(guest.quantity == "adsorption_separation") & (guest.measure == "absolute_log_difference")].copy()
    comp_order = ["landfill_CO2_vs_CH4", "methane_purification_CO2_vs_CH4", "post_combustion_CO2_vs_N2", "pre_combustion_CO2_vs_H2"]
    rows = [(comp, reg) for comp in comp_order for reg in ["low", "high"]]
    ymap = {(comp, reg): i for i, (comp, reg) in enumerate(rows)}
    g["y"] = [ymap[(r.comparison, r.regime)] for _, r in g.iterrows()]
    c.axvline(0, color=COLORS["control"], lw=0.85)
    for inter, off in [("linker_family_change", -0.15), ("metal_substitution", 0.15)]:
        gg = g[g.intervention == inter].sort_values("y")
        _errorbar_rows(c, gg, "median_paired_difference_CO2_minus_coguest", "median_bootstrap_95_low", "median_bootstrap_95_high", "y",
                       INTERVENTION_COLOR[inter], offset=off)
    c.set_yticks(range(len(rows)), [f"{_comparison_label(co)} · {reg}" for co, reg in rows]); c.invert_yaxis()
    c.set_xlabel(r"Paired $\mathrm{CO_2}$ minus co-guest · $|\Delta\log q|$")
    clean_axis(c, "x")

    title_left(d, "High-pressure pre-combustion boundary"); panel_label(d, "D")
    bd = guest[(guest.comparison == "pre_combustion_CO2_vs_H2") & (guest.regime == "high") &
               (((guest.quantity == "adsorption_separation") & (guest.measure == "absolute_log_difference")) |
                ((guest.quantity == "heat_contrast") & (guest.measure == "absolute_hoa_difference")))].copy()
    bd["quantity_label"] = np.where(bd.quantity.eq("adsorption_separation"), "Adsorption", "Energetic")
    short_inter = {"linker_family_change": "Linker", "metal_substitution": "Metal"}
    bd["row_label"] = [f"{short_inter[i]} · {q}" for i, q in zip(bd.intervention, bd.quantity_label)]
    q_order = [("linker_family_change", "Adsorption"), ("metal_substitution", "Adsorption"),
               ("linker_family_change", "Energetic"), ("metal_substitution", "Energetic")]
    bd["_order"] = [q_order.index((i, q)) for i, q in zip(bd.intervention, bd.quantity_label)]
    bd = bd.sort_values("_order").reset_index(drop=True); bd["y"] = np.arange(len(bd))
    d.axvline(0, color=COLORS["control"], lw=0.85)
    for _, r in bd.iterrows():
        col = INTERVENTION_COLOR[r.intervention]
        _errorbar_rows(d, pd.DataFrame([r]), "median_paired_difference_CO2_minus_coguest", "median_bootstrap_95_low", "median_bootstrap_95_high", "y", col, ms=5.3)
    d.set_yticks(bd.y, bd.row_label); d.invert_yaxis()
    d.set_xlabel(r"Paired $\mathrm{CO_2}$ minus $\mathrm{H_2}$ difference")
    clean_axis(d, "x")

    fig.legend(handles=[
        Line2D([0], [0], marker="o", color="none", markerfacecolor="white", markeredgecolor=COLORS["control"], markersize=7, label="Low pressure"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORS["control"], markeredgecolor=COLORS["control"], markersize=7, label="High pressure"),
        *legend_handles_interventions(False),
    ], frameon=False, ncol=4, loc="lower center", bbox_to_anchor=(0.59, 0.010), columnspacing=1.5)
    fig.subplots_adjust(left=0.205, right=0.985, top=0.94, bottom=0.115)
    fig_dir = OUT_MAIN / "Figure_03"; fig_dir.mkdir(parents=True, exist_ok=True)
    outputs = save_figure(fig, fig_dir / "Figure_03"); plt.close(fig)
    pA = write_panel_source(link[["target", "p/bar_low", "p/bar_high", "median_adsorption_low", "median_adsorption_high"]], fig_dir, "A")
    pB = write_panel_source(link[["target", "p/bar_low", "p/bar_high", "median_heat_low", "median_heat_high"]], fig_dir, "B")
    pC = write_panel_source(g, fig_dir, "C"); pD = write_panel_source(bd.drop(columns=["_order"]), fig_dir, "D")
    inputs = [DATA_MAIN / "04_heat_adsorption_pressure_results.csv", DATA_MAIN / "04_05_results.csv"]
    write_manifest(fig_dir, "Figure_03", inputs, outputs, [pA, pB, pC, pD], {"boundary": "plots chemistry-associated separation, not raw uptake"})
    return outputs


def _process_concordance_panel(ax, df, metric, title, letter):
    title_left(ax, title); panel_label(ax, letter)
    g = df[(df.metric == metric) & df.intervention.isin(["linker_family_change", "metal_substitution"])].copy()
    proc_order = ["landfill-gas-vpsa", "methane-storage-psa", "natural-gas-purification", "post-combustion-vsa", "pre-combustion-40-40"]
    if metric == "uptake_selectivity_concordant":
        proc_order = [p for p in proc_order if p != "methane-storage-psa"]
    ymap = {p: i for i, p in enumerate(proc_order)}
    g = g[g.process.isin(proc_order)]; g["y"] = g.process.map(ymap)
    for inter, off in [("linker_family_change", -0.14), ("metal_substitution", 0.14)]:
        gg = g[g.intervention == inter].sort_values("y")
        _errorbar_rows(ax, gg, "estimate", "bootstrap_95_low", "bootstrap_95_high", "y", INTERVENTION_COLOR[inter], offset=off, ms=5.2)
    ax.set_yticks(range(len(proc_order)), [PROCESS_LABEL[p] for p in proc_order]); ax.invert_yaxis()
    ax.set_xlim(0.6, 1.0); ax.set_xlabel("Concordance fraction"); clean_axis(ax, "x")
    return g


def _selected_case_dumbbell(ax, data, value_col, proc_order, title, letter, symlog=False):
    title_left(ax, title); panel_label(ax, letter); ax.axvline(0, color=COLORS["control"], lw=0.85)
    styles = {
        "strong_linker_process_aligned": (COLORS["linker"], "D", "Process-aligned linker case"),
        "process_discordant_comparison": (COLORS["control"], "s", "Process-discordant linker case"),
    }
    ymap = {p: i for i, p in enumerate(proc_order)}
    for p in proc_order:
        row = data[data.process == p]
        vals = {}
        for cat in styles:
            rr = row[row.selection_category == cat]
            if not rr.empty and np.isfinite(rr.iloc[0][value_col]):
                vals[cat] = float(rr.iloc[0][value_col])
        if len(vals) == 2:
            ax.plot(list(vals.values()), [ymap[p], ymap[p]], color=COLORS["control_light"], lw=2.4, zorder=1)
    for cat, (col, mark, lab) in styles.items():
        g = data[data.selection_category == cat].sort_values("y")
        ax.plot(g[value_col], g.y, linestyle="none", marker=mark, ms=6.3, color=col, label=lab, zorder=3, clip_on=True)
    ax.set_yticks(range(len(proc_order)), [PROCESS_LABEL[p] for p in proc_order]); ax.invert_yaxis()
    if symlog:
        ax.set_xscale("symlog", linthresh=1.0, linscale=1.0, base=10)
    clean_axis(ax, "x")
    ax.margins(x=0.10)


def render_figure_04():
    apply_style(10.05)
    summary = read_main("04_process_translation_summary_final.csv")
    cases = read_main("04_02_final_case_set.csv")
    cand = read_main("04_candidate_process_results.csv")
    fig, axs = plt.subplots(2, 2, figsize=(11.7, 8.2), gridspec_kw={"wspace": 0.38, "hspace": 0.34})
    a, b, c, d = axs.ravel()
    pA = _process_concordance_panel(a, summary, "uptake_working_capacity_concordant", "Uptake → working-capacity concordance", "A")
    pB = _process_concordance_panel(b, summary, "uptake_selectivity_concordant", "Uptake → selectivity concordance", "B")

    sel = cases[cases.selection_category.isin(["strong_linker_process_aligned", "process_discordant_comparison"])][["selection_category", "role_label", "pair_key"]]
    cc = cand.merge(sel, left_on="frozen_case_pair_key", right_on="pair_key", how="inner")
    proc_order = ["landfill-gas-vpsa", "methane-storage-psa", "natural-gas-purification", "post-combustion-vsa", "pre-combustion-40-40"]
    ymap = {p: i for i, p in enumerate(proc_order)}; cc["y"] = cc.process.map(ymap)

    _selected_case_dumbbell(c, cc, "working_capacity_change_oriented_by_uptake", proc_order, "Selected cases: retained working-capacity direction", "C", symlog=False)
    c.set_xlabel("Working-capacity change oriented by uptake")

    cc_sel = cc[cc.selectivity_pair_complete.fillna(False)].copy()
    _selected_case_dumbbell(d, cc_sel, "selectivity_change_oriented_by_uptake", proc_order, "Selected cases: selectivity boundary", "D", symlog=True)
    d.set_xlabel("Selectivity change oriented by uptake · symlog scale")

    case_handles = [
        Line2D([0], [0], marker="D", linestyle="none", color=COLORS["linker"], markersize=6.5, label="Process-aligned linker case"),
        Line2D([0], [0], marker="s", linestyle="none", color=COLORS["control"], markersize=7, label="Process-discordant linker case"),
    ]
    fig.legend(handles=legend_handles_interventions(False) + case_handles, frameon=False, ncol=4,
               loc="lower center", bbox_to_anchor=(0.59, 0.010), columnspacing=1.6, handletextpad=0.5)

    fig.subplots_adjust(left=0.205, right=0.985, top=0.95, bottom=0.125)
    fig_dir = OUT_MAIN / "Figure_04"; fig_dir.mkdir(parents=True, exist_ok=True)
    outputs = save_figure(fig, fig_dir / "Figure_04"); plt.close(fig)
    sA = write_panel_source(pA, fig_dir, "A"); sB = write_panel_source(pB, fig_dir, "B")
    sC = write_panel_source(cc[["selection_category", "role_label", "process", "working_capacity_change_oriented_by_uptake", "uptake_working_capacity_concordant"]], fig_dir, "C")
    sD = write_panel_source(cc_sel[["selection_category", "role_label", "process", "selectivity_change_oriented_by_uptake", "uptake_selectivity_concordant"]], fig_dir, "D")
    inputs = [DATA_MAIN / "04_process_translation_summary_final.csv", DATA_MAIN / "04_02_final_case_set.csv", DATA_MAIN / "04_candidate_process_results.csv"]
    write_manifest(fig_dir, "Figure_04", inputs, outputs, [sA, sB, sC, sD], {"science": "process translation; old robustness dashboard moved to SI"})
    return outputs


def render_figure_06():
    apply_style(9.7)
    stats = read_raspa("final_pair_statistics.csv")
    modes = ["henry_full", "gcmc_0p1bar", "gcmc_1bar"]
    mode_lab = {"henry_full": "Henry", "gcmc_0p1bar": "0.1 bar", "gcmc_1bar": "1 bar"}
    mode_color = {"henry_full": COLORS["raspa_full"], "gcmc_0p1bar": COLORS["vdw"], "gcmc_1bar": COLORS["co2"]}
    pair_order = ["A1", "A2", "A3", "A4", "B1", "B2", "C1", "C2"]
    roles = stats[["pair_id", "role", "group"]].drop_duplicates().set_index("pair_id")

    fig, axs = plt.subplots(2, 2, figsize=(11.8, 9.0), gridspec_kw={"wspace": 0.32, "hspace": 0.35})
    a, b, c, d = axs.ravel()

    title_left(a, "Full-model contrast across loading regimes"); panel_label(a, "A")
    a.axvline(0, color=COLORS["control"], lw=0.85)
    yy = np.arange(len(pair_order))
    offsets = {"henry_full": -0.18, "gcmc_0p1bar": 0, "gcmc_1bar": 0.18}
    markers = {"henry_full": "o", "gcmc_0p1bar": "s", "gcmc_1bar": "^"}
    for mode in modes:
        g = stats[(stats["mode"] == mode) & stats.pair_id.isin(pair_order)].set_index("pair_id").loc[pair_order].reset_index()
        col = mode_color[mode]
        a.errorbar(
            g.signed_log2_A_over_B, yy + offsets[mode],
            xerr=[g.signed_log2_A_over_B - g.approx_95ci_log2_low, g.approx_95ci_log2_high - g.signed_log2_A_over_B],
            fmt=markers[mode], ms=5.3, color=col, ecolor=col, capsize=2.2, lw=1.05,
            label=mode_lab[mode], zorder=3,
        )
    a.set_yticks(yy, [ROLE_LABEL.get(roles.loc[p, "role"], p) for p in pair_order]); a.invert_yaxis()
    a.set_xlabel(r"Signed $\log_2(A/B)$"); clean_axis(a, "x")
    a.legend(frameon=False, loc="upper left", borderaxespad=0.35, ncol=1, handletextpad=0.5, labelspacing=0.4)

    title_left(b, "Henry versus finite-pressure consistency"); panel_label(b, "B")
    h = stats[stats["mode"] == "henry_full"].set_index("pair_id")
    for mode, mark in [("gcmc_0p1bar", "s"), ("gcmc_1bar", "^")]:
        g = stats[stats["mode"] == mode].set_index("pair_id")
        x = h.loc[pair_order, "signed_log2_A_over_B"].to_numpy()
        yv = g.loc[pair_order, "signed_log2_A_over_B"].to_numpy()
        b.scatter(x, yv, s=46, marker=mark, facecolor="white", edgecolor=mode_color[mode], lw=1.35, label=mode_lab[mode], zorder=3)
        if mode == "gcmc_1bar":
            offsets_text = {
                "A1": (5, 4), "A3": (-16, -12), "A4": (-14, -12),
                "B1": (5, 4), "C1": (5, 4),
            }
            for p, xx, yyv in zip(pair_order, x, yv):
                if p not in offsets_text:
                    continue
                dx, dy = offsets_text[p]
                b.annotate(p, (xx, yyv), xytext=(dx, dy), textcoords="offset points",
                           fontsize=8.6, fontweight="bold", color=COLORS["ink"])
    lim = symmetric_limits(np.r_[
        h.loc[pair_order, "signed_log2_A_over_B"].to_numpy(),
        stats[stats["mode"].isin(["gcmc_0p1bar", "gcmc_1bar"])].signed_log2_A_over_B.to_numpy(),
    ], pad=0.18)
    b.plot(lim, lim, "--", color=COLORS["control"], lw=1.0)
    b.axhline(0, color=COLORS["grid"], lw=0.85); b.axvline(0, color=COLORS["grid"], lw=0.85)
    b.set_xlim(lim); b.set_ylim(lim)
    b.set_xlabel(r"Henry signed $\log_2(A/B)$")
    b.set_ylabel(r"Finite-pressure signed $\log_2(A/B)$")
    clean_axis(b, None)

    title_left(c, "Electrostatic sensitivity at Henry limit"); panel_label(c, "C")
    c.axvline(0, color=COLORS["control"], lw=0.85)
    hf = stats[stats["mode"] == "henry_full"].set_index("pair_id").loc[pair_order]
    hc = stats[stats["mode"] == "henry_chargeoff"].set_index("pair_id").loc[pair_order]
    for yi, p in enumerate(pair_order):
        line_col = COLORS["metal_light"] if p == "A4" else COLORS["control_light"]
        line_w = 3.0 if p == "A4" else 2.6
        c.plot([hc.loc[p, "signed_log2_A_over_B"], hf.loc[p, "signed_log2_A_over_B"]], [yi, yi], color=line_col, lw=line_w, solid_capstyle="round")
    c.scatter(hc.signed_log2_A_over_B, np.arange(len(pair_order)), s=46, facecolor="white", edgecolor=COLORS["raspa_chargeoff"], lw=1.35, label="Charge off", zorder=3)
    c.scatter(hf.signed_log2_A_over_B, np.arange(len(pair_order)), s=46, color=COLORS["raspa_full"], label="Full", zorder=3)
    c.set_yticks(range(len(pair_order)), pair_order); c.invert_yaxis()
    c.set_xlabel(r"Signed $\log_2(A/B)$"); clean_axis(c, "x")
    c.legend(frameon=False, loc="lower right", borderaxespad=0.4, ncol=1, handletextpad=0.5, labelspacing=0.4)

    title_left(d, "Energy decomposition at 1 bar"); panel_label(d, "D")
    d.axhline(0, color=COLORS["control"], lw=0.85)
    selected = ["A1", "A3", "A4", "B1"]
    g = stats[(stats["mode"] == "gcmc_1bar") & stats.pair_id.isin(selected)].set_index("pair_id").loc[selected]
    x = np.arange(len(selected)); w = 0.20
    d.bar(x - w, g.delta_vdw_energy_B_minus_A_K_per_CO2, width=w, color=COLORS["vdw"], edgecolor=COLORS["raspa_full"], linewidth=0.9, label="VDW")
    d.bar(x, g.delta_coulomb_energy_B_minus_A_K_per_CO2, width=w, color=COLORS["metal_light"], edgecolor=COLORS["coulomb"], linewidth=0.9, label="Coulomb")
    d.bar(x + w, g.delta_total_energy_B_minus_A_K_per_CO2, width=w, color=COLORS["control_light"], edgecolor=COLORS["total"], linewidth=0.9, label="Total")
    d.set_xticks(x, selected)
    d.set_ylabel(r"$\Delta$ energy B−A (K per $\mathrm{CO_2}$)")
    clean_axis(d, "y")
    ymin, ymax = d.get_ylim()
    d.set_ylim(ymin, ymax + 0.18 * (ymax - ymin))
    d.legend(frameon=False, ncol=3, loc="upper center", borderaxespad=0.35, columnspacing=1.0, handletextpad=0.4)

    fig.subplots_adjust(left=0.19, right=0.985, top=0.94, bottom=0.085)
    fig_dir = OUT_MAIN / "Figure_06"; fig_dir.mkdir(parents=True, exist_ok=True)
    outputs = save_figure(fig, fig_dir / "Figure_06"); plt.close(fig)
    sA = write_panel_source(stats[(stats["mode"].isin(modes)) & stats.pair_id.isin(pair_order)], fig_dir, "A")
    sB = write_panel_source(stats[(stats["mode"].isin(["henry_full", "gcmc_0p1bar", "gcmc_1bar"])) & stats.pair_id.isin(pair_order)], fig_dir, "B")
    sC = write_panel_source(stats[(stats["mode"].isin(["henry_full", "henry_chargeoff"])) & stats.pair_id.isin(pair_order)], fig_dir, "C")
    sD = write_panel_source(g.reset_index(), fig_dir, "D")
    inputs = [DATA_RASPA / "final_pair_statistics.csv"]
    write_manifest(fig_dir, "Figure_06", inputs, outputs, [sA, sB, sC, sD], {"raspa": "RASPA 3.0.29 frozen closure results; six structural cases + two linker comparators; no density map"})
    return outputs


def render_all_main():
    outputs = []
    for fn in [render_figure_01, render_figure_02, render_figure_03, render_figure_04, render_figure_06]:
        outputs.extend(fn())
    return outputs
