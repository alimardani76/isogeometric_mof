"""Panel C configuration."""

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
PANEL_DIR = CIF_ROOT / "C_cu_zn_pressure_exception"

def first_existing(*paths):
    for p in paths:
        if p.exists():
            return p
    return paths[0]

C_I = first_existing(
    PANEL_DIR / "C_i__DB0-m3_o6_o27_f0_nbo.sym.33.cif",
    PANEL_DIR / "DB0-m3_o6_o27_f0_nbo.sym.33.cif",
)
C_II = first_existing(
    PANEL_DIR / "C_ii__DB0-m2_o6_o27_f0_nbo.sym.30.cif",
    PANEL_DIR / "DB0-m2_o6_o27_f0_nbo.sym.30.cif",
)

OUT_ROOT = ROOT / "OVITO_screening"
OUT_DIR = OUT_ROOT / "60_C_whole_geometry"

C_PAIRWISE_CUTOFFS = {
    ("C","C"): 1.60,
    ("C","H"): 1.20,
    ("C","N"): 1.50,
    ("C","O"): 1.50,
    ("N","H"): 1.10,
    ("N","N"): 1.40,
    ("Zn","O"): 2.20,
    ("Cu","O"): 2.20,
}

EXPECTED = {
    "i": {
        "atoms":332,
        "elements":{"O":48,"C":160,"Zn":12,"H":80,"N":32},
        "total_bonds":376,
        "bonds":{"C-C":160,"C-H":48,"C-N":32,"C-O":48,"H-N":32,"N-N":8,"O-Zn":48},
        "metal":"Zn",
        "first_shell_range":(2.02,2.04),
        "next_shell_min":3.25,
    },
    "ii": {
        "atoms":332,
        "elements":{"O":48,"C":160,"Cu":12,"H":80,"N":32},
        "total_bonds":376,
        "bonds":{"C-C":160,"C-H":48,"C-N":32,"C-O":48,"H-N":32,"N-N":8,"Cu-O":48},
        "metal":"Cu",
        "first_shell_range":(1.94,1.97),
        "next_shell_min":3.00,
    },
}

# label, view, up, replication
CASES = [
    ("C1_c_up_b__111",     (0,0,1),(0,1,0),(1,1,1)),
    ("C2_c_up_b__plane22", (0,0,1),(0,1,0),(2,2,1)),
    ("C3_c_up_a__plane22", (0,0,1),(1,0,0),(2,2,1)),

    ("A1_a_up_c__111",     (1,0,0),(0,0,1),(1,1,1)),
    ("A2_a_up_c__plane22", (1,0,0),(0,0,1),(1,2,2)),

    ("B1_b_up_c__111",     (0,1,0),(0,0,1),(1,1,1)),
    ("B2_b_up_c__plane22", (0,1,0),(0,0,1),(2,1,2)),

    ("D1_abc_up_c__111",   (1,1,1),(0,0,1),(1,1,1)),
]

PALETTE = {
    "H": (0.92,0.92,0.92),
    "C": (0.29,0.29,0.29),
    "N": (0.16,0.36,0.78),
    "O": (0.84,0.20,0.20),
    "Zn":(0.25,0.48,0.72),
    "Cu":(0.82,0.42,0.16),
}

RADII = {
    "H":0.10,
    "C":0.27,
    "N":0.32,
    "O":0.34,
    "Zn":0.62,
    "Cu":0.62,
}

BOND_WIDTH = 0.12
BOND_COLOR = (0.48,0.48,0.48)
IMAGE_SIZE = (3200,2400)
DPI = 600
PAIR_MARGIN = 1.06
