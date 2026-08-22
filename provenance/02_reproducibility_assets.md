# Reproducibility assets audit

Audit date: 2026-08-22. Scope: `analysis`, `raw`, `Step 1 computation`, `Step 2 chemistry strengthening`, `Step 2 results`, `Step 3 production`, `Step 3 results`, `Step 4 extension`, and `Step 4 results`.

## Inventory-level findings

- 17,024 files totaling approximately 3,454.6 MB were in scope.
- Extensions: 16,211 Parquet, 467 CSV, 101 CIF, 64 Python, 50 JSON, 40 TXT, 27 PYC, 23 Markdown, 10 TeX, 9 PDF, 9 PNG, 6 SVG, 2 ZIP, 2 LOG, 1 GZ, 1 BAT, and 1 JSONL.
- No notebooks (`.ipynb`) were found.
- No R, Julia, MATLAB, shell, or PowerShell analysis scripts were found.
- No BibTeX, LaTeX style/class, or main manuscript TeX file was found. Ten `.tex` files were found: nine generated SI tables plus one additional TeX file recorded in the inventory.
- No environment-definition or build-configuration file (`requirements`, Conda YAML, lockfile, `pyproject.toml`, setup file, Dockerfile) was found.
- No README was found in `analysis`, `raw`, Steps 1-2, or their results. Twenty-three Markdown files were found in Step 3/4 production and results.

## Step 1 result-generation scripts

All paths below are original project-relative paths. Unless stated otherwise, dependencies are Python plus pandas and NumPy; additional packages are named where imported.

| Script | Verified purpose | Principal declared inputs | Principal declared outputs |
|---|---|---|---|
| `01_build_cohort.py` | Build the framework cohort | raw geometry, dimensionality, topology, cluster, RAC, adsorption/process CSVs, and CIF archive listing | `analysis/framework_master.parquet`, `cohort_flow.csv` |
| `02_extract_cif_chemistry.py` | Extract CIF chemistry in parallel | raw archive, framework master | CIF chemistry Parquet, checkpoint/failure/summary CSVs |
| `03_build_candidate_pairs.py` | Build candidate pair-rule datasets | framework master, CIF chemistry | `full_pair_rules/`, restart shards/JSONL manifest, summary/profile CSVs; imports PyArrow |
| `04_check_metal_coordination.py` | Classify metal-pair coordination | metal-pair Parquet, raw CIF archive | coordination signatures/pair classifications and CSV audits; imports pymatgen |
| `05_group_related_pairs.py` | Assign dependence/evidence groups | classified metal pairs and linker/functional pair tables | stringent dependence ledger and evidence/family summaries |
| `06_integrate_adsorption.py.py` | Join adsorption outcomes to pairs | stringent ledger, nine raw adsorption CSVs | pair-condition Parquet and merge/missing summaries |
| `07_analyze_adsorption_contrasts.py` | Calculate direction-free contrast outputs | integrated pair-condition data and raw adsorption scales | final pair/group effect Parquets and summary CSVs |
| `08_analyze_unordered_metal_changes.py` | Summarize exact unordered metal changes | final pair effects | metal-change and pressure CSVs |
| `09_build_reciprocal_matches.py` | Build covariance-aware reciprocal matches | framework master, stringent ledger | reciprocal pairs, scaling/precision/support tables, run manifest; imports scikit-learn |
| `10_test_matching_robustness.py` | Compare full and reciprocal matching results | reciprocal pairs, final effects, full summaries | reciprocal effect tables and design comparison |
| `11_audit_topology_sources.py` | Audit topology provenance | framework master, stringent ledger | framework/pair provenance tables and conflict/summary CSVs |
| `12_test_topology_robustness.py` | Test high-confidence topology subset | topology pairs and final effects/summaries | class/metal pressure results and comparison/summary CSVs |
| `13_test_residual_geometry.py` | Test residual geometry associations | final pair effects | group Parquet and result/summary CSVs |
| `14_test_geometry_limits.py` | Evaluate fixed geometry tiers | framework/pair tables, scales, raw adsorption CSVs | caliper assignment Parquet and support/composition/effect/pressure/geometry summaries |
| `15_define_primary_pairs.py` | Freeze the primary pair catalogue | caliper assignments and dependence ledger | final primary pairs, counts, manifest |
| `16_build_same_chemistry_controls.py` | Build outcome-blind controls | framework/CIF chemistry, reciprocal scaling/precision | control pairs, contexts, summary, manifest; imports SciPy KD-tree |
| `17_compare_same_chemistry_controls.py` | Compare primary pairs with controls | caliper assignments, controls, scales, raw adsorption | common-support design, cell estimates, results, summary |
| `18_test_symmetric_control_matching.py` | Symmetric reciprocal/control robustness | reciprocal chemistry/control pairs, effects/scales, raw adsorption | design/cells/results/summary and manifest |
| `19_audit_boundary_cases.py` | Audit boundary cases and CIF quality | matching/topology/control outputs, CIF chemistry, raw archive | disagreement, CIF-quality, and summary CSVs |
| `20_audit_process_data.py` | Audit process fields | raw `overall_process.csv`, primary pairs | validity/coverage/invalid/missing tables and manifest |
| `21_analyze_process_translation.py` | Analyze frozen pairs against process outputs | raw process CSV, primary pairs | pair/group Parquets, summary/attrition CSVs, manifest |
| `22_audit_working_capacity.py` | Audit working-capacity provenance/algebra | raw process CSV plus local text search | numerical/text audit CSVs and manifest |
| `23_finalize_major_metal_results.py` | Assemble final supported metal outputs | process pair results, metal-pressure summary, primary pairs | final metal Parquets/CSVs and manifest |
| `24_select_structure_cases.py` | Create auditable case shortlists | primary pairs/effects/process and CIF-quality audit | shortlist, pair summary, selection summary, unavailable summary, manifest |
| `25_inspect_structure_cases.py` | Build candidate inspection package | shortlist plus framework, CIF, coordination, adsorption, and process data | candidate tables, selected CIF copies, review sheet, failures, manifest; imports pymatgen |

`RUN_STEP1.bat` invokes scripts 01-25 sequentially and logs to `analysis/RUN_STEP1.log`. It requires Windows batch and Python on `PATH`. It does not call `26_audit_heat_of_adsorption.py`.

`26_audit_heat_of_adsorption.py` is a duplicate audit candidate but is not part of the runner and resolves `ROOT` to `Step 1 computation`, making its declared `analysis/` and `raw/` paths inconsistent with the current layout. The Step 2 version fixes the root calculation. `combiner.py` only concatenates Python source files.

## Step 2 result-generation scripts

| Script | Verified purpose | Principal inputs | Output directory | Extra imports |
|---|---|---|---|---|
| `01_audit_heat_of_adsorption.py` | HOA availability/coverage audit | final pair effects and raw adsorption CSVs | `Step 2 results/heat_audit` | none beyond pandas/NumPy |
| `02_analyze_heat_adsorption_contrasts.py` | Matched HOA/adsorption contrast analysis | final pair effects and raw HOA columns | `Step 2 results/heat_analysis` | joblib, SciPy statistics |
| `03_analyze_residual_geometry_adjustment.py` | Residual-geometry-adjusted sensitivity | symmetric design, primary/control pairs, scales, raw adsorption | `Step 2 results/residual_adjustment` | joblib |
| `04_audit_balance_and_family_dominance.py` | Balance and family-exclusion audit | design, pairs/controls, group effects | `Step 2 results/balance_family_dominance` | joblib |
| `05_analyze_guest_specificity.py` | Paired guest-specificity summaries | group effects and matched HOA group data | `Step 2 results/guest_specificity` | joblib |
| `06_freeze_step2_claims.py` | Validate and freeze the Step 2 evidence matrix | named Step 2 CSV outputs | `Step 2 results/step2_closure` | none beyond pandas/NumPy |

No Step 2 runner was found; numeric filename order is the only workflow ordering evidence.

## Step 3 figure/table/packaging scripts

| Script | Verified purpose | Principal inputs | Principal outputs |
|---|---|---|---|
| `01_prepare_final_case_selection.py` | Prepare human-review case package | one discovered review sheet; optional HOA/guest results | `case_selection/01_*` |
| `02_freeze_final_case_selection.py` | Freeze six expected cases | recommended review set | final case set/framework tables and manifest |
| `03_audit_selected_case_charges.py` | Extract/audit selected CIF charge rows | final case set and uniquely discovered raw archive | `case_chemistry/03_*`; pymatgen |
| `04_build_figure_source_package.py` | Copy/filter exact figure source tables | final case set and uniquely resolved upstream basenames | `figure_source_data/Figure_01`-`Figure_06`, registries, manifest |
| `05_freeze_figure_blueprint.py` | Freeze panel/caption/source blueprint | figure-source registry/index/missing list | `figure_blueprint/05_*` |
| `06_render_quantitative_figures.py` | Render Figures 1-4 and 6 | packaged figure-source CSVs | PDF/PNG/SVG plus manifest/report; matplotlib |
| `06_render_quantitative_figures_REPLACEMENT_v8.py` | Alternate quantitative renderer | same source class | same output names |
| `06_render_quantitative_figures_REPLACEMENT_v9.py` | Alternate quantitative renderer | same source class | same output names |
| `07_render_structure_case_figure.py` | Render Figure 5 | final cases, charge summaries, inspected CIFs or frozen fallback | Figure 5 PDF/PNG/SVG plus panel source/report/manifest |
| `07_render_structure_case_figure_STEP4_v2.py` | Alternate Figure 5 renderer with Step 4 case chemistry | above plus Phase 2C/2E CSVs | same output names |
| `07_render_structure_case_figure_STEP4_v3.py` | Alternate Figure 5 renderer | same as v2 | same output names |
| `07_render_structure_case_figure_STEP4_v4.py` | Alternate Figure 5 renderer | same as v2 | same output names |
| `09_build_si_source_registry.py` | Resolve sources for proposed SI assets | named upstream tables discovered by schema | SI item/source/blocker registries and manifest |
| `10_build_lean_si_package.py` | Generate SI figures, tables, and source copies | frozen Step 2/3 tables and handoff candidates | three SI figures, nine TeX tables, source CSVs, report/manifest |

Renderer ambiguity: the final `06_manifest.json` and `07_manifest.json` record the canonical script names but do not include an executing-script SHA-256. Alternate renderer files have distinct hashes and modification times immediately preceding the generated outputs. Figure 5's manifest lists Step 4 inputs that the canonical renderer does not declare. These facts narrow the candidates but do not prove which file executed. All variants are retained and no canonical choice is asserted.

## Step 4 audit/extension scripts

The numbered scripts write only below `Step 4 results` according to their code and governance documents.

| Scripts | Verified purpose and inputs | Output area |
|---|---|---|
| `01_phase0_frozen_audit.py` | Discover, hash, schema-audit, and count named frozen Step 1-3 sources | `00_governance` |
| `02_phase1_existing_evidence_audit.py` | Read the Phase 0 inventory and chosen frozen sources to audit existing evidence | `01_existing_evidence` |
| `03_phase2a_cif_chemistry_preflight.py` | Audit selected CIF/charge inputs and installed chemistry toolchain | `02_cif_chemistry/phase2a_preflight` |
| `04_phase2b0_coordination_method_recovery.py` | Recover the existing coordination implementation from scripts/data | `phase2b0_method_recovery` |
| `05_phase2b_selected_case_local_chemistry.py` | Compute selected-case structural/local-chemistry descriptions | `phase2b_selected_case_local_chemistry` |
| `06_phase2b1_charge_site_mapping_provenance.py` | Audit existing charge-to-CIF row mapping provenance | `phase2b1_charge_mapping_provenance` |
| `07_phase2b2_exact_charge_site_bridge.py` | Build/audit raw-CIF-row to pymatgen-site mapping | `phase2b2_exact_charge_site_bridge`; SciPy optimizer |
| `08_phase2c_case_chemistry_synthesis.py` | Combine validated selected-case chemistry outputs | `phase2c_case_chemistry_synthesis` |
| `09_phase2d0_linker_localization_feasibility.py` | Search existing files for linker/atom mapping candidates | `phase2d0_linker_localization_feasibility` |
| `10_phase2d1_linker_definition_recovery.py` | Narrow the linker-definition/mapping search | `phase2d1_linker_definition_recovery` |
| `11_phase2e_chemistry_closure.py` | Convert Phase 2 outputs to a closure/decision map | `phase2e_chemistry_closure` |
| `12_phase3a_dependency_exchangeability_audit.py` | Audit dependence/exchangeability using frozen pairs/controls | `03_falsification/phase3a_*` |
| `13_phase3b_falsification_closure.py` | Freeze the Phase 3 null-reference decision | `phase3b_falsification_closure` |
| `14_phase4a_simulation_provenance_feasibility.py` | Search local files/runtime for simulation reproduction inputs; does not simulate | `04_host_guest_maps/phase4a_*` |
| `15_phase4b_external_protocol_reconstruction.py` | Encode externally recovered protocol candidates and selected-state feasibility; does not simulate | `phase4b_external_protocol_reconstruction` |
| `16_phase4c_core_simulation_closure.py` | Record core simulation-branch closure | `phase4c_core_closure` |
| `17_phase6a_core_integration_freeze.py` | Hash and freeze the core integration handoff | `06_integration/phase6a_*` |

## Processed datasets used in production

Verified small processed input packages copied into this draft:

- `Step 3 results/figure_source_data` (33 files, 0.387 MB): exact figure-source CSVs plus registries/manifests.
- `Step 3 results/si_source_data` (24 files, 0.201 MB): source CSVs used by the SI generator.
- `Step 3 results/case_selection` (9 files, 0.026 MB): case selection tables/manifests.
- `Step 3 results/case_chemistry` (7 files, 0.203 MB): selected-case charge tables/manifests, no CIFs.
- Step 4 Phase 2C and 2E result folders (10 files, 0.021 MB): selected-case synthesis and Figure 5 decision inputs.

Large processed datasets in `analysis` include the framework master, pair rules, effect tables, controls, robustness outputs, and 16,211 Parquet files. They are fully enumerated in `01_inventory_report.csv` but not copied to this draft. Most Parquet files are restart/intermediate shards under `analysis/full_pair_rules_work`; final named Parquets are documented by the script table and existing manifests.

## Figures and tables

- Main figures: Figures 1-6, each in PDF/PNG/SVG, plus manifests/source/report files in the original output folder.
- SI figures: S01-S03 in PDF/PNG.
- SI tables: nine generated `.tex` tables.
- Figure generators: Step 3 scripts `06*`, `07*`, and `10_build_lean_si_package.py`.
- Table generator: `10_build_lean_si_package.py`.

## Manifests, hashes, and provenance

Existing provenance assets include 11 JSON manifests under `analysis`, six Step 2 manifests, multiple Step 3 manifests, the 107-row frozen `output_hash_manifest.csv`, an availability matrix, Step 4 Phase 0's 56-instance frozen-source hash audit, figure source/output manifests, and Step 4 per-phase summaries/toolchain records.

The raw folder contained no hashes. This draft therefore computes SHA-256 for its 19 files without copying them; see `raw_data_sha256.csv`.

## Configuration and environment

No standalone configuration files or environment definitions were found. Numeric settings, worker counts, seeds, thresholds, filenames, and path rules are embedded in the scripts. Recorded package versions and unpinned imports are summarized in `../environment/README.md`.

## Release information still required

- authoritative project title/author list and paper citation;
- code license;
- ARC-MOF citation/version/access route and license/data-use terms;
- permission status for processed derivative tables, selected CIFs, and generated figures;
- a tested environment definition with all dependency versions;
- proof of the active Step 3 renderer variants, preferably by script hashes in manifests;
- a portable path/layout decision for scripts copied under `scripts/`;
- confirmation whether the out-of-scope Step 5 folders belong in the paper workflow.
