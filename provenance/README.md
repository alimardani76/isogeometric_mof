# Provenance

Audit artifacts:

- `01_inventory_report.csv`: one row for each file in the nine user-specified source folders.
- `02_reproducibility_assets.md`: inspected scripts, workflow inputs/outputs, figure/table generators, datasets, manifests, configuration, and environment evidence.
- `raw_data_sha256.csv`: locally computed SHA-256 hashes for all 19 audited `raw/` files; no raw file is copied here.
- `draft_inclusion_manifest.csv`: exact repository-relative path, size, SHA-256, and inclusion reason for every committed candidate file except the manifest itself.
- `03_inclusion_exclusion.md`: inclusion and exclusion policy applied before the first commit.
- `output_hash_manifest.csv`: existing 107-row frozen-output hash manifest.
- `availability_matrix.csv`: existing list of explicitly unavailable/not-computed objects.
- `frozen_run_manifest.json`: existing frozen-package run manifest.
- `phase0_frozen_input_inventory.csv` and `phase0_manifest.json`: existing Step 4 input inventory and audit decision.
- `phase2a_toolchain.json`: existing runtime/toolchain record.
- `figure_06_manifest.json`: current canonical selected-case RASPA Figure 6 source/output manifest.
- `figure_07_manifest.json`: historical script-numbered manifest for the older
  structure-resolved Figure 5 renderer (`07_render_structure_case_figure.py`);
  it does **not** imply that the manuscript has a Figure 7 and is not canonical
  Figure 5 provenance.

## Canonical publication provenance

- `publication_figures/`: final per-figure manifests, exact panel-level source
  CSVs, and compact selected-case RASPA provenance used for manuscript-facing
  Figures 1-4, 6 and SI figures.
- `final_publication_asset_hashes.csv`: hashes for the finalized
  publication-facing asset/reproduction layer. This is **not** the final
  repository-wide release manifest; the repository-wide manifest must be
  generated only after the complete release tree is frozen.
- canonical Figure 5 provenance/reproduction is under `../structural_panel/`.

Historical records remain preserved below and in the other provenance files;
current canonical publication assets do not erase the historical audit trail.

## Raw ARC-MOF-derived source location

Audited location: `7B2/raw/`

Basenames:

- `all_topology_lists.csv`
- `ARCMOF_20241004.tar.gz`
- `ARC-MOF_Dim.csv`
- `flig-clusters.csv`
- `func-clusters.csv`
- `geo-clusters.csv`
- `geometric_properties.csv`
- `landfill-CH4.csv`
- `landfill-CO2.csv`
- `mc-clusters.csv`
- `methane.csv`
- `methane_purification-CH4.csv`
- `methane_purification-CO2.csv`
- `overall_process.csv`
- `post_comb_vsa-CO2.csv`
- `post_comb_vsa-N2.csv`
- `pre_comb_4040-CO2.csv`
- `pre_comb_4040-H2.csv`
- `RACs.csv`

No README, license, citation file, or provenance manifest was found in `raw/`. A name-only listing of `ARCMOF_20241004.tar.gz` produced no entry whose name matched README, license/licence, citation, copying, notice, or provenance. This does not prove that no relevant terms exist elsewhere; it means the audited files do not establish permission.

Required before public release: identify the authoritative ARC-MOF source, citation, version/date, access route, license or data-use terms, and whether the derived CSV/CIF artifacts may be redistributed. Keep raw data external unless those questions are resolved.
