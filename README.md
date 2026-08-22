# isogeometric_mof

Draft reproducibility repository assembled from the audited Project 7B2 folders on 2026-08-22.

## Purpose

This repository draft inventories and packages the verified computational assets used by Project 7B2. Existing project documentation describes the work as geometry-controlled, observational chemistry contrasts. This draft does not add a scientific claim, method, citation, license, or data-use permission.

## Contents

- `data/`: small processed tables used by the figure, SI, case-selection, and selected-case chemistry workflows. Raw ARC-MOF-derived files and CIFs are not included.
- `scripts/`: unmodified copies of verified Python and batch workflow scripts, organized by their original project stage.
- `figures/`: generated main and supplementary figure files found in `Step 3 results`.
- `tables/`: generated LaTeX supplementary tables found in `Step 3 results/si_tables`.
- `environment/`: software versions and imports observed in scripts and run manifests. No installable environment definition was found.
- `provenance/`: the full audit inventory, reproducibility-assets report, source hashes/manifests, and release blockers.

## Audited reproduction workflow

The scripts were copied without rewriting, as required by the audit. They retain their original path assumptions and therefore describe the workflow in the original `7B2` layout rather than a directly runnable layout inside this draft.

1. Place the required source files in the original project-root `raw/` directory after independently resolving access and redistribution terms. The exact audited basenames and computed hashes are listed in `provenance/raw_data_sha256.csv`.
2. From `Step 1 computation`, run `RUN_STEP1.bat`. The batch file invokes scripts `01_build_cohort.py` through `25_inspect_structure_cases.py` in numeric order and writes to `analysis/`. It does not invoke `26_audit_heat_of_adsorption.py`.
3. Run the six scripts in `Step 2 chemistry strengthening` in numeric order. They read `analysis/` and selected raw adsorption CSVs and write under `Step 2 results/`.
4. Run the Step 3 scripts in numeric order: case preparation/freezing, charge audit, figure-source packaging, figure blueprint, figure rendering, SI registry, and SI packaging. The existing files do not prove which alternate `06` and `07` renderer produced the final files; see `provenance/02_reproducibility_assets.md`.
5. If the Step 4 audit layer is needed, run the numbered scripts in `Step 4 extension` in order. Existing Step 4 documentation states that these scripts read upstream Steps 1-3 and write to `Step 4 results/`.

The processed tables included here preserve the exact source copies associated with the quantitative figures and printed SI assets. The unmodified SI packaging script still expects the original upstream project layout. Figure 5 structure rendering also requires selected CIFs, which are deliberately excluded pending provenance and redistribution review.

## Software evidence

An audited run recorded Windows 11, Python 3.13.13, pandas 2.3.2, NumPy 1.26.4, pymatgen 2025.10.7, and matplotlib 3.10.5. The scripts also import PyArrow, SciPy, scikit-learn, and joblib, but audited version pins for those packages were not found. `gemmi` is optional in one renderer and was recorded as unavailable. See `environment/README.md`.

## Data provenance and ARC-MOF note

The project owner identified every file in the audited `raw/` folder as ARC-MOF-derived source data. No README, license, citation file, or provenance manifest was present in that folder, and no README/license/citation-named entry was found by listing the compressed archive. Consequently, this draft includes names, sizes, dates, and SHA-256 hashes only; it does not copy the raw files or selected CIFs and does not assert that they may be redistributed.

The existing Step 4 protocol-reconstruction script contains a literature citation and external-code candidate, but this audit did not independently validate those external sources and does not treat that script as a license for the data.

## Limitations and release blockers

- No project license or explicit code/data redistribution terms were found.
- No citation metadata file was found.
- No `requirements.txt`, Conda environment, lockfile, `pyproject.toml`, container file, or equivalent environment definition was found.
- The active Step 3 renderer variants cannot be proven because manifests record canonical script names but not script hashes, while alternate versions exist with nearby timestamps.
- The copied scripts use the original directory layout. They require either restoration to that layout or a separately reviewed path refactor before this draft is directly runnable.
- `Step 1 computation/26_audit_heat_of_adsorption.py` resolves its project root differently from neighboring Step 1 scripts and is not called by `RUN_STEP1.bat`; the corrected Step 2 copy was retained instead.
- The existing `Step 3 production/README.md` says the folder is empty even though it contains scripts and is therefore stale.
- Two additional top-level folders, `Step 5 results` and `Step 5 validation`, were observed but were outside the user-specified audit scope and are not represented here.
- This audit checked file presence, metadata, script-declared paths/imports, manifests, and selected text content. It did not rerun the scientific workflow or validate numerical results.

No GitHub remote is configured or used by this draft.
