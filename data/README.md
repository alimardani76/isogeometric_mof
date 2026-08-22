# Data

This folder contains only small processed tables that were verified as inputs or outputs of the Step 3 and Step 4 production scripts.

Included subfolders:

- `figure_source_data/`: CSV/JSON/TXT files packaged by `04_build_figure_source_package.py` for the six main-figure messages.
- `si_source_data/`: CSV source copies used by `10_build_lean_si_package.py`.
- `case_selection/`: Step 3 case-selection tables and manifests.
- `case_chemistry/`: Step 3 selected-case charge tables and manifests; no CIFs.
- `step4_case_chemistry/`: the Phase 2C and Phase 2E selected-case synthesis/decision files needed by later Figure 5 variants.

These files are processed outputs derived from the local project. Their presence here does not establish a redistribution license. Before public release, review the upstream ARC-MOF terms and decide whether these derived tables may be distributed.

Not included:

- any file from the audited `raw/` folder;
- the ARC-MOF compressed archive;
- CIF structure files from `analysis/final_structure_case_inspection` or the frozen handoff package;
- large analysis Parquet files and intermediate shards.

Source paths and hashes are recorded under `provenance/`.
