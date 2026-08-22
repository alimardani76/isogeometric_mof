#!/usr/bin/env python3
"""Project 7B2 Step 3, file 07: render the six frozen structure cases.

Aggressive redesign of Figure 5.
Rendering only. No case membership, numerical values, or scientific claims are changed.

Source policy:
- Prefer analysis/final_structure_case_inspection when present in the local project.
- Otherwise fall back to the frozen handover package 08_structures subset.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

try:
    from pymatgen.io.cif import CifParser
    HAVE_PYMATGEN = True
except Exception:
    CifParser = None
    HAVE_PYMATGEN = False

try:
    import gemmi
    HAVE_GEMMI = True
except Exception:
    gemmi = None
    HAVE_GEMMI = False

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = ROOT / "Step 3 results"
CASE_DIR = RESULTS / "case_selection"
CHEM_DIR = RESULTS / "case_chemistry"
FROZEN = RESULTS / "Paper7B_Hosein_to_Shayan_Frozen_Source_Package" / "08_structures"
OUT = RESULTS / "main_figures"
OUT.mkdir(parents=True, exist_ok=True)

CASES = CASE_DIR / "02_final_case_set.csv"
ELEMENT_CHARGE = CHEM_DIR / "03_element_charge_summaries.csv"
PAIR_CHARGE = CHEM_DIR / "03_pair_charge_contrasts.csv"
P2C = ROOT / "Step 4 results" / "02_cif_chemistry" / "phase2c_case_chemistry_synthesis" / "phase2c_pair_case_chemistry_cards.csv"
P2E = ROOT / "Step 4 results" / "02_cif_chemistry" / "phase2e_chemistry_closure" / "phase2e_case_manuscript_decision_map.csv"

DPI = 600
ROLE_ORDER = [
    "strong_linker_process_aligned",
    "strong_metal_process_aligned",
    "cu_zn_pressure_exception",
    "near_null_comparison",
    "process_discordant_comparison",
    "functional_motif_example",
]
ROLE_TITLE = {
    "strong_linker_process_aligned": "Strong linker contrast",
    "strong_metal_process_aligned": "Strong metal contrast",
    "cu_zn_pressure_exception": "Cu–Zn pressure exception",
    "near_null_comparison": "Near-null linker contrast",
    "process_discordant_comparison": "Process-discordant contrast",
    "functional_motif_example": "Exploratory functional motif",
}
ROLE_NOTE = {
    "strong_linker_process_aligned": "Selected as a large linker-driven contrast with process agreement.",
    "strong_metal_process_aligned": "Selected as a large metal-identity contrast with process agreement.",
    "cu_zn_pressure_exception": "Selected as a pressure-exception case within the Cu/Zn comparison set.",
    "near_null_comparison": "Selected as a matched comparison with minimal adsorption separation.",
    "process_discordant_comparison": "Selected as a case where process translation breaks alignment.",
    "functional_motif_example": "Illustrative exploratory case only. Not used as class-level evidence.",
}
COL = {
    "blue": "#A7D8EF",
    "blue_dark": "#4C8CB5",
    "pink": "#F6C6D7",
    "pink_dark": "#CC7EA0",
    "grey": "#C4CAD3",
    "grey_dark": "#6D7682",
    "soft": "#F7F8FB",
    "soft_2": "#FBFCFE",
    "border": "#CAD2DB",
    "text": "#26313A",
    "muted": "#64707C",
    "green": "#72A68B",
    "red": "#C87575",
    "lav": "#B8AAD9",
}
ROLE_COLOR = {
    "strong_linker_process_aligned": COL["blue_dark"],
    "strong_metal_process_aligned": COL["pink_dark"],
    "cu_zn_pressure_exception": COL["red"],
    "near_null_comparison": COL["grey_dark"],
    "process_discordant_comparison": "#8870B1",
    "functional_motif_example": "#7A7A7A",
}
ELEMENT_COLOR = {
    "H": "#D9D9D9", "C": "#4A4F54", "N": "#77AEDD", "O": "#E59696",
    "F": "#93C98A", "Cl": "#86BD84", "Br": "#A5775E", "I": "#8C75AB",
    "S": "#D7BA62", "P": "#E2A665", "Cu": "#C98A61", "Zn": "#92AABD",
    "V": "#7C90A4", "Fe": "#C78262", "Co": "#7088B9", "Ni": "#7AAA84",
}
METALS = {"Cu", "Zn", "V", "Fe", "Co", "Ni", "Mn", "Cr", "Mo", "Ag", "Cd"}


def style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "font.size": 9.0,
        "axes.labelcolor": COL["text"],
        "text.color": COL["text"],
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    })


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical(x: str) -> str:
    x = str(x).strip()
    x = re.sub(r"(?i)\.cif$", "", x)
    x = re.sub(r"(?i)_repeat$", "", x)
    x = re.sub(r"(?i)_sqe$", "", x)
    return x


def require(paths):
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(missing))


def resolve_structure_source():
    analysis = ROOT / "analysis" / "final_structure_case_inspection"
    if analysis.exists():
        return analysis, analysis / "cifs", "analysis/final_structure_case_inspection"
    return FROZEN, FROZEN / "cifs_selected", "frozen 08_structures subset"


def find_cif(cif_dir: Path, mof_id: str) -> Path:
    candidates = [
        cif_dir / f"{mof_id}.cif",
        cif_dir / f"{mof_id}_repeat.cif",
        cif_dir / f"{mof_id}_sqe.cif",
    ]
    for p in candidates:
        if p.exists():
            return p
    matches = list(cif_dir.glob(f"{mof_id}*.cif"))
    if len(matches) == 1:
        return matches[0]
    raise FileNotFoundError(f"Could not resolve exactly one CIF for {mof_id}: {matches}")


def parse_structure(path: Path):
    if HAVE_PYMATGEN:
        parser = CifParser(str(path), occupancy_tolerance=1.0)
        structures = parser.parse_structures(primitive=False)
        if not structures:
            raise RuntimeError(f"No structure parsed from {path}")
        structure = structures[0]
        frac = np.array([s.frac_coords for s in structure.sites], dtype=float)
        symbols = []
        for site in structure.sites:
            species = sorted(site.species.items(), key=lambda kv: float(kv[1]), reverse=True)
            symbols.append(species[0][0].symbol)
        return frac, symbols, "pymatgen"

    if HAVE_GEMMI:
        ss = gemmi.read_small_structure(str(path))
        if not ss.sites:
            raise RuntimeError(f"No sites parsed from {path}")
        frac = np.array([[s.fract.x, s.fract.y, s.fract.z] for s in ss.sites], dtype=float)
        symbols = [str(s.type_symbol) for s in ss.sites]
        return frac, symbols, "gemmi"

    raise RuntimeError("Neither pymatgen nor gemmi is available for CIF parsing")


def paired_projection(frac_a: np.ndarray, frac_b: np.ndarray):
    ca = frac_a - frac_a.mean(axis=0, keepdims=True)
    cb = frac_b - frac_b.mean(axis=0, keepdims=True)
    combo = np.vstack([ca, cb])
    _, _, vt = np.linalg.svd(combo, full_matrices=False)
    basis = vt[:2].T
    xy_a = ca @ basis
    xy_b = cb @ basis
    all_xy = np.vstack([xy_a, xy_b])
    span = np.ptp(all_xy, axis=0)
    span[span == 0] = 1.0
    lo = all_xy.min(axis=0)
    xy_a = (xy_a - lo) / span
    xy_b = (xy_b - lo) / span
    if np.ptp(all_xy[:, 0]) < np.ptp(all_xy[:, 1]):
        xy_a = xy_a[:, ::-1]
        xy_b = xy_b[:, ::-1]
    return xy_a, xy_b


def draw_structure(ax, xy, symbols, left_label, accent):
    keep = np.array([s != "H" for s in symbols])
    xy = xy[keep]
    symbols = [s for s, k in zip(symbols, keep) if k]
    if len(xy) == 0:
        raise RuntimeError("No non-hydrogen atoms available for structure overview")

    ax.set_facecolor(COL["soft_2"])
    for sym in sorted(set(symbols), key=lambda s: (s not in METALS, s)):
        idx = np.array([s == sym for s in symbols])
        is_metal = sym in METALS
        size = 34 if is_metal else (13 if sym == "C" else 17)
        ax.scatter(
            xy[idx, 0], xy[idx, 1], s=size,
            c=ELEMENT_COLOR.get(sym, "#999999"),
            edgecolors="white" if is_metal else "none",
            linewidths=.45 if is_metal else 0,
            alpha=.92 if is_metal else .84,
            zorder=3 if is_metal else 2,
        )

    ax.set_xlim(-.05, 1.05)
    ax.set_ylim(-.05, 1.05)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")
    for sp in ax.spines.values():
        sp.set_linewidth(.9)
        sp.set_color(COL["border"])
    ax.spines["left"].set_color(accent)
    ax.spines["left"].set_linewidth(2.4)
    ax.text(.03, .97, left_label, transform=ax.transAxes, ha="left", va="top",
            fontsize=9.2, fontweight="bold",
            bbox=dict(facecolor="white", edgecolor="none", alpha=.88, pad=1.5))


def summarize_charge(elements: pd.DataFrame, mof_id: str) -> str:
    x = elements[elements.mof_id.astype(str).map(canonical).eq(mof_id)].copy()
    metals = x[x.is_metal.eq(True)].sort_values("element")
    if metals.empty:
        return "n/a"
    return ", ".join(f"{r.element} {r.charge_mean:+.2f}" for _, r in metals.iterrows())


def bool_fraction(series: pd.Series):
    vals = series.dropna()
    if vals.empty:
        return None
    if vals.dtype == bool:
        b = vals.astype(bool)
    else:
        b = vals.astype(str).str.lower().map({"true": True, "false": False}).dropna()
    if len(b) == 0:
        return None
    return int(b.sum()), int(len(b))


def case_metrics(ads: pd.DataFrame, proc: pd.DataFrame, pair_key: str):
    med = None
    xa = ads[ads.pair_key.astype(str).eq(pair_key)] if "pair_key" in ads else pd.DataFrame()
    if not xa.empty and "absolute_log_difference" in xa:
        vals = pd.to_numeric(xa["absolute_log_difference"], errors="coerce").dropna()
        if not vals.empty:
            med = float(vals.median())
    xp = proc[proc.pair_key.astype(str).eq(pair_key)] if "pair_key" in proc else pd.DataFrame()
    wc = bool_fraction(xp["uptake_working_capacity_concordant"]) if "uptake_working_capacity_concordant" in xp else None
    sel = bool_fraction(xp["uptake_selectivity_concordant"]) if "uptake_selectivity_concordant" in xp else None
    return med, wc, sel


def metric_chip(ax, x, y, w, h, label, value, face, edge, value_color=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.012,rounding_size=0.04",
                                facecolor=face, edgecolor=edge, linewidth=.9))
    ax.text(x + 0.03 * w, y + 0.67 * h, label, ha="left", va="center",
            fontsize=6.6, color=COL["muted"], fontweight="bold")
    ax.text(x + 0.03 * w, y + 0.31 * h, value, ha="left", va="center",
            fontsize=8.2, color=value_color or COL["text"], fontweight="bold")



def step4_chemistry_annotation(row, role: str) -> str:
    wd_all = float(row["all_atom_charge_wasserstein"])
    wd_het = float(row["heteroatom_charge_wasserstein"])
    sensitive = int(row["method_sensitive_sites_total"])
    role = str(role)

    if role == "strong_linker_process_aligned":
        return f"robust node context | REPEAT WD all/hetero = {wd_all:.3f}/{wd_het:.3f}"
    if role == "strong_metal_process_aligned":
        return f"robust local coordination | REPEAT WD all/hetero = {wd_all:.3f}/{wd_het:.3f}"
    if role == "cu_zn_pressure_exception":
        return f"method-sensitive coordination: {sensitive} sites | REPEAT WD = {wd_all:.3f}/{wd_het:.3f}"
    if role == "near_null_comparison":
        return f"near-null comparator | REPEAT WD all/hetero = {wd_all:.3f}/{wd_het:.3f}"
    if role == "process_discordant_comparison":
        return f"descriptive chemistry context | REPEAT WD = {wd_all:.3f}/{wd_het:.3f}"
    if role == "functional_motif_example":
        return f"exploratory only | REPEAT WD all/hetero = {wd_all:.3f}/{wd_het:.3f}"
    return f"REPEAT WD all/hetero = {wd_all:.3f}/{wd_het:.3f}"

def main():
    style()
    source_dir, cif_dir, source_label = resolve_structure_source()
    pair_audit = source_dir / "candidate_pair_audit.csv"
    ads = source_dir / "candidate_adsorption_conditions.csv"
    proc = source_dir / "candidate_process_results.csv"
    require([CASES, ELEMENT_CHARGE, PAIR_CHARGE, pair_audit, ads, proc, cif_dir, P2C, P2E])

    cases = pd.read_csv(CASES)
    elements = pd.read_csv(ELEMENT_CHARGE)
    _pair_charge = pd.read_csv(PAIR_CHARGE)
    _pair_audit = pd.read_csv(pair_audit, low_memory=False)
    ads_df = pd.read_csv(ads, low_memory=False)
    proc_df = pd.read_csv(proc, low_memory=False)
    p2c = pd.read_csv(P2C, low_memory=False)
    p2e = pd.read_csv(P2E, low_memory=False)
    if len(p2c) != 6 or p2c['case_role'].nunique() != 6:
        raise RuntimeError('Phase 2C case chemistry is not the expected six-role set')
    if len(p2e) != 6 or p2e['case_role'].nunique() != 6:
        raise RuntimeError('Phase 2E manuscript map is not the expected six-role set')
    step4 = p2c.merge(
        p2e[['case_role','phase2e_decision','recommended_placement']],
        on='case_role', how='left', validate='one_to_one'
    ).set_index('case_role')

    if len(cases) != 6 or set(cases.selection_category) != set(ROLE_ORDER):
        raise RuntimeError("Frozen case set is not the expected six-role set")
    cases["role_order"] = cases.selection_category.map({r: i for i, r in enumerate(ROLE_ORDER)})
    cases = cases.sort_values("role_order")

    parser_backends = set()
    source_rows = []
    fig = plt.figure(figsize=(11.2, 12.4))
    outer = fig.add_gridspec(3, 2, hspace=.24, wspace=.16)

    for i, (_, row) in enumerate(cases.iterrows()):
        role = row.selection_category
        accent = ROLE_COLOR[role]
        sub = outer[i // 2, i % 2].subgridspec(3, 2, height_ratios=[.58, 3.05, 2.05], hspace=.03, wspace=.05)
        ax_h = fig.add_subplot(sub[0, :])
        ax_a = fig.add_subplot(sub[1, 0])
        ax_b = fig.add_subplot(sub[1, 1])
        ax_f = fig.add_subplot(sub[2, :])

        for ax in [ax_h, ax_f]:
            ax.set_xticks([])
            ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_visible(False)
            ax.set_facecolor("white")

        id_a, id_b = canonical(row.id_a), canonical(row.id_b)
        cif_a, cif_b = find_cif(cif_dir, id_a), find_cif(cif_dir, id_b)
        frac_a, sym_a, backend_a = parse_structure(cif_a)
        frac_b, sym_b, backend_b = parse_structure(cif_b)
        parser_backends.update([backend_a, backend_b])
        xy_a, xy_b = paired_projection(frac_a, frac_b)
        draw_structure(ax_a, xy_a, sym_a, "A", accent)
        draw_structure(ax_b, xy_b, sym_b, "B", accent)

        ax_h.set_xlim(0, 1)
        ax_h.set_ylim(0, 1)
        ax_h.add_patch(FancyBboxPatch((0.0, 0.12), 1.0, 0.76,
                                      boxstyle="round,pad=0.018,rounding_size=0.05",
                                      facecolor=COL["soft"], edgecolor=COL["border"], linewidth=.9))
        ax_h.add_patch(FancyBboxPatch((0.012, 0.20), 0.065, 0.60,
                                      boxstyle="round,pad=0.01,rounding_size=0.05",
                                      facecolor=accent, edgecolor=accent, linewidth=0))
        ax_h.text(0.0445, 0.50, chr(65 + i), ha="center", va="center", fontsize=14.6, fontweight="bold", color="white")
        ax_h.text(0.10, 0.62, ROLE_TITLE[role], ha="left", va="center", fontsize=10.7, fontweight="bold", color=accent)
        ax_h.text(0.10, 0.30, str(row.transition), ha="left", va="center", fontsize=8.7, fontweight="bold", color=COL["text"])

        med, wc, sel = case_metrics(ads_df, proc_df, row.pair_key)
        med_txt = f"{med:.3f}" if med is not None else "n/a"
        wc_txt = f"{wc[0]}/{wc[1]}" if wc else "n/a"
        sel_txt = f"{sel[0]}/{sel[1]}" if sel else "n/a"

        ax_f.set_xlim(0, 1)
        ax_f.set_ylim(0, 1)
        ax_f.add_patch(FancyBboxPatch((0.0, 0.02), 1.0, 0.96,
                                      boxstyle="round,pad=0.018,rounding_size=0.05",
                                      facecolor=COL["soft"], edgecolor=COL["border"], linewidth=.9))
        metric_chip(ax_f, 0.03, 0.62, 0.28, 0.24, "median |Δlog q|", med_txt, "white", COL["border"])
        metric_chip(ax_f, 0.36, 0.62, 0.27, 0.24, "WC concordance", wc_txt, COL["blue"], COL["blue_dark"])
        metric_chip(ax_f, 0.68, 0.62, 0.24, 0.24, "Selectivity", sel_txt, COL["pink"], COL["pink_dark"])
        ax_f.text(0.03, 0.43, f"A metal q: {summarize_charge(elements, id_a)}", ha="left", va="center",
                  fontsize=7.15, color=COL["muted"], fontweight="bold")
        ax_f.text(0.52, 0.43, f"B metal q: {summarize_charge(elements, id_b)}", ha="left", va="center",
                  fontsize=7.15, color=COL["muted"], fontweight="bold")

        s4 = step4.loc[role]
        chem_line = step4_chemistry_annotation(s4, role)
        ax_f.text(0.03, 0.24, chem_line, ha="left", va="center",
                  fontsize=7.15, color=accent, fontweight="bold")

        ax_f.text(0.03, 0.075, ROLE_NOTE[role], ha="left", va="center",
                  fontsize=6.75, color=COL["muted"], fontstyle="italic" if role == "functional_motif_example" else "normal")
        if role == "functional_motif_example":
            ax_f.text(0.97, 0.075, "exploratory only", ha="right", va="center",
                      fontsize=6.9, color=ROLE_COLOR[role], fontstyle="italic", fontweight="bold")

        source_rows.append({
            "panel": chr(65 + i),
            "selection_category": role,
            "pair_key": row.pair_key,
            "id_a": id_a,
            "id_b": id_b,
            "transition": row.transition,
            "median_absolute_log_difference": row.median_absolute_log_difference,
            "mean_wc_concordance": row.mean_wc_concordance,
            "mean_selectivity_concordance": row.mean_selectivity_concordance,
            "cif_a": str(cif_a),
            "cif_b": str(cif_b),
            "parser_a": backend_a,
            "parser_b": backend_b,
            "charge_use": "validated selected-case structural fingerprint only",
            "all_atom_charge_wasserstein": float(s4["all_atom_charge_wasserstein"]),
            "heteroatom_charge_wasserstein": float(s4["heteroatom_charge_wasserstein"]),
            "method_sensitive_sites_total": int(s4["method_sensitive_sites_total"]),
            "crystalnn_shell_inventory_same": s4["crystalnn_shell_inventory_same"],
            "chemenv_inventory_same": s4["chemenv_inventory_same"],
            "phase2e_decision": s4["phase2e_decision"],
            "step4_annotation": chem_line,
        })

    fig.subplots_adjust(left=.045, right=.985, bottom=.03, top=.985)
    outputs = []
    for ext in ["pdf", "svg", "png"]:
        path = OUT / f"Figure_05.{ext}"
        fig.savefig(path, dpi=DPI if ext == "png" else None, bbox_inches="tight")
        outputs.append(str(path))
    plt.close(fig)

    pd.DataFrame(source_rows).to_csv(OUT / "07_case_panel_source.csv", index=False)
    report = [
        "PROJECT 7B2 STRUCTURE-CASE FIGURE RENDERING",
        "=" * 72,
        "Decision: FIGURE 5 RENDERED",
        f"Cases rendered: {len(source_rows)}",
        f"Framework structures rendered: {2 * len(source_rows)}",
        f"CIF parser backend(s): {', '.join(sorted(parser_backends))}",
        f"Structure source: {source_label}",
        "",
        "Boundaries:",
        "- structures are pair-aligned deterministic projections of frozen CIF atom coordinates",
        "- both members of each pair use the same projection basis for visual comparison",
        "- hydrogen is hidden only for visual readability",
        "- metal charges and REPEAT distribution distances are selected-case descriptive fingerprints only",
        "- CrystalNN/ChemEnv annotations describe local coordination only",
        "- no adsorption site, linker-local charge, oxidation state, charge transfer, causal mechanism, or direction is inferred",
    ]
    (OUT / "07_render_report.txt").write_text("\n".join(report), encoding="utf-8", newline="\n")
    manifest = {
        "stage": "structure-resolved Figure 5 rendering",
        "created": datetime.now().isoformat(timespec="seconds"),
        "script": "07_render_structure_case_figure.py",
        "structure_source": source_label,
        "inputs": {str(p): sha256(p) for p in [CASES, ELEMENT_CHARGE, PAIR_CHARGE, pair_audit, ads, proc, P2C, P2E]},
        "cif_directory": str(cif_dir),
        "case_count": len(source_rows),
        "framework_count": 2 * len(source_rows),
        "parser_backends": sorted(parser_backends),
        "outputs": outputs + [str(OUT / "07_case_panel_source.csv"), str(OUT / "07_render_report.txt")],
        "pair_membership_changed": False,
        "mechanism_claim": False,
        "python": sys.version,
        "pandas": pd.__version__,
        "matplotlib": plt.matplotlib.__version__,
    }
    (OUT / "07_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
    print("\n".join(report))
    print(f"\nOutputs: {OUT}")


if __name__ == "__main__":
    main()
