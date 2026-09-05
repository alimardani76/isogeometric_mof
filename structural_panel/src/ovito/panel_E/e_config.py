"""Panel E configuration."""

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
CIF_DIR = CIF_ROOT / "E_process_discordant_comparison"
E_I = CIF_DIR / "E_i__DB0-m3_o440_o155_f0_fsc.sym.26.cif"
E_II = CIF_DIR / "E_ii__DB0-m3_o152_o155_f0_fsc.sym.27.cif"

OUT_ROOT = ROOT / "OVITO_screening"
OUT_DIR = OUT_ROOT / "40_E_basis_matched"

E_PAIRWISE_CUTOFFS = {
    ("C","C"): 1.60,
    ("C","H"): 1.20,
    ("C","N"): 1.50,
    ("C","O"): 1.50,
    ("O","H"): 1.10,
    ("Zn","O"): 2.20,
    ("Zn","N"): 1.90,
}

EXPECTED = {
    "i": {
        "atoms": 84,
        "elements": {"C":46,"H":18,"O":16,"Zn":2,"N":2},
        "total_bonds": 99,
        "bonds": {
            "C-C":51, "C-H":14, "C-N":4, "C-O":16,
            "H-O":4, "N-Zn":2, "O-Zn":8,
        },
        "components": [
            ({"C":28,"H":12,"N":2,"O":8},2),
            ({"C":18,"H":6,"O":8},2),
        ],
    },
    "ii": {
        "atoms": 84,
        "elements": {"C":48,"H":20,"O":12,"Zn":2,"N":2},
        "total_bonds": 101,
        "bonds": {
            "C-C":55, "C-H":18, "C-N":4, "C-O":12,
            "H-O":2, "N-Zn":2, "O-Zn":8,
        },
        "components": [
            ({"C":26,"H":12,"N":2,"O":4},2),
            ({"C":22,"H":8,"O":8},2),
        ],
    },
}

# Mapping:
# E_i a -> E_ii c
# E_i b -> E_ii a
# E_i c -> E_ii b
#
# Direction coefficients (h,k,l)_Ei -> (k,l,h)_Eii
# Replication          (x,y,z)_Ei -> (y,z,x)_Eii
CASES = [
    # label, vi, vii, rep_i, rep_ii
    ("P1_a_to_c__111",        (1,0,0), (0,0,1), (1,1,1), (1,1,1)),
    ("P1_a_to_c__plane22",    (1,0,0), (0,0,1), (1,2,2), (2,2,1)),

    ("P2_b_to_a__111",        (0,1,0), (1,0,0), (1,1,1), (1,1,1)),
    ("P2_b_to_a__plane22",    (0,1,0), (1,0,0), (2,1,2), (1,2,2)),

    ("P3_c_to_b__111",        (0,0,1), (0,1,0), (1,1,1), (1,1,1)),
    ("P3_c_to_b__plane22",    (0,0,1), (0,1,0), (2,2,1), (2,1,2)),

    ("D1_abc_plus__111",      (1,1,1), (1,1,1), (1,1,1), (1,1,1)),
    ("D2_abc_mixed__111",     (1,-1,1), (-1,1,1), (1,1,1), (1,1,1)),
]

PALETTE = {
    "H":  (0.92,0.92,0.92),
    "C":  (0.29,0.29,0.29),
    "N":  (0.16,0.36,0.78),
    "O":  (0.84,0.20,0.20),
    "Zn": (0.26,0.50,0.72),
}

RADII = {
    "H":0.10,
    "C":0.26,
    "N":0.32,
    "O":0.32,
    "Zn":0.58,
}

BOND_WIDTH = 0.11
BOND_COLOR = (0.50,0.50,0.50)
IMAGE_SIZE = (3200,2400)
DPI = 600
PAIR_MARGIN = 1.06
