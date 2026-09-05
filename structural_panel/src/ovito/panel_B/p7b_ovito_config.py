"""Shared configuration for Project 7B OVITO structural screening."""

from pathlib import Path
import os

MODULE_ROOT = Path(__file__).resolve().parents[3]

def project_root():
    """Resolve the structural-panel root.

    P7B_ROOT may point either to this packaged module or to the historical
    starter-pack layout. Without it, use the packaged module itself.
    """
    env = os.environ.get("P7B_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return MODULE_ROOT

def cif_root(root: Path) -> Path:
    packaged = root / "data" / "cifs"
    historical = root / "CIF_by_panel"
    if packaged.exists():
        return packaged
    if historical.exists():
        return historical
    return packaged

ROOT = project_root()
CIF_ROOT = cif_root(ROOT)
OUT_ROOT = ROOT / "OVITO_screening"

PANEL_DATA = {
    "A": {
        "folder": "A_strong_linker_process_aligned",
        "role": "Strong linker / process aligned",
        "topology": "pcu",
        "i": "A_i__DB0-m3_o11_o17_f0_pcu.sym.32.cif",
        "ii": "A_ii__DB0-m3_o12_o20_f0_pcu.sym.24.cif",
        "cell_context": "~15.1 x 11.1 x 9.9 A",
        "reps": [(1,1,1),(2,1,1),(1,2,1),(1,1,2),(2,2,1),(2,1,2),(1,2,2),(2,2,2)],
        "warning": "Linker contrast. Do not label an adsorption site."
    },
    "B": {
        "folder": "B_strong_metal_process_aligned",
        "role": "Strong metal / process aligned",
        "topology": "nbo",
        "i": "B_i__DB0-m3_o7_o7_f0_nbo.sym.48.cif",
        "ii": "B_ii__DB0-m2_o7_o7_f0_nbo.sym.45.cif",
        "cell_context": "~35.5 x 35.5 x 35.5 A",
        "reps": [(1,1,1),(2,1,1),(1,2,1),(1,1,2)],
        "warning": "Cleanest local Zn/Cu comparison; still not an adsorption mechanism."
    },
    "C": {
        "folder": "C_cu_zn_pressure_exception",
        "role": "Cu-Zn pressure exception",
        "topology": "nbo",
        "i": "C_i__DB0-m3_o6_o27_f0_nbo.sym.33.cif",
        "ii": "C_ii__DB0-m2_o6_o27_f0_nbo.sym.30.cif",
        "cell_context": "~32.3 x 32.3 x 38.7 A",
        "reps": [(1,1,1),(2,1,1),(1,2,1),(1,1,2)],
        "warning": "Boundary/method-sensitive local case. Avoid strong coordination-mechanism claims."
    },
    "D": {
        "folder": "D_near_null_comparison",
        "role": "Near-null linker comparator",
        "topology": "nbo",
        "i": "D_i__DB0-m2_o23_o28_f0_nbo.sym.21.cif",
        "ii": "D_ii__DB0-m2_o23_o28_f0_nbo.sym.4.cif",
        "cell_context": "~44.8 x 44.8 x 32.4 A, monoclinic",
        "reps": [(1,1,1),(2,1,1),(1,2,1),(1,1,2)],
        "warning": "Near-null comparator, not inactive/no effect."
    },
    "E": {
        "folder": "E_process_discordant_comparison",
        "role": "Process-discordant linker comparator",
        "topology": "fsc",
        "i": "E_i__DB0-m3_o440_o155_f0_fsc.sym.26.cif",
        "ii": "E_ii__DB0-m3_o152_o155_f0_fsc.sym.27.cif",
        "cell_context": "~17.5 x 8.6 x 13.5 A",
        "reps": [(1,1,1),(2,1,1),(1,2,1),(1,3,1),(1,1,2),(2,2,1),(1,2,2),(2,2,2)],
        "warning": "Do not invent a structural explanation for process discordance."
    },
    "F": {
        "folder": "F_functional_motif_example",
        "role": "Exploratory functional-motif example",
        "topology": "sra",
        "i": "F_i__DB0-m9_o17_o27_f0_sra.sym.117.cif",
        "ii": "F_ii__DB0-m9_o17_o27_f0_sra.sym.116.cif",
        "cell_context": "~6.3 x 21.4 x 25.4 A",
        "reps": [(1,1,1),(2,1,1),(3,1,1),(4,1,1),(1,2,1),(1,1,2),(2,2,1)],
        "warning": "Exploratory only; no class-wide mechanism."
    },
}

# Crystallographic camera directions expressed as coefficients of a,b,c.
VIEW_COEFFS_FULL = {
    "a_plus":       ( 1, 0, 0),
    "a_minus":      (-1, 0, 0),
    "b_plus":       ( 0, 1, 0),
    "b_minus":      ( 0,-1, 0),
    "c_plus":       ( 0, 0, 1),
    "c_minus":      ( 0, 0,-1),
    "ab_plus":      ( 1, 1, 0),
    "ab_mixed":     ( 1,-1, 0),
    "ac_plus":      ( 1, 0, 1),
    "ac_mixed":     ( 1, 0,-1),
    "bc_plus":      ( 0, 1, 1),
    "bc_mixed":     ( 0, 1,-1),
    "abc_plus":     ( 1, 1, 1),
    "abc_mixed":    ( 1,-1, 1),
}

VIEW_NAMES_QUICK = [
    "a_plus","b_plus","c_plus",
    "ab_plus","ac_plus","bc_plus","abc_plus","abc_mixed"
]

IMAGE_SIZE = (3200, 2400)
DPI = 600
PAIR_MARGIN = 1.08

# Publication-oriented baseline palette.
PALETTE_BASE = {
    "H":  (0.90, 0.90, 0.90),
    "C":  (0.27, 0.27, 0.27),
    "N":  (0.20, 0.36, 0.82),
    "O":  (0.86, 0.18, 0.18),
    "Zn": (0.48, 0.38, 0.68),
    "Cu": (0.78, 0.39, 0.17),
    "V":  (0.42, 0.50, 0.66),
    "I":  (0.48, 0.20, 0.56),
}

PALETTE_SOFT = {
    "H":  (0.92, 0.92, 0.92),
    "C":  (0.36, 0.36, 0.36),
    "N":  (0.32, 0.48, 0.74),
    "O":  (0.78, 0.30, 0.30),
    "Zn": (0.53, 0.47, 0.65),
    "Cu": (0.70, 0.45, 0.28),
    "V":  (0.48, 0.56, 0.67),
    "I":  (0.52, 0.34, 0.58),
}

PALETTE_METAL_HIGH = {
    **PALETTE_BASE,
    "C":  (0.35, 0.35, 0.35),
    "Zn": (0.34, 0.20, 0.78),
    "Cu": (0.92, 0.34, 0.05),
    "V":  (0.18, 0.48, 0.70),
}

BASE_RADII = {
    "H": 0.12,
    "C": 0.30,
    "N": 0.33,
    "O": 0.33,
    "Zn": 0.48,
    "Cu": 0.48,
    "V": 0.46,
    "I": 0.52,
}

BASE_BOND_WIDTH = 0.13
BASE_BOND_COLOR = (0.58, 0.58, 0.58)

# One-factor-at-a-time style recipes.
STYLE_RECIPES = [
    dict(name="S00_baseline", h_mode="show", h_radius=0.12, particle_scale=1.00,
         bond_width=0.13, bond_color=(0.58,0.58,0.58), bond_coloring="uniform",
         palette="base", show_cell=False, ao=False, bond_mode="covalent"),

    dict(name="S01_H_hidden", h_mode="hide", h_radius=0.12, particle_scale=1.00,
         bond_width=0.13, bond_color=(0.58,0.58,0.58), bond_coloring="uniform",
         palette="base", show_cell=False, ao=False, bond_mode="covalent"),

    dict(name="S02_H_0p08", h_mode="show", h_radius=0.08, particle_scale=1.00,
         bond_width=0.13, bond_color=(0.58,0.58,0.58), bond_coloring="uniform",
         palette="base", show_cell=False, ao=False, bond_mode="covalent"),

    dict(name="S03_H_0p18", h_mode="show", h_radius=0.18, particle_scale=1.00,
         bond_width=0.13, bond_color=(0.58,0.58,0.58), bond_coloring="uniform",
         palette="base", show_cell=False, ao=False, bond_mode="covalent"),

    dict(name="S04_atoms_0p75", h_mode="show", h_radius=0.12, particle_scale=0.75,
         bond_width=0.13, bond_color=(0.58,0.58,0.58), bond_coloring="uniform",
         palette="base", show_cell=False, ao=False, bond_mode="covalent"),

    dict(name="S05_atoms_1p25", h_mode="show", h_radius=0.12, particle_scale=1.25,
         bond_width=0.13, bond_color=(0.58,0.58,0.58), bond_coloring="uniform",
         palette="base", show_cell=False, ao=False, bond_mode="covalent"),

    dict(name="S06_bond_0p08", h_mode="show", h_radius=0.12, particle_scale=1.00,
         bond_width=0.08, bond_color=(0.58,0.58,0.58), bond_coloring="uniform",
         palette="base", show_cell=False, ao=False, bond_mode="covalent"),

    dict(name="S07_bond_0p20", h_mode="show", h_radius=0.12, particle_scale=1.00,
         bond_width=0.20, bond_color=(0.58,0.58,0.58), bond_coloring="uniform",
         palette="base", show_cell=False, ao=False, bond_mode="covalent"),

    dict(name="S08_bond_dark", h_mode="show", h_radius=0.12, particle_scale=1.00,
         bond_width=0.13, bond_color=(0.36,0.36,0.36), bond_coloring="uniform",
         palette="base", show_cell=False, ao=False, bond_mode="covalent"),

    dict(name="S09_bond_by_particle", h_mode="show", h_radius=0.12, particle_scale=1.00,
         bond_width=0.13, bond_color=(0.58,0.58,0.58), bond_coloring="particle",
         palette="base", show_cell=False, ao=False, bond_mode="covalent"),

    dict(name="S10_palette_soft", h_mode="show", h_radius=0.12, particle_scale=1.00,
         bond_width=0.13, bond_color=(0.58,0.58,0.58), bond_coloring="uniform",
         palette="soft", show_cell=False, ao=False, bond_mode="covalent"),

    dict(name="S11_palette_metal_high", h_mode="show", h_radius=0.12, particle_scale=1.00,
         bond_width=0.13, bond_color=(0.58,0.58,0.58), bond_coloring="uniform",
         palette="metal_high", show_cell=False, ao=False, bond_mode="covalent"),

    dict(name="S12_cell_on", h_mode="show", h_radius=0.12, particle_scale=1.00,
         bond_width=0.13, bond_color=(0.58,0.58,0.58), bond_coloring="uniform",
         palette="base", show_cell=True, ao=False, bond_mode="covalent"),

    dict(name="S13_AO_soft", h_mode="show", h_radius=0.12, particle_scale=1.00,
         bond_width=0.13, bond_color=(0.58,0.58,0.58), bond_coloring="uniform",
         palette="base", show_cell=False, ao=True, bond_mode="covalent"),

    dict(name="S14_bonds_VdW_auto", h_mode="show", h_radius=0.12, particle_scale=1.00,
         bond_width=0.13, bond_color=(0.58,0.58,0.58), bond_coloring="uniform",
         palette="base", show_cell=False, ao=False, bond_mode="vdw"),
]

def cif_paths(panel):
    cfg = PANEL_DATA[panel]
    d = CIF_ROOT / cfg["folder"]
    return {"i": d / cfg["i"], "ii": d / cfg["ii"]}

def rep_code(rep):
    return "".join(str(v) for v in rep)

def parse_rep(text):
    text = text.lower().replace("x","").replace(",","").replace(" ","")
    if len(text) != 3 or not text.isdigit():
        raise ValueError("Replication must look like 111, 211, 121, etc.")
    return tuple(int(c) for c in text)


# ---------------------------------------------------------------------------
# Panel B chemically controlled bond topology for rendering.
# Derived from the B CIF nearest-neighbor gaps and validated against the
# bond-diagnostics CSV. Unspecified pairs stay OFF in Pairwise mode.
# ---------------------------------------------------------------------------
B_PAIRWISE_CUTOFFS = {
    ("C", "C"): 1.60,
    ("C", "H"): 1.20,
    ("C", "I"): 2.25,
    ("C", "O"): 1.50,
    ("Zn", "O"): 2.20,
    ("Cu", "O"): 2.20,
}

B_EXPECTED_BOND_COUNTS = {
    "i": {
        "C-C": 204,
        "C-H": 48,
        "C-I": 48,
        "C-O": 48,
        "O-Zn": 48,
        "TOTAL": 396,
    },
    "ii": {
        "C-C": 204,
        "C-H": 48,
        "C-I": 48,
        "C-O": 48,
        "Cu-O": 48,
        "TOTAL": 396,
    },
}
