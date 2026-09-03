
# isogeometric_mof: Reproducibility and Transparency Record


> **Publication-release preparation:** this branch is being prepared as the
> public-release version of the Paper 7B repository. The historical analysis
> archive is preserved. The finalized structural panel is now integrated and
> hash-verified; redesigned quantitative/SI figures and the final RASPA Figure 6
> package remain to be reconciled before release. Scientific values and claim
> boundaries are frozen during this release-engineering work.


## Purpose

This document provides a detailed record of the computational workflow
behind the isogeometric MOF adsorption analysis.

The goal is to make the analysis traceable from:

raw source data → preprocessing → chemistry extraction → pair
construction → statistical analysis → figure generation → supplementary
tables.

This repository contains the reproducibility assets generated from the
audited Project 7B2 workflow. The historical Steps 1--4 analysis is preserved,
and the publication release also includes a dedicated selected-case validation
layer under `validation/raspa/`. Final manuscript-facing assets are canonicalized
on the release branch before public release.

------------------------------------------------------------------------

# 1. Project scope

The analysis investigates adsorption contrasts between chemically
modified MOF frameworks while attempting to control structural and
geometric differences through systematic framework comparison and
matched analyses.

The computational workflow was developed as a staged pipeline:

1.  Dataset construction and chemistry extraction.
2.  Chemistry-controlled adsorption analysis.
3.  Production analysis, figures, and supplementary tables.
4.  Additional chemistry interpretation and provenance audits.

------------------------------------------------------------------------

# 2. Input data and provenance

## ARC-MOF-derived input data

The original project uses ARC-MOF-derived structural and
adsorption-related data.

The raw source data are not included in this repository because their
redistribution conditions must be handled according to the original
database/source terms.

Instead, this repository contains:

-   file inventories;
-   SHA-256 hashes;
-   provenance manifests;
-   derived processed datasets required for interpretation.

Relevant files:

    provenance/raw_data_sha256.csv
    provenance/phase0_frozen_input_inventory.csv
    provenance/phase0_manifest.json

The raw-data audit recorded the original source files, sizes,
timestamps, and hashes without redistributing the source files.

------------------------------------------------------------------------

# 3. Repository structure

    data/
        case_selection/
        case_chemistry/
        figure_source_data/
        si_source_data/
        step4_case_chemistry/

    scripts/
        step1/
        step2/
        step3/
        step4/

    figures/
        main/
        supplementary/

    tables/
        supplementary/

    provenance/
    environment/
    structural_panel/
    validation/
        raspa/
    archive/

------------------------------------------------------------------------

# 4. Step 1: Dataset construction and framework comparison

Location:

    scripts/step1/

Purpose:

Build the analysis cohort, extract structural chemistry information,
construct candidate comparisons, and generate the framework-pair
datasets used downstream.

Main workflow components:

## 01_build_cohort.py

Purpose: - assemble the framework cohort; - integrate structural
descriptors; - connect topology, geometry, adsorption, and
process-related information.

Expected outputs include cohort-level datasets and analysis tables.

## 02_extract_cif_chemistry.py

Purpose: - extract chemical information from CIF structures; - identify
framework chemistry features; - generate chemistry-level records.

## 03_build_candidate_pairs.py

Purpose: - generate candidate framework comparisons.

## 04_check_metal_coordination.py

Purpose: - audit metal coordination consistency.

## 05_group_related_pairs.py

Purpose: - organize related framework comparisons.

## Matching and robustness analysis

Scripts include:

-   reciprocal matching;
-   matching robustness tests;
-   topology robustness;
-   geometry limit analysis;
-   boundary-case audits.

Final Step 1 outputs are stored mainly in:

    data/case_selection/
    data/figure_source_data/

------------------------------------------------------------------------

# 5. Step 2: Chemistry strengthening and adsorption analysis

Location:

    scripts/step2/

Purpose:

Analyze adsorption-related contrasts and test whether observed
differences persist under additional controls.

Main analyses include:

-   heat of adsorption analysis;
-   residual geometry adjustment;
-   balance/family dominance checks;
-   guest-specific analysis;
-   claim freezing.

Outputs:

    data/figure_source_data/
    data/si_source_data/

Examples:

    hoa_condition__heat_adsorption_condition_results.csv
    hoa_pressure__heat_adsorption_pressure_results.csv
    guest__05_results.csv
    controls_primary__step3_same_chemistry_control_results.csv

------------------------------------------------------------------------

# 6. Step 3: Production analysis, figures, and SI generation

Location:

    scripts/step3/

Purpose:

Generate the final manuscript-facing outputs.

## Case selection and freezing

Scripts:

    01_prepare_final_case_selection.py
    02_freeze_final_case_selection.py

Outputs:

    data/case_selection/

## Charge and chemistry audits

Scripts:

    03_audit_selected_case_charges.py

Outputs:

    data/case_chemistry/

## Figure source generation

Scripts:

    04_build_figure_source_package.py
    05_freeze_figure_blueprint.py
    06_render_quantitative_figures.py
    07_render_structure_case_figure.py

Generated figures:

    figures/main/

    Figure_01.pdf
    Figure_02.pdf
    Figure_03.pdf
    Figure_04.pdf
    Figure_05.pdf
    Figure_06.pdf

The canonical final Figure 5 is synchronized at `figures/main/Figure_05.pdf`.
Its complete curated source/reproduction module is under `structural_panel/`;
the historical Step 3 structural renderers remain provenance only.

Supplementary figures:

    figures/supplementary/

## Supplementary information

Scripts:

    09_build_si_source_registry.py
    10_build_lean_si_package.py

Tables:

    tables/supplementary/

Generated SI tables:

-   Table S01 Condition Coverage
-   Table S02 Control Summary
-   Table S03 HOA Summary
-   Table S04 Guest Specificity
-   Table S05 Residual Adjustment
-   Table S06 Balance
-   Table S07 Family Exclusion
-   Table S08 Process Translation
-   Table S09 Final Cases Charges

------------------------------------------------------------------------

# 7. Step 4: Chemistry interpretation and transparency layer

Location:

    scripts/step4/

Purpose:

Provide additional audits and interpretation support.

Major components:

-   frozen input audit;
-   evidence audit;
-   CIF chemistry preflight;
-   coordination recovery;
-   local chemistry analysis;
-   charge-site mapping;
-   case chemistry synthesis;
-   dependency and exchangeability audits;
-   falsification closure;
-   simulation provenance feasibility;
-   integration freeze.

Outputs:

    data/step4_case_chemistry/
    provenance/

------------------------------------------------------------------------

# 8. Figures and tables

## Main figures

Location:

    figures/main/

Contains the historical paper-facing figure set. For the release branch,
Figure 5 is canonicalized as PDF at `figures/main/Figure_05.pdf`; its editable
PowerPoint, 24 high-resolution source PNGs, CIF inputs, manifests, and OVITO
sources are versioned under `structural_panel/`.

## Supplementary figures

Location:

    figures/supplementary/

## Supplementary tables

Location:

    tables/supplementary/

Source datasets:

    data/figure_source_data/
    data/si_source_data/

------------------------------------------------------------------------

# 9. Software and computational environment

Observed workflow components include:

-   Python
-   pandas
-   NumPy
-   matplotlib
-   pymatgen
-   PyArrow
-   SciPy
-   scikit-learn
-   joblib

The audited project did not contain a complete environment lock file.

Future release improvement:

-   add requirements.txt or conda environment;
-   test reproduction from a clean environment.

------------------------------------------------------------------------

# 10. Reproduction workflow

Recommended order:

1.  Obtain permitted access to required external source datasets.
2.  Restore the expected project directory structure.
3.  Install required Python dependencies.
4.  Execute Step 1 scripts.
5.  Execute Step 2 analysis.
6.  Generate Step 3 production outputs.
7.  Run Step 4 transparency and interpretation audits.

The included scripts preserve the original analysis workflow rather than
being rewritten into a new package.

------------------------------------------------------------------------

# 11. Reproducibility limitations

Current limitations:

-   Raw ARC-MOF-derived source files are not included.
-   Scripts retain original project-path assumptions.
-   No complete environment lock file was available.
-   Some renderer variants exist and require careful selection.
-   The workflow has not been rerun from a clean external clone.

These limitations are documented intentionally to preserve transparency.

------------------------------------------------------------------------

# 12. Repository status

This repository represents the reproducibility archive for the
computational analysis.

Included:

-   processed datasets;
-   analysis scripts;
-   figure sources;
-   generated figures;
-   supplementary tables;
-   provenance records.

Excluded:

-   raw ARC-MOF source files;
-   exploratory validation branches;
-   temporary intermediate files.

------------------------------------------------------------------------

# 13. Publication-release preparation

The public-release workflow is intentionally separated from the historical
analysis archive.

Current release-facing records:

- `structural_panel/` — completed, manifest-verified final Figure 5 module;
- `validation/raspa/README.md` — selected-case RASPA production scope,
  limitations, and archival strategy;
- `provenance/claim_boundaries.md` — interpretation boundaries that must not
  be broadened during repository cleanup;
- `provenance/source_data_policy.md` — conservative ARC-MOF/CIF and large-file
  redistribution policy;
- `archive/README.md` — policy for superseded/noncanonical renderers and other
  historical assets.

The structural-panel workstream is complete on this release branch. Before
the repository as a whole is public, it still requires:

1. synchronization with the finalized redesigned quantitative/SI figures;
2. synchronization with the finalized RASPA Figure 6/source package;
3. one canonical renderer/source package for each remaining paper-facing figure;
4. a tested environment definition;
5. a clean-clone publication-reproduction test;
6. final code/data licensing, source-rights review, and citation metadata;
7. a final release SHA-256 manifest generated only after all release files are
   frozen.

Until those checks pass, the repository should not claim complete clean-clone
reproducibility.
