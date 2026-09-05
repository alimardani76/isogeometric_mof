"""Panel F configuration."""

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
CIF_DIR = CIF_ROOT / "F_functional_motif_example"
F_I = CIF_DIR / "F_i__DB0-m9_o17_o27_f0_sra.sym.117.cif"
F_II = CIF_DIR / "F_ii__DB0-m9_o17_o27_f0_sra.sym.116.cif"

OUT_ROOT = ROOT / "OVITO_screening"
OUT_DIR = OUT_ROOT / "50_F_whole_geometry"

F_PAIRWISE_CUTOFFS = {
    ("C","C"): 1.65,
    ("C","H"): 1.20,
    ("C","N"): 1.50,
    ("C","O"): 1.50,
    ("N","N"): 1.40,
    ("V","O"): 2.15,
}

EXPECTED = {
    "i": {
        "atoms": 134,
        "elements": {"O":20,"C":70,"V":4,"H":30,"N":10},
        "total_bonds": 160,
        "bonds": {"C-C":76,"C-H":30,"C-N":10,"C-O":16,"N-N":4,"O-V":24},
        "cyano_count": 2,
        "organic_components": [
            ({"C":17,"H":7,"N":5,"O":4},4),
            ({"C":17,"H":7,"N":5,"O":4},4),
            ({"C":18,"H":8,"O":4},4),
            ({"C":18,"H":8,"O":4},4),
        ],
        "cyano_component_signatures": [
            {"C":17,"H":7,"N":5,"O":4},
            {"C":17,"H":7,"N":5,"O":4},
        ],
    },
    "ii": {
        "atoms": 134,
        "elements": {"O":20,"C":70,"V":4,"H":30,"N":10},
        "total_bonds": 160,
        "bonds": {"C-C":76,"C-H":30,"C-N":10,"C-O":16,"N-N":4,"O-V":24},
        "cyano_count": 2,
        "organic_components": [
            ({"C":17,"H":7,"N":5,"O":4},4),
            ({"C":16,"H":8,"N":4,"O":4},4),
            ({"C":19,"H":7,"N":1,"O":4},4),
            ({"C":18,"H":8,"O":4},4),
        ],
        "cyano_component_signatures": [
            {"C":17,"H":7,"N":5,"O":4},
            {"C":19,"H":7,"N":1,"O":4},
        ],
    },
}

# label, view, up, replication
CASES = [
    ("A1_a_up_c__111",      (1,0,0), (0,0,1), (1,1,1)),
    ("A2_a_up_c__plane22",  (1,0,0), (0,0,1), (1,2,2)),
    ("A3_a_up_b__plane22",  (1,0,0), (0,1,0), (1,2,2)),

    ("B1_b_up_c__111",      (0,1,0), (0,0,1), (1,1,1)),
    ("B2_b_up_c__plane22",  (0,1,0), (0,0,1), (2,1,2)),

    ("C1_c_up_b__111",      (0,0,1), (0,1,0), (1,1,1)),
    ("C2_c_up_b__plane22",  (0,0,1), (0,1,0), (2,2,1)),

    ("D1_abc_up_c__111",    (1,1,1), (0,0,1), (1,1,1)),
]

PALETTE = {
    "H": (0.92,0.92,0.92),
    "C": (0.29,0.29,0.29),
    "N": (0.15,0.36,0.78),
    "O": (0.84,0.20,0.20),
    "V": (0.38,0.56,0.70),
}

RADII = {
    "H":0.10,
    "C":0.25,
    "N":0.32,
    "O":0.32,
    "V":0.58,
}

BOND_WIDTH = 0.11
BOND_COLOR = (0.50,0.50,0.50)
IMAGE_SIZE = (3200,2400)
DPI = 600
PAIR_MARGIN = 1.06
