from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

from .style import (
    apply_style, clean_axis, panel_label, title_left, save_figure,
    COLORS, INTERVENTION_COLOR, INTERVENTION_LABEL, TARGET_LABEL, TARGET_ORDER,
    legend_handles_interventions,
)
from .utils import (
    DATA_SI, DATA_MAIN, DATA_RASPA, OUT_SI, read_si, read_main, read_raspa,
    ordered_conditions, write_panel_source, write_manifest,
)


def _errorbar_rows(ax, df, x, lo, hi, y, color, marker="o", label=None,
                   offset=0.0, ms=4.8, open_marker=False):
    yy = np.asarray(df[y] if isinstance(y, str) else y, dtype=float) + offset
    face = "white" if open_marker else color
    xv = df[x].to_numpy(dtype=float); lov = df[lo].to_numpy(dtype=float); hiv = df[hi].to_numpy(dtype=float)
    ax.errorbar(
        xv, yy, xerr=[xv - lov, hiv - xv], fmt=marker,
        color=color, ecolor=color, elinewidth=1.1, capsize=2.2,
        ms=ms, markerfacecolor=face, markeredgewidth=1.0,
        label=label, zorder=3,
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


def render_s01():
    apply_style(9.25)
    p = read_si("controls_primary__step3_same_chemistry_control_results.csv")
    s = read_si("controls_symmetric__step5b_symmetric_control_results.csv")
    ints = ["linker_family_change", "metal_substitution", "functional_motif_change"]
    specs = [
        ("A", r"Primary design · $|\Delta\log q|$", p[p.effect_measure == "absolute_log_difference"].copy()),
        ("B", r"Primary design · standardized $|\Delta q|$", p[p.effect_measure == "standardized_absolute_difference"].copy()),
        ("C", r"Symmetric design · standardized $|\Delta q|$", s[s.effect_measure == "standardized_absolute_difference"].copy()),
    ]
    cond = _condition_table(specs[0][2]); key = ["target", "T/K", "p/bar"]
    ymap = {tuple(r[k] for k in key): i for i, r in cond.iterrows()}
    fig, axs = plt.subplots(1, 3, figsize=(14.1, 7.6), gridspec_kw={"wspace": 0.22})
    panel_sources = []
    for idx, (letter, title, df) in enumerate(specs):
        ax = axs[idx]; title_left(ax, title); panel_label(ax, letter); ax.axvline(0, color=COLORS["control"], lw=0.85)
        df = df[df.intervention.isin(ints)].copy(); df["y"] = [ymap[tuple(r[k] for k in key)] for _, r in df.iterrows()]
        for inter, off in zip(ints, [-0.20, 0, 0.20]):
            g = df[df.intervention == inter].sort_values("y")
            _errorbar_rows(ax, g, "median_chemistry_minus_control", "bootstrap_95_low", "bootstrap_95_high", "y",
                           INTERVENTION_COLOR[inter], offset=off, ms=4.5)
        ax.set_xlabel("Chemistry minus control")
        if idx == 0:
            ax.set_yticks(range(len(cond)), cond.condition_label)
        else:
            ax.set_yticks(range(len(cond)), [])
        ax.set_ylim(len(cond) - 0.5, -0.5); clean_axis(ax, "x")
        panel_sources.append(df)
    fig.legend(handles=legend_handles_interventions(True), frameon=False, ncol=3,
               loc="lower center", bbox_to_anchor=(0.60, 0.014), columnspacing=1.6)
    fig.subplots_adjust(left=0.19, right=0.99, top=0.93, bottom=0.11)
    fig_dir = OUT_SI / "Figure_S01"; fig_dir.mkdir(parents=True, exist_ok=True)
    outputs = save_figure(fig, fig_dir / "Figure_S01_Additional_Controls"); plt.close(fig)
    src = [write_panel_source(df, fig_dir, l) for (l, _, _), df in zip(specs, panel_sources)]
    inputs = [DATA_SI / "controls_primary__step3_same_chemistry_control_results.csv", DATA_SI / "controls_symmetric__step5b_symmetric_control_results.csv"]
    write_manifest(fig_dir, "Figure_S01", inputs, outputs, src, {"purpose": "additional control-scale and exploratory motif detail"})
    return outputs


def render_s02():
    apply_style(9.2)
    hoa = read_si("hoa_condition__heat_adsorption_condition_results.csv")
    hp = read_si("hoa_pressure__heat_adsorption_pressure_results.csv")
    ints = ["linker_family_change", "metal_substitution"]
    absd = hoa[(hoa.effect_measure == "absolute_log_difference") & hoa.intervention.isin(ints)].copy()
    stdd = hoa[(hoa.effect_measure == "standardized_absolute_difference") & hoa.intervention.isin(ints)].copy()
    cond = _condition_table(absd); key = ["target", "T/K", "p/bar"]
    ymap = {tuple(r[k] for k in key): i for i, r in cond.iterrows()}
    for df in [absd, stdd]:
        df["y"] = [ymap[tuple(r[k] for k in key)] for _, r in df.iterrows()]
    press = hp[(hp.effect_measure == "absolute_log_difference") & hp.intervention.isin(ints)].copy()
    rank = {t: i for i, t in enumerate(TARGET_ORDER)}; press["y"] = press.target.map(rank); press = press.sort_values("y")

    fig, axs = plt.subplots(2, 2, figsize=(12.2, 9.25), gridspec_kw={"wspace": 0.22, "hspace": 0.27})
    a, b, c, d = axs.ravel()
    for ax in [a, b, d]:
        ax.axvline(0, color=COLORS["control"], lw=0.85)

    title_left(a, r"HOA association · absolute-log separation"); panel_label(a, "A")
    for inter, off in [("linker_family_change", -0.15), ("metal_substitution", 0.15)]:
        g = absd[absd.intervention == inter].sort_values("y")
        _errorbar_rows(a, g, "spearman_rho_heat_vs_adsorption_separation", "bootstrap_95_low_rho", "bootstrap_95_high_rho", "y", INTERVENTION_COLOR[inter], offset=off)
    a.set_yticks(range(len(cond)), cond.condition_label); a.set_ylim(len(cond) - 0.5, -0.5)
    a.set_xlabel(r"Spearman $\rho$"); clean_axis(a, "x")

    title_left(b, r"HOA association · standardized separation"); panel_label(b, "B")
    for inter, off in [("linker_family_change", -0.15), ("metal_substitution", 0.15)]:
        g = stdd[stdd.intervention == inter].sort_values("y")
        _errorbar_rows(b, g, "spearman_rho_heat_vs_adsorption_separation", "bootstrap_95_low_rho", "bootstrap_95_high_rho", "y", INTERVENTION_COLOR[inter], offset=off)
    b.set_yticks(range(len(cond)), []); b.set_ylim(len(cond) - 0.5, -0.5)
    b.set_xlabel(r"Spearman $\rho$"); clean_axis(b, "x")

    title_left(c, "Median energetic contrast by condition"); panel_label(c, "C")
    for inter, off in [("linker_family_change", -0.15), ("metal_substitution", 0.15)]:
        g = absd[absd.intervention == inter].sort_values("y")
        _errorbar_rows(c, g, "median_absolute_hoa_difference", "bootstrap_95_low_absolute_hoa_difference", "bootstrap_95_high_absolute_hoa_difference", "y", INTERVENTION_COLOR[inter], offset=off)
    c.set_yticks(range(len(cond)), cond.condition_label); c.set_ylim(len(cond) - 0.5, -0.5)
    c.set_xlabel(r"Median $|\Delta HOA|$"); clean_axis(c, "x")

    title_left(d, "Pressure-change energetic/adsorption association"); panel_label(d, "D")
    for inter, off in [("linker_family_change", -0.15), ("metal_substitution", 0.15)]:
        g = press[press.intervention == inter].sort_values("y")
        _errorbar_rows(d, g, "spearman_rho_pressure_change_heat_vs_adsorption", "bootstrap_95_low_rho", "bootstrap_95_high_rho", "y", INTERVENTION_COLOR[inter], offset=off)
    targets = [t for t in TARGET_ORDER if t in set(press.target)]
    d.set_yticks([rank[t] for t in targets], [TARGET_LABEL[t] for t in targets]); d.set_ylim(max(rank.values()) + 0.5, -0.5)
    d.set_xlabel(r"Spearman $\rho$ of pressure-induced changes"); clean_axis(d, "x")

    fig.legend(handles=legend_handles_interventions(False), frameon=False, ncol=2,
               loc="lower center", bbox_to_anchor=(0.60, 0.014), columnspacing=1.7)
    fig.subplots_adjust(left=0.22, right=0.985, top=0.94, bottom=0.10)
    fig_dir = OUT_SI / "Figure_S02"; fig_dir.mkdir(parents=True, exist_ok=True)
    outputs = save_figure(fig, fig_dir / "Figure_S02_HOA_Associations"); plt.close(fig)
    src = [write_panel_source(x, fig_dir, l) for x, l in [(absd, "A"), (stdd, "B"), (absd, "C"), (press, "D")]]
    inputs = [DATA_SI / "hoa_condition__heat_adsorption_condition_results.csv", DATA_SI / "hoa_pressure__heat_adsorption_pressure_results.csv"]
    write_manifest(fig_dir, "Figure_S02", inputs, outputs, src, {"interpretation": "energetic coordinate; not a resolved mechanism"})
    return outputs


def render_s03():
    apply_style(9.3)
    guest = read_si("guest__05_results.csv")
    hp = read_si("hoa_pressure__heat_adsorption_pressure_results.csv")
    comp_order = ["landfill_CO2_vs_CH4", "methane_purification_CO2_vs_CH4", "post_combustion_CO2_vs_N2", "pre_combustion_CO2_vs_H2"]
    rows = [(co, reg) for co in comp_order for reg in ["low", "high"]]; ymap = {x: i for i, x in enumerate(rows)}
    std = guest[(guest.quantity == "adsorption_separation") & (guest.measure == "standardized_absolute_difference")].copy()
    std["y"] = [ymap[(r.comparison, r.regime)] for _, r in std.iterrows()]
    en = guest[(guest.quantity == "heat_contrast") & (guest.measure == "absolute_hoa_difference")].copy()
    en["y"] = [ymap[(r.comparison, r.regime)] for _, r in en.iterrows()]
    p = hp[hp.effect_measure == "absolute_log_difference"].copy(); rank = {t: i for i, t in enumerate(TARGET_ORDER)}; p["y"] = p.target.map(rank)

    fig, axs = plt.subplots(2, 2, figsize=(12.1, 8.45), gridspec_kw={"wspace": 0.34, "hspace": 0.33})
    a, b, c, d = axs.ravel()
    for ax in axs.ravel():
        ax.axvline(0, color=COLORS["control"], lw=0.85)

    title_left(a, r"$\mathrm{CO_2}$ minus co-guest · standardized separation"); panel_label(a, "A")
    for inter, off in [("linker_family_change", -0.15), ("metal_substitution", 0.15)]:
        g = std[std.intervention == inter].sort_values("y")
        _errorbar_rows(a, g, "median_paired_difference_CO2_minus_coguest", "median_bootstrap_95_low", "median_bootstrap_95_high", "y", INTERVENTION_COLOR[inter], offset=off)
    a.set_yticks(range(len(rows)), [f"{_comparison_label(co)} · {reg}" for co, reg in rows]); a.set_ylim(len(rows) - 0.5, -0.5)
    a.set_xlabel("Paired difference"); clean_axis(a, "x")

    title_left(b, r"$\mathrm{CO_2}$ minus co-guest · energetic contrast"); panel_label(b, "B")
    for inter, off in [("linker_family_change", -0.15), ("metal_substitution", 0.15)]:
        g = en[en.intervention == inter].sort_values("y")
        _errorbar_rows(b, g, "median_paired_difference_CO2_minus_coguest", "median_bootstrap_95_low", "median_bootstrap_95_high", "y", INTERVENTION_COLOR[inter], offset=off)
    b.set_yticks(range(len(rows)), []); b.set_ylim(len(rows) - 0.5, -0.5)
    b.set_xlabel(r"Paired difference in $|\Delta HOA|$"); clean_axis(b, "x")

    for ax, inter, letter, title in [
        (c, "linker_family_change", "C", "Pressure-change association · linker"),
        (d, "metal_substitution", "D", "Pressure-change association · metal"),
    ]:
        title_left(ax, title); panel_label(ax, letter)
        g = p[p.intervention == inter].sort_values("y")
        _errorbar_rows(ax, g, "spearman_rho_pressure_change_heat_vs_adsorption", "bootstrap_95_low_rho", "bootstrap_95_high_rho", "y", INTERVENTION_COLOR[inter], ms=5.0)
        targets = [t for t in TARGET_ORDER if t in set(g.target)]
        ax.set_yticks([rank[t] for t in targets], [TARGET_LABEL[t] for t in targets] if ax is c else [])
        ax.set_ylim(max(rank.values()) + 0.5, -0.5); ax.set_xlabel(r"Spearman $\rho$"); clean_axis(ax, "x")

    fig.legend(handles=legend_handles_interventions(False), frameon=False, ncol=2,
               loc="lower center", bbox_to_anchor=(0.60, 0.012), columnspacing=1.7)
    fig.subplots_adjust(left=0.205, right=0.985, top=0.94, bottom=0.10)
    fig_dir = OUT_SI / "Figure_S03"; fig_dir.mkdir(parents=True, exist_ok=True)
    outputs = save_figure(fig, fig_dir / "Figure_S03_Guest_Pressure_Specificity"); plt.close(fig)
    src = [write_panel_source(x, fig_dir, l) for x, l in [(std, "A"), (en, "B"), (p[p.intervention == "linker_family_change"], "C"), (p[p.intervention == "metal_substitution"], "D")]]
    inputs = [DATA_SI / "guest__05_results.csv", DATA_SI / "hoa_pressure__heat_adsorption_pressure_results.csv"]
    write_manifest(fig_dir, "Figure_S03", inputs, outputs, src, {"note": "paired process-regime comparisons; not equal-pressure thermodynamic comparisons"})
    return outputs


def render_s04():
    apply_style(9.2)
    rec = read_si("04_reciprocal_covariance_matching_summary.csv")
    top = read_si("04_step1_topology_robustness_summary.csv")
    bal = read_si("balance__04_balance.csv")
    res = read_si("04_step2_residual_geometry_summary.csv")
    fam = read_si("family__04_family_exclusion_summary.csv")
    adj = read_si("adjustment__03_results.csv")
    fig, axs = plt.subplots(3, 2, figsize=(12.25, 10.8), gridspec_kw={"wspace": 0.35, "hspace": 0.38})
    a, b, c, d, e, f = axs.ravel()

    title_left(a, "Reciprocal covariance matching"); panel_label(a, "A")
    order = ["linker_family_change", "metal_substitution", "functional_motif_change"]
    rr = rec.set_index("intervention").loc[order].reset_index(); y = np.arange(3)[::-1]
    for yi, (_, r) in zip(y, rr.iterrows()):
        a.barh(yi, r.selected_fraction, color=INTERVENTION_COLOR[r.intervention], height=0.34)
        a.text(r.selected_fraction + 0.018, yi, f"{100*r.selected_fraction:.1f}% · {int(r.selected_pairs):,}", va="center", fontsize=8.8, fontweight="bold")
    a.set_yticks(y, [INTERVENTION_LABEL[i] for i in order]); a.set_xlim(0, 1.16)
    a.set_xlabel("Selected fraction of stringent pairs"); clean_axis(a, "x")

    title_left(b, "Topology-robust pressure directions"); panel_label(b, "B")
    x = np.arange(len(top)); w = 0.18
    b.bar(x - w/2, top.same_log_pressure_direction/top.comparisons, width=w, color=COLORS["raspa_full"], label="Absolute-log")
    b.bar(x + w/2, top.same_standardized_pressure_direction/top.comparisons, width=w, color=COLORS["co2"], label="Standardized")
    b.set_ylim(0.85, 1.035); b.set_xticks(x, ["Exact metal change", "Intervention class"])
    b.set_ylabel("Direction agreement fraction"); clean_axis(b, "y")
    b.legend(frameon=False, loc="upper center", borderaxespad=0.35, ncol=2, columnspacing=1.0, handletextpad=0.45)

    title_left(c, "Chemistry-versus-control geometry balance"); panel_label(c, "C")
    bb = bal[bal.intervention.isin(["linker_family_change", "metal_substitution"])].copy()
    geom_order = ["Di_diff", "Df_diff", "Dif_diff", "Density_diff", "UC_volume_diff", "AVAf_diff", "POAVAf_diff"]
    glab = {"Di_diff": "Di", "Df_diff": "Df", "Dif_diff": "Dif", "Density_diff": "Density", "UC_volume_diff": "Cell volume", "AVAf_diff": "AVAf", "POAVAf_diff": "POAVAf"}
    yy = np.arange(len(geom_order))
    for inter, off in [("linker_family_change", -0.16), ("metal_substitution", 0.16)]:
        g = bb[bb.intervention == inter].set_index("geometry_variable").loc[geom_order]
        c.barh(yy + off, g.absolute_global_smd, height=0.27, color=INTERVENTION_COLOR[inter])
    c.axvline(0.2, color=COLORS["control"], ls="--", lw=1.0)
    c.set_yticks(yy, [glab[g] for g in geom_order]); c.invert_yaxis(); c.set_xlabel("|Global SMD|"); clean_axis(c, "x")

    title_left(d, "Residual-geometry association summary"); panel_label(d, "D")
    effect_order = ["absolute_log_difference", "absolute_uptake_difference", "standardized_absolute_difference"]
    elab = {"absolute_log_difference": r"$|\Delta\log q|$", "absolute_uptake_difference": r"$|\Delta q|$", "standardized_absolute_difference": r"Standardized $|\Delta q|$"}
    rr2 = res[res.intervention.isin(["linker_family_change", "metal_substitution"])].copy(); xx = np.arange(len(effect_order))
    for inter, off in [("linker_family_change", -0.17), ("metal_substitution", 0.17)]:
        g = rr2[rr2.intervention == inter].set_index("effect_measure").loc[effect_order]
        d.bar(xx + off, g.median_absolute_rho, width=0.22, color=INTERVENTION_COLOR[inter], alpha=0.96)
        d.scatter(xx + off, g.maximum_absolute_rho, s=30, facecolor="white", edgecolor=INTERVENTION_COLOR[inter], linewidth=1.1, zorder=3)
    d.set_xticks(xx, [elab[x] for x in effect_order], rotation=8); d.set_ylabel(r"$|\mathrm{Spearman}\ \rho|$"); clean_axis(d, "y")
    d.set_ylim(0, max(0.31, float(rr2.maximum_absolute_rho.max()) * 1.12))
    d.legend(handles=[
        Line2D([0], [0], color=COLORS["control"], lw=6, label=r"Median $|\rho|$"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="white", markeredgecolor=COLORS["control"], markersize=7, label=r"Maximum $|\rho|$"),
    ], frameon=False, loc="upper center", borderaxespad=0.35, ncol=2, columnspacing=1.0, handletextpad=0.45)

    title_left(e, "Largest-family exclusion sensitivity"); panel_label(e, "E")
    ff = fam[fam.intervention.isin(["linker_family_change", "metal_substitution"])].copy()
    ff["label"] = [f"{INTERVENTION_LABEL[i]}\n{elab[m]}" for i, m in zip(ff.intervention, ff.effect_measure)]
    y2 = np.arange(len(ff))[::-1]
    e.barh(y2, 100 * ff.max_abs_relative_change_excluding_top10, color=[INTERVENTION_COLOR[i] for i in ff.intervention], height=0.38)
    e.set_yticks(y2, ff.label); e.set_xlabel("Maximum |relative change| after excluding top 10 families (%)"); clean_axis(e, "x")

    title_left(f, "Standardized linker adjustment sensitivity"); panel_label(f, "F")
    f.axvline(0, color=COLORS["control"], lw=0.85)
    aa = adj[adj.effect_measure == "standardized_absolute_difference"].copy().sort_values("relative_adjustment_change")
    yy2 = np.arange(len(aa)); vals = 100 * aa.relative_adjustment_change
    f.scatter(vals, yy2, s=36, color=COLORS["linker"], zorder=3)
    med = float(vals.median())
    f.axvline(med, color=COLORS["linker"], ls="--", lw=1.15)
    f.set_yticks([]); f.set_xlabel("Relative change after seven-variable adjustment (%)"); clean_axis(f, "x")
    f.annotate(f"median {med:.1f}%", xy=(med, len(aa)*0.88), xytext=(7, 0), textcoords="offset points", color=COLORS["linker"], fontsize=8.8, fontweight="bold", va="center")

    # One intervention legend for panels A/C/D/E; panel-specific legends remain above B/D.
    fig.legend(handles=legend_handles_interventions(True), frameon=False, ncol=3,
               loc="lower center", bbox_to_anchor=(0.60, 0.008), columnspacing=1.5)
    fig.subplots_adjust(left=0.18, right=0.985, top=0.95, bottom=0.085)
    fig_dir = OUT_SI / "Figure_S04"; fig_dir.mkdir(parents=True, exist_ok=True)
    outputs = save_figure(fig, fig_dir / "Figure_S04_Robustness_Geometry_Sensitivity"); plt.close(fig)
    src = [write_panel_source(x, fig_dir, l) for x, l in [(rr, "A"), (top, "B"), (bb, "C"), (rr2, "D"), (ff, "E"), (aa, "F")]]
    inputs = [DATA_SI / "04_reciprocal_covariance_matching_summary.csv", DATA_SI / "04_step1_topology_robustness_summary.csv", DATA_SI / "balance__04_balance.csv", DATA_SI / "04_step2_residual_geometry_summary.csv", DATA_SI / "family__04_family_exclusion_summary.csv", DATA_SI / "adjustment__03_results.csv"]
    write_manifest(fig_dir, "Figure_S04", inputs, outputs, src, {"purpose": "old audit-style robustness evidence consolidated into SI"})
    return outputs


def render_s05():
    apply_style(9.6)
    cases = read_main("04_02_final_case_set.csv")
    cand = read_main("04_candidate_process_results.csv")
    geom_cols = ["fraction_Di_diff", "fraction_Df_diff", "fraction_Dif_diff", "fraction_Density_diff", "fraction_UC_volume_diff", "fraction_AVAf_diff", "fraction_POAVAf_diff"]
    glab = ["Di", "Df", "Dif", "Density", "Cell volume", "AVAf", "POAVAf"]
    uniq = cand.drop_duplicates("frozen_case_pair_key")[["frozen_case_pair_key", "maximum_fraction_of_limit"] + geom_cols]
    d = cases[["selection_category", "role_label", "pair_key"]].merge(uniq, left_on="pair_key", right_on="frozen_case_pair_key", how="left")
    arr = d[geom_cols].to_numpy(float)
    cmap = LinearSegmentedColormap.from_list("geom", ["#FFFFFF", COLORS["linker_light"], COLORS["linker"]])
    fig, axs = plt.subplots(1, 2, figsize=(11.8, 5.7), gridspec_kw={"width_ratios": [1.48, 1.0], "wspace": 0.32})
    a, b = axs

    title_left(a, "Selected-case geometry differences relative to primary calipers"); panel_label(a, "A", x=-0.07)
    im = a.imshow(arr, aspect="auto", vmin=0, vmax=max(1, float(np.nanmax(arr))), cmap=cmap)
    a.set_xticks(range(len(glab)), glab, rotation=22, ha="right"); a.set_yticks(range(len(d)), d.role_label)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            if np.isfinite(arr[i, j]):
                a.text(j, i, f"{arr[i,j]:.2f}", ha="center", va="center", fontsize=8.4, color="white" if arr[i,j] > 0.65 else COLORS["ink"])
    cb = fig.colorbar(im, ax=a, orientation="horizontal", fraction=0.07, pad=0.20)
    cb.set_label("Pair difference / primary caliper")

    title_left(b, "Largest normalized geometry difference"); panel_label(b, "B")
    y = np.arange(len(d)); b.barh(y, d.maximum_fraction_of_limit, color=COLORS["linker_light"], edgecolor=COLORS["linker"], linewidth=1.0, height=0.42)
    b.axvline(1, color=COLORS["control"], ls="--", lw=1.15)
    b.set_yticks(y, []); b.invert_yaxis(); b.set_xlabel("Maximum fraction of primary caliper"); clean_axis(b, "x")
    b.annotate("primary-caliper boundary", xy=(1, -0.35), xytext=(-4, 3), textcoords="offset points", ha="right", va="bottom", color=COLORS["muted"], fontsize=8.7)

    fig.subplots_adjust(left=0.215, right=0.985, top=0.92, bottom=0.20)
    fig_dir = OUT_SI / "Figure_S05"; fig_dir.mkdir(parents=True, exist_ok=True)
    outputs = save_figure(fig, fig_dir / "Figure_S05_Structural_Geometry_Control"); plt.close(fig)
    sA = write_panel_source(d[["selection_category", "role_label"] + geom_cols], fig_dir, "A")
    sB = write_panel_source(d[["selection_category", "role_label", "maximum_fraction_of_limit"]], fig_dir, "B")
    inputs = [DATA_MAIN / "04_02_final_case_set.csv", DATA_MAIN / "04_candidate_process_results.csv"]
    write_manifest(fig_dir, "Figure_S05", inputs, outputs, [sA, sB], {"note": "companion only; main structural Figure 5 remains externally finalized"})
    return outputs


def render_s06():
    apply_style(9.25)
    st = read_raspa("final_pair_statistics.csv")
    pair_order = ["A1", "A2", "A3", "A4", "B1", "B2", "C1", "C2"]
    mode_order = ["henry_full", "henry_chargeoff", "gcmc_0p1bar", "gcmc_1bar"]
    mlab = ["Henry · full", "Henry · charge off", "0.1 bar", "1 bar"]
    piv = st.pivot(index="pair_id", columns="mode", values="signed_log2_A_over_B").reindex(index=pair_order, columns=mode_order)
    cmap = LinearSegmentedColormap.from_list("div", [COLORS["metal"], "#FFFFFF", COLORS["linker"]])
    vmax = max(abs(np.nanmin(piv.to_numpy())), abs(np.nanmax(piv.to_numpy())))
    fig, axs = plt.subplots(2, 2, figsize=(12.0, 8.7), gridspec_kw={"wspace": 0.31, "hspace": 0.30})
    a, b, c, d = axs.ravel()

    title_left(a, "Eight-pair signed adsorption contrast"); panel_label(a, "A")
    im = a.imshow(piv.to_numpy(), aspect="auto", cmap=cmap, norm=TwoSlopeNorm(vcenter=0, vmin=-vmax, vmax=vmax))
    a.set_xticks(range(len(mode_order)), mlab, rotation=16, ha="right"); a.set_yticks(range(len(pair_order)), pair_order)
    for i in range(len(pair_order)):
        for j in range(len(mode_order)):
            v = piv.iloc[i, j]
            a.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8.2, color="white" if abs(v) > 0.75 * vmax else COLORS["ink"])
    cb = fig.colorbar(im, ax=a, fraction=0.04, pad=0.025); cb.set_label(r"Signed $\log_2(A/B)$")

    title_left(b, "Full versus charge-off Henry contrast"); panel_label(b, "B"); b.axvline(0, color=COLORS["control"], lw=0.85)
    hf = st[st["mode"] == "henry_full"].set_index("pair_id").loc[pair_order]
    hc = st[st["mode"] == "henry_chargeoff"].set_index("pair_id").loc[pair_order]
    for yi, p in enumerate(pair_order):
        line_col = COLORS["metal_light"] if p == "A4" else COLORS["control_light"]
        b.plot([hc.loc[p, "signed_log2_A_over_B"], hf.loc[p, "signed_log2_A_over_B"]], [yi, yi], color=line_col, lw=2.7, solid_capstyle="round")
    b.scatter(hc.signed_log2_A_over_B, range(len(pair_order)), s=46, facecolor="white", edgecolor=COLORS["raspa_chargeoff"], lw=1.3, label="Charge off")
    b.scatter(hf.signed_log2_A_over_B, range(len(pair_order)), s=46, color=COLORS["raspa_full"], label="Full")
    b.set_yticks(range(len(pair_order)), pair_order); b.invert_yaxis(); b.set_xlabel(r"Signed $\log_2(A/B)$"); clean_axis(b, "x")
    b.legend(frameon=False, loc="lower right", bbox_to_anchor=(1.0, 1.01), borderaxespad=0.0, ncol=2)

    def energy_panel(ax, mode, letter, title):
        title_left(ax, title); panel_label(ax, letter); ax.axhline(0, color=COLORS["control"], lw=0.85)
        g = st[(st["mode"] == mode) & st.pair_id.isin(pair_order)].set_index("pair_id").loc[pair_order]
        x = np.arange(len(pair_order)); w = 0.21
        ax.bar(x - w, g.delta_vdw_energy_B_minus_A_K_per_CO2, width=w, color=COLORS["vdw"], edgecolor=COLORS["raspa_full"], linewidth=0.9, label="VDW")
        ax.bar(x, g.delta_coulomb_energy_B_minus_A_K_per_CO2, width=w, color=COLORS["metal_light"], edgecolor=COLORS["coulomb"], linewidth=0.9, label="Coulomb")
        ax.bar(x + w, g.delta_total_energy_B_minus_A_K_per_CO2, width=w, color=COLORS["control_light"], edgecolor=COLORS["total"], linewidth=0.9, label="Total")
        ax.set_xticks(x, pair_order); ax.set_ylabel(r"$\Delta$ energy B−A (K per $\mathrm{CO_2}$)"); clean_axis(ax, "y")
        return g.reset_index()

    gC = energy_panel(c, "gcmc_0p1bar", "C", "Energy decomposition · 0.1 bar")
    gD = energy_panel(d, "gcmc_1bar", "D", "Energy decomposition · 1 bar")
    ymin, ymax = d.get_ylim()
    d.set_ylim(ymin, ymax + 0.18 * (ymax - ymin))
    d.legend(frameon=False, ncol=3, loc="upper center", borderaxespad=0.35, columnspacing=1.0, handletextpad=0.4)

    fig.subplots_adjust(left=0.115, right=0.985, top=0.94, bottom=0.095)
    fig_dir = OUT_SI / "Figure_S06"; fig_dir.mkdir(parents=True, exist_ok=True)
    outputs = save_figure(fig, fig_dir / "Figure_S06_RASPA_Eight_Pair_Detail"); plt.close(fig)
    sA = write_panel_source(piv.reset_index(), fig_dir, "A")
    sB = write_panel_source(st[st["mode"].isin(["henry_full", "henry_chargeoff"])], fig_dir, "B")
    sC = write_panel_source(gC, fig_dir, "C"); sD = write_panel_source(gD, fig_dir, "D")
    inputs = [DATA_RASPA / "final_pair_statistics.csv"]
    write_manifest(fig_dir, "Figure_S06", inputs, outputs, [sA, sB, sC, sD], {"exclusions": "no RASPA density map; raw grids/generation code unavailable"})
    return outputs


def render_all_si():
    outputs = []
    for fn in [render_s01, render_s02, render_s03, render_s04, render_s05, render_s06]:
        outputs.extend(fn())
    return outputs
