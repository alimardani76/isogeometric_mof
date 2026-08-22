from __future__ import annotations

import csv
import hashlib
import importlib
import json
import os
import platform
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

TITLE = "PROJECT 7B STEP 4 - PHASE 2A CIF / LOCAL-CHEMISTRY PREFLIGHT"


def find_project_root(start: Path) -> Path:
    p = start.resolve()
    for cand in [p] + list(p.parents):
        if (cand / "Step 3 results").exists() and (cand / "Step 4 extension").exists():
            return cand
    raise RuntimeError("Could not locate project root containing 'Step 3 results' and 'Step 4 extension'.")


def sha256(path: Path, block: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(block)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def import_version(module_name: str):
    try:
        m = importlib.import_module(module_name)
        version = getattr(m, "__version__", None)
        if version is None:
            try:
                from importlib.metadata import version as pkg_version
                version = pkg_version(module_name)
            except Exception:
                version = "unknown"
        return True, str(version), None
    except Exception as exc:
        return False, None, f"{type(exc).__name__}: {exc}"


def resolve_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower = {str(c).lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    # modest fuzzy fallback
    for actual in df.columns:
        al = str(actual).lower()
        for c in candidates:
            if c.lower() in al:
                return actual
    return None


def normalize_id(x: str) -> str:
    s = str(x).strip()
    if s.lower().endswith(".cif"):
        s = s[:-4]
    return s


def inventory_files(root: Path, patterns: tuple[str, ...]) -> list[dict]:
    rows = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        low = p.name.lower()
        if any(key in low for key in patterns):
            rows.append({
                "path": str(p.relative_to(root)),
                "basename": p.name,
                "bytes": p.stat().st_size,
                "sha256": sha256(p),
            })
    return rows


def parse_cif_with_pymatgen(path: Path):
    from pymatgen.core import Structure
    s = Structure.from_file(str(path))
    counts = Counter(str(site.specie.symbol) if hasattr(site.specie, "symbol") else str(site.specie) for site in s)
    return {
        "parser": "pymatgen",
        "n_sites": len(s),
        "elements": ";".join(sorted(counts)),
        "element_counts": json.dumps(dict(sorted(counts.items())), sort_keys=True),
        "volume_A3": float(s.volume),
        "density_g_cm3": float(s.density),
    }


def parse_cif_with_gemmi(path: Path):
    import gemmi
    doc = gemmi.cif.read_file(str(path))
    block = doc.sole_block()
    st = gemmi.make_small_structure_from_block(block)
    counts = Counter(str(site.element.name) for site in st.sites)
    # SmallStructure has cell.volume
    return {
        "parser": "gemmi",
        "n_sites": len(st.sites),
        "elements": ";".join(sorted(counts)),
        "element_counts": json.dumps(dict(sorted(counts.items())), sort_keys=True),
        "volume_A3": float(st.cell.volume),
        "density_g_cm3": None,
    }


def main():
    print(TITLE)
    print("=" * 72)

    root = find_project_root(Path.cwd())
    frozen = root / "Step 3 results" / "Paper7B_Hosein_to_Shayan_Frozen_Source_Package"
    if not frozen.exists():
        raise RuntimeError(f"Frozen handoff package not found: {frozen}")

    out = root / "Step 4 results" / "02_cif_chemistry" / "phase2a_preflight"
    out.mkdir(parents=True, exist_ok=True)

    toolchain = {
        "python": sys.version,
        "platform": platform.platform(),
        "project_root": str(root),
        "frozen_package": str(frozen),
        "packages": {},
        "executables": {},
    }
    for mod in ["pandas", "numpy", "pymatgen", "gemmi"]:
        ok, ver, err = import_version(mod)
        toolchain["packages"][mod] = {"available": ok, "version": ver, "error": err}

    crystalnn_ok = False
    crystalnn_err = None
    chemenv_ok = False
    chemenv_err = None
    if toolchain["packages"]["pymatgen"]["available"]:
        try:
            from pymatgen.analysis.local_env import CrystalNN  # noqa: F401
            crystalnn_ok = True
        except Exception as exc:
            crystalnn_err = f"{type(exc).__name__}: {exc}"
        try:
            from pymatgen.analysis.chemenv.coordination_environments.coordination_geometry_finder import LocalGeometryFinder  # noqa: F401
            chemenv_ok = True
        except Exception as exc:
            chemenv_err = f"{type(exc).__name__}: {exc}"
    toolchain["packages"]["CrystalNN"] = {"available": crystalnn_ok, "error": crystalnn_err}
    toolchain["packages"]["ChemEnv_LocalGeometryFinder"] = {"available": chemenv_ok, "error": chemenv_err}

    for exe in ["network", "zeo++", "raspa3", "simulate", "raspa"]:
        toolchain["executables"][exe] = shutil.which(exe)

    (out / "phase2a_toolchain.json").write_text(json.dumps(toolchain, indent=2), encoding="utf-8")

    chem_inv = inventory_files(
        frozen,
        ("coord", "crystalnn", "chemenv", "charge", "chem", "disorder", "cif", "case", "atom")
    )
    pd.DataFrame(chem_inv).sort_values(["basename", "path"]).to_csv(out / "phase2a_existing_chemistry_file_inventory.csv", index=False)

    # Canonical selected-structure paths
    cifs_dir = frozen / "08_structures" / "cifs_selected"
    if not cifs_dir.exists():
        # documented fallback search, but frozen package remains canonical
        hits = [p for p in frozen.rglob("cifs_selected") if p.is_dir()]
        if not hits:
            raise RuntimeError("No cifs_selected directory found in frozen handoff package.")
        cifs_dir = hits[0]
    cif_files = sorted(cifs_dir.glob("*.cif"))

    case_framework_file = frozen / "08_structures" / "02_final_case_frameworks.csv"
    expected_ids = set()
    case_framework_df = None
    if case_framework_file.exists():
        case_framework_df = pd.read_csv(case_framework_file)
        id_col = resolve_col(case_framework_df, ["mof_id", "framework_id", "mof", "framework"])
        if id_col:
            expected_ids = {normalize_id(v) for v in case_framework_df[id_col].dropna().astype(str)}

    cif_ids = {normalize_id(p.stem) for p in cif_files}

    # Parse CIFs independently. Prefer pymatgen because Phase 2 intends to use pymatgen local-env tools;
    # use gemmi only as an independent fallback.
    can_pmg = toolchain["packages"]["pymatgen"]["available"]
    can_gemmi = toolchain["packages"]["gemmi"]["available"]
    parse_rows = []
    for p in cif_files:
        row = {
            "cif_file": p.name,
            "cif_id_from_filename": normalize_id(p.stem),
            "bytes": p.stat().st_size,
            "sha256": sha256(p),
            "parse_ok": False,
            "parser": None,
            "n_sites": None,
            "elements": None,
            "element_counts": None,
            "volume_A3": None,
            "density_g_cm3": None,
            "error": None,
        }
        try:
            if can_pmg:
                d = parse_cif_with_pymatgen(p)
            elif can_gemmi:
                d = parse_cif_with_gemmi(p)
            else:
                raise RuntimeError("Neither pymatgen nor gemmi is installed; cannot independently parse CIFs.")
            row.update(d)
            row["parse_ok"] = True
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
        parse_rows.append(row)
    parse_df = pd.DataFrame(parse_rows)

    # Existing atom-charge mapping cross-check
    atom_charge_file = frozen / "06_cif_chemistry" / "03_atom_charge_rows.csv"
    charge_audit_file = frozen / "06_cif_chemistry" / "03_charge_mapping_audit.csv"
    atom_df = pd.read_csv(atom_charge_file) if atom_charge_file.exists() else pd.DataFrame()
    charge_audit_df = pd.read_csv(charge_audit_file) if charge_audit_file.exists() else pd.DataFrame()

    cross_rows = []
    charge_id_col = resolve_col(atom_df, ["mof_id", "framework_id", "mof", "framework"]) if not atom_df.empty else None
    elem_col = resolve_col(atom_df, ["element", "site_symbol", "atom_symbol", "species"]) if not atom_df.empty else None
    charge_col = resolve_col(atom_df, ["charge", "repeat_charge", "partial_charge"]) if not atom_df.empty else None
    occ_col = resolve_col(atom_df, ["occupancy", "occ"]) if not atom_df.empty else None

    for _, r in parse_df.iterrows():
        cid = r["cif_id_from_filename"]
        sub = pd.DataFrame()
        if charge_id_col:
            mask = atom_df[charge_id_col].astype(str).map(normalize_id).eq(cid)
            sub = atom_df.loc[mask]
        cross = {
            "cif_id": cid,
            "parse_ok": bool(r["parse_ok"]),
            "cif_n_sites": r["n_sites"],
            "charge_rows": int(len(sub)),
            "site_count_matches_charge_rows": None,
            "charge_numeric_fraction": None,
            "occupancy_nonnull_fraction": None,
            "charge_elements": None,
        }
        if r["parse_ok"] and r["n_sites"] is not None and charge_id_col:
            cross["site_count_matches_charge_rows"] = int(r["n_sites"]) == len(sub)
        if not sub.empty and charge_col:
            cross["charge_numeric_fraction"] = float(pd.to_numeric(sub[charge_col], errors="coerce").notna().mean())
        if not sub.empty and occ_col:
            cross["occupancy_nonnull_fraction"] = float(sub[occ_col].notna().mean())
        if not sub.empty and elem_col:
            cross["charge_elements"] = ";".join(sorted(set(sub[elem_col].dropna().astype(str))))
        cross_rows.append(cross)

    cross_df = pd.DataFrame(cross_rows)
    parse_df.to_csv(out / "phase2a_structure_parse_audit.csv", index=False)
    cross_df.to_csv(out / "phase2a_cif_charge_crosscheck.csv", index=False)

    # Identify existing coordination-like files anywhere in project (provenance scan only)
    project_coord = []
    patterns = ("coordination", "crystalnn", "chemenv", "local_env", "neighbor")
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        # avoid pycache and Step 4 generated outputs in the discovery table
        rel = str(p.relative_to(root))
        if "__pycache__" in rel:
            continue
        if any(k in p.name.lower() for k in patterns):
            project_coord.append({
                "path": rel,
                "basename": p.name,
                "bytes": p.stat().st_size,
                "sha256": sha256(p),
            })
    pd.DataFrame(project_coord).to_csv(out / "phase2a_existing_coordination_outputs.csv", index=False)

    # Status logic
    fatal = []
    warnings = []
    if len(cif_files) == 0:
        fatal.append("No selected CIF files found in frozen package.")
    failed_parses = int((~parse_df["parse_ok"]).sum()) if not parse_df.empty else 0
    if failed_parses:
        fatal.append(f"{failed_parses} selected CIF(s) failed independent parsing.")

    if expected_ids:
        missing_cif_ids = sorted(expected_ids - cif_ids)
        extra_cif_ids = sorted(cif_ids - expected_ids)
        if missing_cif_ids:
            fatal.append(f"Expected framework IDs without matching CIF filename stems: {missing_cif_ids}")
        if extra_cif_ids:
            warnings.append(f"CIF filename stems not present in case-framework ID column: {extra_cif_ids}")
    else:
        warnings.append("Could not resolve framework ID column from 02_final_case_frameworks.csv; filename-ID reconciliation not enforced.")

    if not cross_df.empty and "site_count_matches_charge_rows" in cross_df:
        mism = cross_df["site_count_matches_charge_rows"].eq(False).sum()
        unknown = cross_df["site_count_matches_charge_rows"].isna().sum()
        if mism:
            fatal.append(f"{int(mism)} CIF(s) have site-count mismatch against atom charge rows.")
        if unknown:
            warnings.append(f"Site-count/charge-row match could not be evaluated for {int(unknown)} CIF(s).")

    if atom_df.empty:
        fatal.append("Frozen atom-level charge table is missing or unreadable.")
    elif charge_id_col is None:
        fatal.append("Could not identify framework ID column in atom-level charge table.")
    if charge_col is None and not atom_df.empty:
        warnings.append("Could not identify a charge column in atom-level charge table.")

    if not can_pmg:
        warnings.append("pymatgen is not installed; Phase 2B CrystalNN/ChemEnv work is blocked until installed, although CIF parsing may pass through gemmi.")
    else:
        if not crystalnn_ok:
            warnings.append("pymatgen is installed but CrystalNN import failed.")
        if not chemenv_ok:
            warnings.append("pymatgen is installed but ChemEnv LocalGeometryFinder import failed.")

    if not toolchain["executables"].get("network") and not toolchain["executables"].get("zeo++"):
        warnings.append("Zeo++ executable was not found in PATH. This does not block Phase 2B coordination analysis.")

    # Explicit evidence boundary table
    boundary_rows = [
        {
            "object": "selected_CIF_structure",
            "status": "EXISTING_VALIDATED" if not fatal else "CHECK",
            "what_it_can_support": "real atomic structure, composition, local coordination geometry after validated parsing",
            "what_it_cannot_support": "preferred adsorption site or host-guest mechanism by itself",
        },
        {
            "object": "REPEAT_atom_charges",
            "status": "EXISTING_VALIDATED" if not atom_df.empty else "MISSING",
            "what_it_can_support": "case-level electrostatic/charge fingerprints when row alignment passes",
            "what_it_cannot_support": "oxidation state, charge-transfer mechanism, or causal adsorption site assignment",
        },
        {
            "object": "CrystalNN_coordination",
            "status": "TOOL_READY" if crystalnn_ok else "TOOL_GAP",
            "what_it_can_support": "neighbor graph, coordination number/signature, first-shell structural comparison",
            "what_it_cannot_support": "adsorption-site occupancy or interaction energy",
        },
        {
            "object": "ChemEnv_coordination_geometry",
            "status": "TOOL_READY" if chemenv_ok else "TOOL_GAP",
            "what_it_can_support": "coordination-environment classification and distortion-aware cross-check",
            "what_it_cannot_support": "guest binding preference",
        },
        {
            "object": "atom_specific_pore_facing_accessibility",
            "status": "NOT_YET_DEFINED",
            "what_it_can_support": "nothing until a probe, radii convention, periodic accessibility rule, and validation test are predeclared",
            "what_it_cannot_support": "must not be inferred merely from global Zeo++ accessible volume/surface area",
        },
        {
            "object": "adsorption_density_or_site_occupancy",
            "status": "EXTENDED_ONLY",
            "what_it_can_support": "guest spatial probability/site occupation when produced by validated host-guest simulation",
            "what_it_cannot_support": "not available from static CIF/charge data",
        },
    ]
    pd.DataFrame(boundary_rows).to_csv(out / "phase2a_evidence_boundary.csv", index=False)

    decision = "PASS" if not fatal else "FAIL"
    summary = {
        "decision": decision,
        "selected_cifs": len(cif_files),
        "expected_case_framework_ids": len(expected_ids),
        "cifs_parsed": int(parse_df["parse_ok"].sum()) if not parse_df.empty else 0,
        "cif_parse_failures": failed_parses,
        "atom_charge_rows": int(len(atom_df)),
        "charge_mapping_audit_rows": int(len(charge_audit_df)),
        "existing_coordination_files_found": len(project_coord),
        "pymatgen_available": can_pmg,
        "crystalnn_available": crystalnn_ok,
        "chemenv_available": chemenv_ok,
        "fatal_issues": fatal,
        "warnings": warnings,
    }
    (out / "phase2a_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md = [
        "# Phase 2A decision",
        "",
        f"**Decision: {decision}**",
        "",
        "This phase performs only structural/chemistry preflight and independent validation. It does not compute adsorption effects or create a new manuscript claim.",
        "",
        f"- Selected CIFs found: {len(cif_files)}",
        f"- Expected case-framework IDs resolved: {len(expected_ids)}",
        f"- CIFs independently parsed: {int(parse_df['parse_ok'].sum()) if not parse_df.empty else 0}",
        f"- Atom-level charge rows: {len(atom_df)}",
        f"- Existing coordination-related project files found: {len(project_coord)}",
        f"- pymatgen available: {can_pmg}",
        f"- CrystalNN available: {crystalnn_ok}",
        f"- ChemEnv available: {chemenv_ok}",
        "",
        "## Fatal issues",
    ]
    md += [f"- {x}" for x in fatal] if fatal else ["- None"]
    md += ["", "## Warnings"]
    md += [f"- {x}" for x in warnings] if warnings else ["- None"]
    md += [
        "",
        "## Gate for Phase 2B",
        "Phase 2B may begin only if this preflight passes and CrystalNN is available. ChemEnv is preferred as an independent coordination-geometry cross-check. Atom-specific pore-facing accessibility remains undefined and must not be added until its geometric/probe definition is separately audited.",
    ]
    (out / "PHASE2A_DECISION.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Decision: {decision}")
    print(f"Selected CIFs found: {len(cif_files)}")
    print(f"Expected case-framework IDs: {len(expected_ids)}")
    print(f"CIFs parsed independently: {int(parse_df['parse_ok'].sum()) if not parse_df.empty else 0}")
    print(f"Atom-level charge rows: {len(atom_df)}")
    print(f"Existing coordination-related files found: {len(project_coord)}")
    print(f"pymatgen / CrystalNN / ChemEnv: {can_pmg} / {crystalnn_ok} / {chemenv_ok}")
    print(f"Fatal issues: {len(fatal)}")
    print(f"Warnings: {len(warnings)}")
    for w in warnings:
        print(f"  WARN: {w}")
    for f in fatal:
        print(f"  FATAL: {f}")
    print("No adsorption effect, matching, bootstrap, pair selection, or process result was recomputed.")
    print(f"Outputs: {out}")


if __name__ == "__main__":
    main()
