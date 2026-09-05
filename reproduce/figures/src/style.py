from __future__ import annotations
from pathlib import Path
import json
import matplotlib as mpl
from matplotlib import font_manager
import warnings

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

# Restrained, color-blind-conscious publication palette.  The intention is a
# Nature/Cell/ACS-style visual language: few saturated hues, dark text, soft
# neutrals, and consistent semantic colors across every main/SI figure.
COLORS = {
    "linker": "#2F5D9B",
    "linker_light": "#AFC4E3",
    "metal": "#D46A1F",
    "metal_light": "#F0B77C",
    "functional": "#756AA6",
    "functional_light": "#C3BCDB",
    "control": "#707985",
    "control_light": "#D8DDE3",
    "ink": "#1F2732",
    "muted": "#68727D",
    "grid": "#E7EAEE",
    "border": "#B7BEC7",
    "co2": "#1B7F79",
    "coguest": "#B58228",
    "raspa_full": "#214E7A",
    "raspa_chargeoff": "#B8C0CA",
    "vdw": "#648DBA",
    "coulomb": "#D98233",
    "total": "#7B858F",
    "positive": "#2F5D9B",
    "negative": "#D46A1F",
}

INTERVENTION_LABEL = {
    "linker_family_change": "Linker family",
    "metal_substitution": "Metal substitution",
    "functional_motif_change": "Functional motif",
}
INTERVENTION_COLOR = {
    "linker_family_change": COLORS["linker"],
    "metal_substitution": COLORS["metal"],
    "functional_motif_change": COLORS["functional"],
}

PROCESS_LABEL = {
    "landfill-gas-vpsa": "Landfill gas",
    "methane-storage-psa": "Methane storage",
    "natural-gas-purification": "Natural-gas purification",
    "post-combustion-vsa": "Post-combustion",
    "pre-combustion-40-40": "Pre-combustion",
}

# Use mathtext for chemical formula subscripts.  This avoids missing Unicode
# subscript glyphs and guarantees proper CH4/CO2/N2/H2 rendering in PDFs.
TARGET_LABEL = {
    "landfill_CH4": r"Landfill $\mathrm{CH_4}$",
    "landfill_CO2": r"Landfill $\mathrm{CO_2}$",
    "methane_purification_CH4": r"Purification $\mathrm{CH_4}$",
    "methane_purification_CO2": r"Purification $\mathrm{CO_2}$",
    "methane_storage_CH4": r"Storage $\mathrm{CH_4}$",
    "post_combustion_CO2": r"Post-comb. $\mathrm{CO_2}$",
    "post_combustion_N2": r"Post-comb. $\mathrm{N_2}$",
    "pre_combustion_CO2": r"Pre-comb. $\mathrm{CO_2}$",
    "pre_combustion_H2": r"Pre-comb. $\mathrm{H_2}$",
}

TARGET_ORDER = [
    "landfill_CH4", "landfill_CO2",
    "methane_purification_CH4", "methane_purification_CO2",
    "methane_storage_CH4",
    "post_combustion_CO2", "post_combustion_N2",
    "pre_combustion_CO2", "pre_combustion_H2",
]

ROLE_LABEL = {
    "strong_linker": "A1 · strong linker",
    "near_null_linker": "A2 · near-null linker",
    "strong_metal": "A3 · strong metal",
    "cu_zn_pressure_exception": "A4 · Cu–Zn exception",
    "confirmatory_strong_linker": "B1 · confirmatory strong linker",
    "confirmatory_near_null_linker": "B2 · confirmatory near-null linker",
    "process_discordant_linker": "C1 · process-discordant linker",
    "exploratory_functional_motif": "C2 · exploratory motif",
}


def resolve_font() -> str:
    candidates = [CONFIG.get("font_primary", "Arial")] + CONFIG.get("font_fallbacks", [])
    for name in candidates:
        try:
            path = font_manager.findfont(name, fallback_to_default=False)
            if path:
                return name
        except Exception:
            continue
    return "DejaVu Sans"


RESOLVED_FONT = resolve_font()
if RESOLVED_FONT.lower() != CONFIG.get("font_primary", "Arial").lower():
    warnings.warn(
        f"Primary font {CONFIG.get('font_primary', 'Arial')!r} was not found; "
        f"using {RESOLVED_FONT!r} as a preview fallback. For submission PDFs, render "
        "on a system with Arial installed and confirm manifest.json reports font_resolved = Arial.",
        RuntimeWarning,
    )


def apply_style(base_font: float = 9.6) -> None:
    # On Windows this resolves to Arial.  The fallback exists only so the
    # package remains executable on machines without Microsoft's font files.
    mpl.rcParams.update({
        "font.family": RESOLVED_FONT,
        "font.sans-serif": [RESOLVED_FONT, CONFIG.get("font_primary", "Arial")] + CONFIG.get("font_fallbacks", []),
        "font.size": base_font,
        "axes.titlesize": base_font + 1.35,
        "axes.titleweight": "bold",
        "axes.labelsize": base_font + 0.55,
        "axes.labelweight": "bold",
        "xtick.labelsize": base_font - 0.10,
        "ytick.labelsize": base_font - 0.10,
        "legend.fontsize": base_font - 0.25,
        "axes.linewidth": 0.85,
        "axes.edgecolor": COLORS["ink"],
        "axes.labelcolor": COLORS["ink"],
        "text.color": COLORS["ink"],
        "xtick.color": COLORS["ink"],
        "ytick.color": COLORS["ink"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.pad_inches": 0.06,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "mathtext.fontset": "custom",
        "mathtext.rm": RESOLVED_FONT,
        "mathtext.it": f"{RESOLVED_FONT}:italic",
        "mathtext.bf": f"{RESOLVED_FONT}:bold",
        "mathtext.default": "regular",
        "axes.unicode_minus": True,
    })


def clean_axis(ax, grid_axis: str | None = "x") -> None:
    if grid_axis:
        ax.grid(axis=grid_axis, color=COLORS["grid"], lw=0.72, zorder=0)
        ax.set_axisbelow(True)
    ax.spines["left"].set_linewidth(0.85)
    ax.spines["bottom"].set_linewidth(0.85)
    ax.tick_params(width=0.75, length=3.4, pad=4)


def panel_label(ax, letter: str, x: float = -0.12, y: float = 1.075) -> None:
    ax.text(
        x, y, letter.upper(), transform=ax.transAxes, ha="left", va="bottom",
        fontsize=14.0, fontweight="bold", clip_on=False,
    )


def title_left(ax, title: str) -> None:
    ax.set_title(title, loc="left", pad=10, fontweight="bold")


def condition_label(target: str, pressure: float) -> str:
    return f"{TARGET_LABEL.get(target, target)} · {pressure:g} bar"


def save_figure(fig, output_base: Path) -> list[Path]:
    output_base.parent.mkdir(parents=True, exist_ok=True)
    out = []
    if CONFIG.get("save_pdf", True):
        p = output_base.with_suffix(".pdf")
        fig.savefig(p, bbox_inches="tight", transparent=CONFIG.get("transparent", False))
        out.append(p)
    if CONFIG.get("save_png", True):
        p = output_base.parent / f"{output_base.name}_200dpi.png"
        fig.savefig(
            p, dpi=int(CONFIG.get("png_dpi", 200)), bbox_inches="tight",
            transparent=CONFIG.get("transparent", False),
        )
        out.append(p)
    return out


def legend_handles_interventions(include_functional: bool = False):
    from matplotlib.lines import Line2D
    keys = ["linker_family_change", "metal_substitution"]
    if include_functional:
        keys.append("functional_motif_change")
    return [
        Line2D(
            [0], [0], marker="o", color="none",
            markerfacecolor=INTERVENTION_COLOR[k], markeredgecolor=INTERVENTION_COLOR[k],
            markersize=6.4, label=INTERVENTION_LABEL[k],
        )
        for k in keys
    ]
