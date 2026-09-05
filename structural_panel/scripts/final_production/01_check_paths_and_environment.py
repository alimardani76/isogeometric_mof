from pathlib import Path
import os

def detect_root():
    env = os.environ.get("P7B_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if not p.exists():
            raise SystemExit(f"P7B_ROOT is set but does not exist: {p}")
        return p
    return Path(__file__).resolve().parents[2]


def main():
    root = detect_root()
    print("="*90)
    print("DETECTED PROJECT ROOT")
    print(root)
    print("="*90)

    cif_root = root / "data" / "cifs"
    if not cif_root.exists():
        cif_root = root / "CIF_by_panel"

    req = [
        cif_root / "A_strong_linker_process_aligned",
        cif_root / "B_strong_metal_process_aligned",
        cif_root / "C_cu_zn_pressure_exception",
        cif_root / "D_near_null_comparison",
        cif_root / "E_process_discordant_comparison",
        cif_root / "F_functional_motif_example",
    ]
    missing = [str(p) for p in req if not p.exists()]
    if missing:
        print("Missing required folders:")
        for m in missing:
            print("  -", m)
        raise SystemExit(1)

    try:
        import ovito
        print("OVITO import: OK")
    except Exception as exc:
        raise SystemExit(
            "Cannot import OVITO in this Python environment.\n"
            "Activate the ovito_render environment first.\n"
            f"Original error: {exc}"
        )

    print("All required panel CIF folders exist.")
    print("Ready to run final HR rendering.")

if __name__ == "__main__":
    main()
