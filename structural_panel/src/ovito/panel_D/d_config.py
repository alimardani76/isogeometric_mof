"""Panel D configuration."""

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
CIF_DIR = CIF_ROOT / "D_near_null_comparison"
D_I = CIF_DIR / "D_i__DB0-m2_o23_o28_f0_nbo.sym.21.cif"
D_II = CIF_DIR / "D_ii__DB0-m2_o23_o28_f0_nbo.sym.4.cif"

OUT_ROOT = ROOT / "OVITO_screening"
OUT_DIR = OUT_ROOT / "20_D_geometry_111"

D_PAIRWISE_CUTOFFS = {
    ("C","C"): 1.70,
    ("C","H"): 1.20,
    ("C","O"): 1.50,
    ("C","N"): 1.50,
    ("Cu","O"): 2.20,
}

EXPECTED = {
    "i": {
        "atoms": 476,
        "elements": {"Cu":12, "C":232, "H":160, "N":8, "O":64},
        "bonds": {"C-C":244, "C-H":160, "C-O":64, "C-N":24, "Cu-O":48},
        "total_bonds": 540,
        "ethyl": 4,
        "methyl_on_CH": 0,
    },
    "ii": {
        "atoms": 464,
        "elements": {"Cu":12, "C":228, "H":152, "N":8, "O":64},
        "bonds": {"C-C":240, "C-H":152, "C-O":64, "C-N":24, "Cu-O":48},
        "total_bonds": 528,
        "ethyl": 0,
        "methyl_on_CH": 4,
    },
}

VIEW_COEFFS = {
    "a_plus":    (1,0,0),
    "b_plus":    (0,1,0),
    "c_plus":    (0,0,1),
    "ab_plus":   (1,1,0),
    "ac_plus":   (1,0,1),
    "ac_mixed":  (1,0,-1),
    "bc_plus":   (0,1,1),
    "bc_mixed":  (0,1,-1),
    "abc_plus":  (1,1,1),
    "abc_mixed": (1,-1,1),
}

# Neutral geometry-screen style. This is not the final D publication style.
PALETTE = {
    "H":  (0.92,0.92,0.92),
    "C":  (0.30,0.30,0.30),
    "N":  (0.22,0.40,0.78),
    "O":  (0.84,0.20,0.20),
    "Cu": (0.78,0.42,0.18),
}

RADII = {
    "H": 0.10,
    "C": 0.25,
    "N": 0.31,
    "O": 0.31,
    "Cu":0.55,
}

BOND_WIDTH = 0.11
BOND_COLOR = (0.50,0.50,0.50)
IMAGE_SIZE = (3200,2400)
DPI = 600
PAIR_MARGIN = 1.07
