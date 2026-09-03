"""Panel A configuration."""

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
CIF_DIR = CIF_ROOT / "A_strong_linker_process_aligned"
A_I = CIF_DIR / "A_i__DB0-m3_o11_o17_f0_pcu.sym.32.cif"
A_II = CIF_DIR / "A_ii__DB0-m3_o12_o20_f0_pcu.sym.24.cif"

OUT_ROOT = ROOT / "OVITO_screening"
OUT_DIR = OUT_ROOT / "30_A_geometry_111"

A_PAIRWISE_CUTOFFS = {
    ("C","C"): 1.70,
    ("C","H"): 1.20,
    ("C","N"): 1.50,
    ("C","O"): 1.50,
    ("N","H"): 1.10,
    ("N","O"): 1.45,
    ("O","H"): 1.10,
    ("Zn","O"): 2.30,
    ("Zn","N"): 2.20,
}

EXPECTED = {
    "i": {
        "atoms": 56,
        "elements": {"O":10, "C":26, "Zn":2, "H":15, "N":3},
        "total_bonds": 63,
        "bonds": {
            "C-C":27, "C-H":13, "C-N":3, "C-O":8,
            "H-N":2, "N-O":2, "O-Zn":8
        },
        "nitro_N": 1,
        "NH_N": 2,
    },
    "ii": {
        "atoms": 44,
        "elements": {"O":16, "C":16, "Zn":2, "H":4, "N":6},
        "total_bonds": 47,
        "bonds": {
            "C-C":13, "C-H":2, "C-N":6, "C-O":8,
            "H-N":2, "N-O":8, "O-Zn":8
        },
        "nitro_N": 4,
        "NH_N": 2,
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

PALETTE = {
    "H":  (0.92,0.92,0.92),
    "C":  (0.30,0.30,0.30),
    "N":  (0.22,0.40,0.78),
    "O":  (0.84,0.20,0.20),
    "Zn": (0.28,0.50,0.72),
}
RADII = {
    "H": 0.10,
    "C": 0.25,
    "N": 0.31,
    "O": 0.31,
    "Zn":0.56,
}

BOND_WIDTH = 0.11
BOND_COLOR = (0.50,0.50,0.50)
IMAGE_SIZE = (3200,2400)
DPI = 600
PAIR_MARGIN = 1.07


# Panel A basis correspondence inferred from the cell metrics and Zn positions.
#
# A_i:  a≈15.08, b≈11.11, c≈9.91 Å
# A_ii: a≈10.02, b≈11.38, c≈14.53 Å
#
# Thus the fair structural comparison is approximately:
#       A_i a  <-> A_ii c
#       A_i b  <-> A_ii b
#       A_i c  <-> A_ii a
#
# Replication counts must be permuted the same way:
#       (rx,ry,rz)_i <-> (rz,ry,rx)_ii
A_BASIS_MAP_NOTE = "A_i(a,b,c) ~ A_ii(c,b,a)"

A_MAPPED_CASES = [
    # name, A_i view, A_ii view, A_i rep, A_ii rep
    ("M1_a_to_c__111",
     (1,0,0), (0,0,1), (1,1,1), (1,1,1)),
    ("M1_a_to_c__plane22",
     (1,0,0), (0,0,1), (1,2,2), (2,2,1)),

    ("M2_b_to_b__111",
     (0,1,0), (0,1,0), (1,1,1), (1,1,1)),
    ("M2_b_to_b__plane22",
     (0,1,0), (0,1,0), (2,1,2), (2,1,2)),

    ("M3_c_to_a__111",
     (0,0,1), (1,0,0), (1,1,1), (1,1,1)),
    ("M3_c_to_a__plane22",
     (0,0,1), (1,0,0), (2,2,1), (1,2,2)),
]
