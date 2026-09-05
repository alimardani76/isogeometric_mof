from __future__ import annotations
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from .style import TARGET_ORDER, condition_label

ROOT = Path(__file__).resolve().parents[1]
DATA_MAIN = ROOT / "data" / "main"
DATA_SI = ROOT / "data" / "si"
DATA_RASPA = ROOT / "data" / "raspa"
OUT_MAIN = ROOT / "outputs" / "main"
OUT_SI = ROOT / "outputs" / "si"


def read_main(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_MAIN / name, low_memory=False)


def read_si(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_SI / name, low_memory=False)


def read_raspa(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_RASPA / name, low_memory=False)


def ensure_cols(df: pd.DataFrame, cols: list[str], label: str = "data") -> None:
    miss = [c for c in cols if c not in df.columns]
    if miss:
        raise RuntimeError(f"{label} missing columns: {miss}")


def ordered_conditions(df: pd.DataFrame, target_col: str = "target", pressure_col: str = "p/bar") -> pd.DataFrame:
    d = df.copy()
    rank = {t: i for i, t in enumerate(TARGET_ORDER)}
    d["_target_rank"] = d[target_col].map(rank).fillna(999)
    d["_pressure_rank"] = pd.to_numeric(d[pressure_col], errors="coerce")
    d = d.sort_values(["_target_rank", "_pressure_rank"])
    d["condition_label"] = [condition_label(t, p) for t, p in zip(d[target_col], d[pressure_col])]
    return d.drop(columns=["_target_rank", "_pressure_rank"])


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_panel_source(df: pd.DataFrame, fig_dir: Path, panel: str) -> Path:
    p = fig_dir / f"source_panel_{panel.upper()}.csv"
    df.to_csv(p, index=False)
    return p


def write_manifest(fig_dir: Path, figure_name: str, inputs: list[Path], outputs: list[Path], panel_sources: list[Path], notes: dict | None = None) -> Path:
    from .style import RESOLVED_FONT
    payload = {
        "figure": figure_name,
        "font_resolved": RESOLVED_FONT,
        "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p)} for p in inputs],
        "panel_sources": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p)} for p in panel_sources],
        "outputs": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p)} for p in outputs],
        "notes": notes or {},
    }
    m = fig_dir / "manifest.json"
    m.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return m


def symmetric_limits(values, pad=0.08, minimum=0.05):
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return (-minimum, minimum)
    m = max(abs(arr.min()), abs(arr.max()), minimum)
    m *= (1 + pad)
    return (-m, m)
