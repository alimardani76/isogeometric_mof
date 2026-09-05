# Data

This folder contains only small processed tables that were verified as inputs or outputs of the Step 3 and Step 4 production scripts.

Included subfolders:

- `figure_source_data/`: historical CSV/JSON/TXT figure-source package produced by the audited Step 3 source-building workflow. It is retained for provenance and is not the canonical source layer for the final selected-case RASPA Figure 6.
- `si_source_data/`: CSV source copies used by `10_build_lean_si_package.py`.
- `case_selection/`: Step 3 case-selection tables and manifests.
- `case_chemistry/`: Step 3 selected-case charge tables and manifests; no CIFs.
- `step4_case_chemistry/`: the Phase 2C and Phase 2E selected-case synthesis/decision files needed by later Figure 5 variants.

## Canonical publication-figure inputs

The finalized quantitative/RASPA publication renderer uses frozen compact
source tables under `../reproduce/figures/data/`.

Current selected-case RASPA publication records are also exposed under
`../validation/raspa/data/`, with final panel-level manifests/source tables
under `../provenance/publication_figures/`.

In particular, historical `figure_source_data/Figure_06/` material belongs to
the earlier audited figure architecture and must not be mistaken for the
canonical final selected-case RASPA Figure 6 source layer.

These files are processed outputs derived from the local project. Their presence here does not establish a redistribution license. Before public release, review the upstream ARC-MOF terms and decide whether these derived tables may be distributed.

Not included:

- any file from the audited `raw/` folder;
- the ARC-MOF compressed archive;
- CIF structure files from `analysis/final_structure_case_inspection` or the frozen handoff package;
- large analysis Parquet files and intermediate shards.

Source paths and hashes are recorded under `provenance/`.
