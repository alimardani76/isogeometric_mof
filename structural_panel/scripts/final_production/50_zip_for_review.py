from pathlib import Path
import os, zipfile

def detect_root():
    env = os.environ.get("P7B_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if not p.exists():
            raise SystemExit(f"P7B_ROOT is set but does not exist: {p}")
        return p
    return Path(__file__).resolve().parents[2]


def main():
    root=detect_root()
    folder=root/"OVITO_final_insets_tight"
    if not folder.exists(): raise SystemExit(f"Missing folder: {folder}")
    out=root/"OVITO_final_insets_tight_REVIEW.zip"
    if out.exists(): out.unlink()
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(folder.rglob("*")):
            if p.is_file():
                z.write(p,arcname=str(Path("OVITO_final_insets_tight")/p.relative_to(folder)))
    print("Created:",out)

if __name__=="__main__":
    main()
