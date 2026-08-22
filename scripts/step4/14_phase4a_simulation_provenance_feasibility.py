#!/usr/bin/env python3
"""
Project 7B Step 4 - Phase 4A
Simulation provenance and reproduction-feasibility audit.

Purpose
-------
Before any new GCMC density map, site-occupancy map, RDF, energy histogram, or
host-guest mechanistic visualization is generated, determine whether Project 7B
contains enough provenance to reproduce the ARC-MOF adsorption values for the
frozen selected structures.

This phase DOES NOT run RASPA or any molecular simulation.
It DOES NOT recompute adsorption or heat of adsorption.

The audit searches for:
- exact RASPA / MC input decks
- force-field and molecule definition files
- framework LJ model
- REPEAT charge use
- guest models
- mixing rules
- electrostatics / cutoff
- cycle counts and equilibration/production split
- framework rigidity
- simulation cell / supercell rule
- fugacity / EOS handling
- move probabilities
- selected-case temperatures/pressures/compositions
- raw logs / restart files / seeds / code version

READ ONLY with respect to Steps 1-3.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import pandas as pd

TITLE = "PROJECT 7B STEP 4 - PHASE 4A SIMULATION PROVENANCE / REPRODUCTION FEASIBILITY"

TEXT_EXTS = {
    ".py", ".txt", ".md", ".json", ".yaml", ".yml", ".toml", ".ini",
    ".sh", ".ps1", ".bat", ".cmd", ".inp", ".input", ".def", ".log",
    ".out", ".cfg", ".conf"
}

SIM_FILENAME_PATTERNS = [
    re.compile(r"simulation\.input$", re.I),
    re.compile(r"force[_-]?field.*\.def$", re.I),
    re.compile(r"pseudo[_-]?atoms.*\.def$", re.I),
    re.compile(r"molecule.*\.def$", re.I),
    re.compile(r".*\.def$", re.I),
    re.compile(r".*raspa.*", re.I),
    re.compile(r".*gcmc.*", re.I),
    re.compile(r".*monte.*carlo.*", re.I),
    re.compile(r".*adsorption.*input.*", re.I),
]

KEYWORDS = {
    "engine_raspa": [
        r"\bRASPA\b", r"RASPA2", r"RASPA3"
    ],
    "monte_carlo": [
        r"Grand\s+Canonical", r"\bGCMC\b", r"Monte\s+Carlo", r"SimulationType\s+MonteCarlo"
    ],
    "framework_uff": [
        r"\bUFF\b", r"Universal\s+Force\s+Field"
    ],
    "repeat_charges": [
        r"\bREPEAT\b", r"repeat_charge"
    ],
    "lorentz_berthelot": [
        r"Lorentz.?Berthelot", r"MixingRule\s+Lorentz"
    ],
    "cutoff": [
        r"CutOff", r"cutoff", r"12\.8"
    ],
    "ewald": [
        r"Ewald", r"ChargeMethod"
    ],
    "rigid_framework": [
        r"FlexibleFramework\s+no", r"rigid\s+framework", r"framework\s+was\s+held\s+rigid"
    ],
    "cycles": [
        r"NumberOfCycles", r"NumberOfInitializationCycles",
        r"10[\s,]*000\s+(?:MC\s+)?cycles", r"equilibration", r"production"
    ],
    "supercell": [
        r"UnitCells", r"replicat", r"supercell", r"cell\s+length"
    ],
    "fugacity": [
        r"fugacity", r"Peng.?Robinson", r"equation\s+of\s+state", r"\bEOS\b"
    ],
    "moves": [
        r"translation", r"rotation", r"reinsertion", r"swap", r"identity\s+change"
    ],
    "co2_model": [
        r"\bCO2\b", r"CO_?2", r"Garcia.?Sanchez"
    ],
    "n2_model": [
        r"\bN2\b", r"N_?2"
    ],
    "ch4_model": [
        r"\bCH4\b", r"CH_?4", r"Martin", r"Stubbs"
    ],
    "h2_model": [
        r"\bH2\b", r"H_?2", r"Belof"
    ],
    "seed": [
        r"RandomSeed", r"seed"
    ],
    "heat_of_adsorption": [
        r"heat\s+of\s+adsorption", r"enthalpy", r"Widom"
    ],
}

PROTOCOL_OBJECTS = [
    ("simulation_engine_version", "Exact engine and version/build used"),
    ("simulation_input_deck", "Exact RASPA simulation.input or equivalent"),
    ("framework_lj_parameters", "Framework Lennard-Jones force field"),
    ("framework_repeat_charges", "Exact framework partial charges"),
    ("guest_co2_definition", "Exact CO2 molecule/force-field definition"),
    ("guest_n2_definition", "Exact N2 molecule/force-field definition"),
    ("guest_ch4_definition", "Exact CH4 molecule/force-field definition"),
    ("guest_h2_definition", "Exact H2 molecule/force-field definition"),
    ("cross_interaction_rule", "Cross LJ combining rule"),
    ("dispersion_cutoff", "LJ cutoff"),
    ("electrostatics_method", "Long-range electrostatics method and settings"),
    ("framework_rigidity", "Rigid/flexible framework setting"),
    ("supercell_rule", "Replication rule / minimum cell dimensions"),
    ("cycle_counts", "Equilibration and production cycle counts"),
    ("cycle_definition", "Meaning of one MC cycle"),
    ("move_probabilities", "MC move set/probabilities"),
    ("fugacity_eos", "Pressure-to-fugacity / EOS treatment"),
    ("state_points", "Temperature, pressure and mixture composition"),
    ("random_seeds", "Random seeds or reproducible seed policy"),
    ("raw_simulation_logs", "Raw outputs/logs for reproduction comparison"),
    ("heat_of_adsorption_definition", "Exact HOA estimator/protocol"),
]


def find_root(start: Path) -> Path:
    p = start.resolve()
    for cand in [p] + list(p.parents):
        if (cand / "Step 3 results").exists() and (cand / "Step 4 extension").exists():
            return cand
    raise RuntimeError("Could not locate Project 7B root.")


def should_skip(p: Path) -> bool:
    low_parts = {x.lower() for x in p.parts}
    skip = {".git", "__pycache__", ".venv", "venv", "env", "node_modules"}
    if low_parts & skip:
        return True
    if "step 4 results" in low_parts or "step 4 extension" in low_parts:
        return True
    return False


def scan_text(path: Path):
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return []
    rows = []
    for name, patterns in KEYWORDS.items():
        for pat in patterns:
            rgx = re.compile(pat, re.I)
            for m in rgx.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                line = text.splitlines()[line_no - 1] if text.splitlines() else ""
                rows.append({
                    "path": str(path),
                    "keyword_group": name,
                    "pattern": pat,
                    "line": line_no,
                    "source_line": line.strip()[:1000],
                })
                # One hit per pattern/file is enough for provenance inventory.
                break
    return rows


def resolve_col(df: pd.DataFrame, candidates: list[str]):
    lower = {str(c).lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    for actual in df.columns:
        al = str(actual).lower()
        for c in candidates:
            cc = c.lower()
            if len(cc) >= 4 and cc in al:
                return actual
    return None


def state_point_inventory(path: Path):
    df = pd.read_csv(path, low_memory=False)
    candidates = {
        "mof": ["mof_id", "framework_id", "mof", "framework"],
        "guest": ["guest", "gas", "component", "species"],
        "temperature": ["temperature", "temperature_k", "temp_k"],
        "pressure": ["pressure", "pressure_bar", "pressure_pa", "pressure_kpa"],
        "composition": ["composition", "mole_fraction", "y", "feed_fraction"],
        "condition": ["condition", "condition_id", "adsorption_condition"],
        "uptake": ["uptake", "mmol/g", "mmol_g", "loading"],
        "hoa": ["hoa", "heat_of_adsorption", "enthalpy"],
    }

    rec = {
        "path": str(path),
        "rows": len(df),
        "columns": json.dumps([str(c) for c in df.columns]),
    }
    for k, opts in candidates.items():
        c = resolve_col(df, opts)
        rec[f"{k}_column"] = c
        if c:
            rec[f"{k}_unique"] = int(df[c].nunique(dropna=True))
            vals = df[c].dropna().astype(str).unique()[:25]
            rec[f"{k}_sample_values"] = json.dumps([str(v) for v in vals])
    return rec


def main():
    print(TITLE)
    print("=" * 72)

    root = find_root(Path.cwd())
    out = root / "Step 4 results" / "04_host_guest_maps" / "phase4a_simulation_provenance"
    out.mkdir(parents=True, exist_ok=True)

    scan_roots = [
        root / "raw",
        root / "analysis",
        root / "Step 1 computation",
        root / "Step 1 results",
        root / "Step 2 calculation",
        root / "Step 2 results",
        root / "Step 3 production",
        root / "Step 3 results",
    ]

    # 1. File-level simulation inventory.
    sim_files = []
    text_hits = []
    seen = set()

    for base in scan_roots:
        if not base.exists():
            continue

        for p in base.rglob("*"):
            if p in seen or not p.is_file() or should_skip(p):
                continue
            seen.add(p)

            name_match = any(r.search(p.name) for r in SIM_FILENAME_PATTERNS)
            if name_match:
                sim_files.append({
                    "path": str(p.relative_to(root)),
                    "size_bytes": p.stat().st_size,
                    "suffix": p.suffix.lower(),
                    "filename_match": True,
                })

            # Search only reasonably sized text/code/config files.
            if p.suffix.lower() in TEXT_EXTS and p.stat().st_size <= 20 * 1024 * 1024:
                hits = scan_text(p)
                for h in hits:
                    h["path"] = str(p.relative_to(root))
                text_hits.extend(hits)

    sim_df = pd.DataFrame(sim_files)
    hits_df = pd.DataFrame(text_hits)

    if not sim_df.empty:
        sim_df = sim_df.drop_duplicates("path").sort_values("path")
    if not hits_df.empty:
        hits_df = hits_df.sort_values(["keyword_group", "path", "line"])

    sim_df.to_csv(out / "phase4a_simulation_file_inventory.csv", index=False)
    hits_df.to_csv(out / "phase4a_protocol_keyword_hits.csv", index=False)

    # 2. Focused excerpts from highest-value protocol files.
    if not hits_df.empty:
        score_weights = {
            "engine_raspa": 10,
            "monte_carlo": 8,
            "framework_uff": 8,
            "repeat_charges": 7,
            "cycles": 7,
            "cutoff": 6,
            "ewald": 6,
            "lorentz_berthelot": 6,
            "rigid_framework": 5,
            "supercell": 5,
            "fugacity": 5,
            "moves": 4,
            "co2_model": 3,
            "n2_model": 3,
            "ch4_model": 3,
            "h2_model": 3,
            "heat_of_adsorption": 4,
            "seed": 2,
        }
        scored = (
            hits_df.assign(
                _score=hits_df["keyword_group"].map(score_weights).fillna(1)
            )
            .groupby("path", as_index=False)
            .agg(
                score=("_score", "sum"),
                keyword_groups=("keyword_group", lambda s: ";".join(sorted(set(s)))),
                n_hits=("keyword_group", "size"),
            )
            .sort_values(["score", "n_hits"], ascending=False)
        )
        scored.to_csv(out / "phase4a_protocol_file_ranking.csv", index=False)

        for rank, row in scored.head(12).reset_index(drop=True).iterrows():
            rel = Path(row["path"])
            p = root / rel
            try:
                lines = p.read_text(encoding="utf-8-sig", errors="replace").splitlines()
            except Exception:
                continue

            h = hits_df[hits_df["path"].eq(row["path"])]
            keep = set()
            for n in h["line"].astype(int):
                for j in range(max(1, n - 8), min(len(lines), n + 8) + 1):
                    keep.add(j)

            excerpt = []
            prev = None
            for j in sorted(keep):
                if prev is not None and j > prev + 1:
                    excerpt.append("\n...\n")
                excerpt.append(f"{j:5d}: {lines[j-1]}\n")
                prev = j

            (out / f"phase4a_protocol_excerpt_{rank+1:02d}.txt").write_text(
                "".join(excerpt), encoding="utf-8"
            )
    else:
        scored = pd.DataFrame()

    # 3. Selected-case frozen adsorption-condition sources.
    frozen = root / "Step 3 results" / "Paper7B_Hosein_to_Shayan_Frozen_Source_Package"
    state_candidates = [
        frozen / "08_structures" / "candidate_adsorption_conditions.csv",
        root / "analysis" / "final_structure_case_inspection" / "candidate_adsorption_conditions.csv",
    ]
    state_rows = []
    for p in state_candidates:
        if p.exists():
            try:
                rec = state_point_inventory(p)
                rec["path"] = str(p.relative_to(root))
                state_rows.append(rec)
            except Exception as exc:
                state_rows.append({
                    "path": str(p.relative_to(root)),
                    "read_error": f"{type(exc).__name__}: {exc}",
                })
    pd.DataFrame(state_rows).to_csv(out / "phase4a_selected_case_state_point_schema.csv", index=False)

    # 4. Search for raw ARC-MOF adsorption tables present locally.
    raw_names = [
        "methane.csv",
        "methane_purification-CH4.csv",
        "methane_purification-CO2.csv",
        "post_comb_vsa-CO2.csv",
        "post_comb_vsa-N2.csv",
        "pre_comb_4040-CO2.csv",
        "pre_comb_4040-H2.csv",
        "landfill-CH4.csv",
        "landfill-CO2.csv",
        "overall_process.csv",
    ]
    raw_inventory = []
    for name in raw_names:
        hits = []
        for base in scan_roots:
            if base.exists():
                hits.extend(base.rglob(name))
        hits = sorted(set(hits))
        raw_inventory.append({
            "basename": name,
            "found": bool(hits),
            "paths": json.dumps([str(p.relative_to(root)) for p in hits[:20]]),
        })
    pd.DataFrame(raw_inventory).to_csv(out / "phase4a_arc_mof_target_file_inventory.csv", index=False)

    # 5. Runtime feasibility only. No execution.
    executables = {
        "raspa": shutil.which("simulate") or shutil.which("raspa") or shutil.which("raspa2") or shutil.which("raspa3"),
        "python": shutil.which("python") or shutil.which("py"),
    }
    (out / "phase4a_runtime_inventory.json").write_text(
        json.dumps(executables, indent=2), encoding="utf-8"
    )

    # 6. Protocol-completeness map from LOCAL project evidence.
    hit_groups = set(hits_df["keyword_group"].astype(str)) if not hits_df.empty else set()
    sim_names = " ".join(sim_df["path"].astype(str).tolist()).lower() if not sim_df.empty else ""

    local_status = {
        "simulation_engine_version": "PARTIAL_KEYWORD_ONLY" if "engine_raspa" in hit_groups else "NOT_RECOVERED",
        "simulation_input_deck": "RECOVERED_FILE_CANDIDATE" if "simulation.input" in sim_names else "NOT_RECOVERED",
        "framework_lj_parameters": "PARTIAL_KEYWORD_ONLY" if "framework_uff" in hit_groups else "NOT_RECOVERED",
        "framework_repeat_charges": "RECOVERED_SELECTED_CIFS" if "repeat_charges" in hit_groups else "RECOVERED_SELECTED_CIFS",
        "guest_co2_definition": "RECOVERED_FILE_CANDIDATE" if ("co2" in sim_names and ".def" in sim_names) else ("PARTIAL_KEYWORD_ONLY" if "co2_model" in hit_groups else "NOT_RECOVERED"),
        "guest_n2_definition": "RECOVERED_FILE_CANDIDATE" if ("n2" in sim_names and ".def" in sim_names) else ("PARTIAL_KEYWORD_ONLY" if "n2_model" in hit_groups else "NOT_RECOVERED"),
        "guest_ch4_definition": "RECOVERED_FILE_CANDIDATE" if ("ch4" in sim_names and ".def" in sim_names) else ("PARTIAL_KEYWORD_ONLY" if "ch4_model" in hit_groups else "NOT_RECOVERED"),
        "guest_h2_definition": "RECOVERED_FILE_CANDIDATE" if ("h2" in sim_names and ".def" in sim_names) else ("PARTIAL_KEYWORD_ONLY" if "h2_model" in hit_groups else "NOT_RECOVERED"),
        "cross_interaction_rule": "PARTIAL_KEYWORD_ONLY" if "lorentz_berthelot" in hit_groups else "NOT_RECOVERED",
        "dispersion_cutoff": "PARTIAL_KEYWORD_ONLY" if "cutoff" in hit_groups else "NOT_RECOVERED",
        "electrostatics_method": "PARTIAL_KEYWORD_ONLY" if "ewald" in hit_groups else "NOT_RECOVERED",
        "framework_rigidity": "PARTIAL_KEYWORD_ONLY" if "rigid_framework" in hit_groups else "NOT_RECOVERED",
        "supercell_rule": "PARTIAL_KEYWORD_ONLY" if "supercell" in hit_groups else "NOT_RECOVERED",
        "cycle_counts": "PARTIAL_KEYWORD_ONLY" if "cycles" in hit_groups else "NOT_RECOVERED",
        "cycle_definition": "NOT_RECOVERED",
        "move_probabilities": "PARTIAL_KEYWORD_ONLY" if "moves" in hit_groups else "NOT_RECOVERED",
        "fugacity_eos": "PARTIAL_KEYWORD_ONLY" if "fugacity" in hit_groups else "NOT_RECOVERED",
        "state_points": "RECOVERED_SELECTED_CASE_TABLE" if state_rows else "NOT_RECOVERED",
        "random_seeds": "PARTIAL_KEYWORD_ONLY" if "seed" in hit_groups else "NOT_RECOVERED",
        "raw_simulation_logs": (
            "RECOVERED_FILE_CANDIDATE"
            if (not sim_df.empty and sim_df["suffix"].isin([".log", ".out"]).any())
            else "NOT_RECOVERED"
        ),
        "heat_of_adsorption_definition": "PARTIAL_KEYWORD_ONLY" if "heat_of_adsorption" in hit_groups else "NOT_RECOVERED",
    }

    comp_rows = []
    for obj, meaning in PROTOCOL_OBJECTS:
        comp_rows.append({
            "protocol_object": obj,
            "meaning": meaning,
            "local_project_status": local_status[obj],
            "required_for_exact_reproduction": True,
        })
    completeness = pd.DataFrame(comp_rows)
    completeness.to_csv(out / "phase4a_protocol_completeness_map.csv", index=False)

    exact_inputs = int((completeness["local_project_status"] == "RECOVERED_FILE_CANDIDATE").sum())
    partial = int(completeness["local_project_status"].str.startswith("PARTIAL").sum())
    not_recovered = int((completeness["local_project_status"] == "NOT_RECOVERED").sum())

    # Exact reproduction permission is deliberately strict.
    has_input = local_status["simulation_input_deck"] == "RECOVERED_FILE_CANDIDATE"
    guest_defs = all(
        local_status[x] == "RECOVERED_FILE_CANDIDATE"
        for x in [
            "guest_co2_definition", "guest_n2_definition",
            "guest_ch4_definition", "guest_h2_definition"
        ]
    )
    has_logs = local_status["raw_simulation_logs"] == "RECOVERED_FILE_CANDIDATE"

    if has_input and guest_defs and has_logs:
        decision = "CONDITIONAL_EXACT_INPUTS_PRESENT_REQUIRES_MANUAL_VALIDATION"
        next_step = "INSPECT_INPUT_DECKS_AND_REPRODUCE_ONE_STATE_POINT_BEFORE_DENSITY_MAPS"
    elif has_input:
        decision = "PARTIAL_INPUT_DECK_PRESENT_PROTOCOL_INCOMPLETE"
        next_step = "RECOVER_MISSING_FORCEFIELD/MOLECULE/LOG PROVENANCE BEFORE SIMULATION"
    else:
        decision = "NO_EXACT_REPRODUCTION_DECK_IN_PROJECT"
        next_step = "DO_NOT_RUN_GCMC_YET; EXTERNAL ARC-MOF PROTOCOL RECONSTRUCTION WOULD BE A NEW METHOD TASK"

    summary = {
        "decision": decision,
        "simulation_file_candidates": int(len(sim_df)),
        "protocol_keyword_hits": int(len(hits_df)),
        "high_value_protocol_files": int(len(scored)),
        "protocol_objects_exact_file_candidates": exact_inputs,
        "protocol_objects_partial_keyword_only": partial,
        "protocol_objects_not_recovered": not_recovered,
        "selected_case_state_point_tables": len(state_rows),
        "raspa_executable_in_path": executables["raspa"],
        "next_step": next_step,
    }
    (out / "phase4a_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    report = [
        "PROJECT 7B STEP 4 - PHASE 4A SIMULATION PROVENANCE AUDIT",
        "=" * 72,
        "",
        f"Decision: {decision}",
        "",
        "Interpretation",
        "--------------",
        "A density map is not an independent scientific object: it inherits the force field,",
        "charges, guest model, state point, supercell, MC protocol, and software implementation.",
        "Therefore no host-guest mechanism visualization should be generated until the frozen",
        "ARC-MOF uptake can be reproduced under the intended protocol.",
        "",
        f"Next: {next_step}",
    ]
    (out / "phase4a_report.md").write_text("\n".join(report), encoding="utf-8")

    print(f"Decision: {decision}")
    print(f"Simulation/input file candidates: {len(sim_df)}")
    print(f"Protocol keyword hits: {len(hits_df)}")
    print(f"Ranked protocol-bearing files: {len(scored)}")
    print(f"Protocol objects with exact file candidates: {exact_inputs}")
    print(f"Protocol objects with only partial textual evidence: {partial}")
    print(f"Protocol objects not recovered locally: {not_recovered}")
    print(f"Selected-case state-point tables recovered: {len(state_rows)}")
    print(f"RASPA executable in PATH: {executables['raspa']}")

    if not scored.empty:
        print("\nTop local protocol-bearing files:")
        for _, r in scored.head(10).iterrows():
            print(
                f"  {r['path']} | score={int(r['score'])} | "
                f"{r['keyword_groups']}"
            )

    print(f"\nNext: {next_step}")
    print("No molecular simulation was run and no adsorption/HOA value was recomputed.")
    print(f"Outputs: {out}")


if __name__ == "__main__":
    main()
