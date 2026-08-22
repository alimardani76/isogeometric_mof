isogeometric_mof: Reproducibility and Transparency Record
Purpose
This document provides a detailed record of the computational workflow
behind the isogeometric MOF adsorption analysis.
The goal is to make the analysis traceable from:
raw source data → preprocessing → chemistry extraction → pair
construction → statistical analysis → figure generation → supplementary
tables.
This repository contains the reproducibility assets generated from the
audited Project 7B2 workflow. It focuses on Steps 1--4 of the analysis
pipeline. Exploratory future validation work is maintained separately
and is not part of this repository.
---
1. Project scope
The analysis investigates adsorption contrasts between chemically
modified MOF frameworks while attempting to control structural and
geometric differences through systematic framework comparison and
matched analyses.
The computational workflow was developed as a staged pipeline:
Dataset construction and chemistry extraction.
Chemistry-controlled adsorption analysis.
Production analysis, figures, and supplementary tables.
Additional chemistry interpretation and provenance audits.
---
2. Input data and provenance
ARC-MOF-derived input data
The original project uses ARC-MOF-derived structural and
adsorption-related data.
The raw source data are not included in this repository because their
redistribution conditions must be handled according to the original
database/source terms.
Instead, this repository contains:
file inventories;
SHA-256 hashes;
provenance manifests;
derived processed datasets required for interpretation.
Relevant files:
    provenance/raw_data_sha256.csv
provenance/phase0_frozen_input_inventory.csv
provenance/phase0_manifest.json

The raw-data audit recorded the original source files, sizes,
timestamps, and hashes without redistributing the source files.
---
3. Repository structure
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



---
4. Step 1: Dataset construction and framework comparison
Location:
    scripts/step1/

Purpose:
Build the analysis cohort, extract structural chemistry information,
construct candidate comparisons, and generate the framework-pair
datasets used downstream.
Main workflow components:
01_build_cohort.py
Purpose: - assemble the framework cohort; - integrate structural
descriptors; - connect topology, geometry, adsorption, and
process-related information.
Expected outputs include cohort-level datasets and analysis tables.
02_extract_cif_chemistry.py
Purpose: - extract chemical information from CIF structures; - identify
framework chemistry features; - generate chemistry-level records.
03_build_candidate_pairs.py
Purpose: - generate candidate framework comparisons.
04_check_metal_coordination.py
Purpose: - audit metal coordination consistency.
05_group_related_pairs.py
Purpose: - organize related framework comparisons.
Matching and robustness analysis
Scripts include:
reciprocal matching;
matching robustness tests;
topology robustness;
geometry limit analysis;
boundary-case audits.
Final Step 1 outputs are stored mainly in:
    data/case_selection/
data/figure_source_data/

---
5. Step 2: Chemistry strengthening and adsorption analysis
Location:
    scripts/step2/

Purpose:
Analyze adsorption-related contrasts and test whether observed
differences persist under additional controls.
Main analyses include:
heat of adsorption analysis;
residual geometry adjustment;
balance/family dominance checks;
guest-specific analysis;
claim freezing.
Outputs:
    data/figure_source_data/
data/si_source_data/

Examples:
    hoa_condition__heat_adsorption_condition_results.csv
hoa_pressure__heat_adsorption_pressure_results.csv
guest__05_results.csv
controls_primary__step3_same_chemistry_control_results.csv

---
6. Step 3: Production analysis, figures, and SI generation
Location:
    scripts/step3/

Purpose:
Generate the final manuscript-facing outputs.
Case selection and freezing
Scripts:
    01_prepare_final_case_selection.py
02_freeze_final_case_selection.py

Outputs:
    data/case_selection/

Charge and chemistry audits
Scripts:
    03_audit_selected_case_charges.py

Outputs:
    data/case_chemistry/

Figure source generation
Scripts:
    04_build_figure_source_package.py
05_freeze_figure_blueprint.py
06_render_quantitative_figures.py
07_render_structure_case_figure.py

Generated figures:
    figures/main/
    Figure\_01.pdf
    Figure\_02.pdf
    Figure\_03.pdf
    Figure\_04.pdf
    Figure\_05.pdf
    Figure\_06.pdf



Supplementary figures:
    figures/supplementary/

Supplementary information
Scripts:
    09_build_si_source_registry.py
10_build_lean_si_package.py

Tables:
    tables/supplementary/

Generated SI tables:
Table S01 Condition Coverage
Table S02 Control Summary
Table S03 HOA Summary
Table S04 Guest Specificity
Table S05 Residual Adjustment
Table S06 Balance
Table S07 Family Exclusion
Table S08 Process Translation
Table S09 Final Cases Charges
---
7. Step 4: Chemistry interpretation and transparency layer
Location:
    scripts/step4/

Purpose:
Provide additional audits and interpretation support.
Major components:
frozen input audit;
evidence audit;
CIF chemistry preflight;
coordination recovery;
local chemistry analysis;
charge-site mapping;
case chemistry synthesis;
dependency and exchangeability audits;
falsification closure;
simulation provenance feasibility;
integration freeze.
Outputs:
    data/step4_case_chemistry/
provenance/

---
8. Figures and tables
Main figures
Location:
    figures/main/

Contains:
PDF versions;
PNG versions;
SVG versions.
Supplementary figures
Location:
    figures/supplementary/

Supplementary tables
Location:
    tables/supplementary/

Source datasets:
    data/figure_source_data/
data/si_source_data/

---
9. Software and computational environment
Observed workflow components include:
Python
pandas
NumPy
matplotlib
pymatgen
PyArrow
SciPy
scikit-learn
joblib
The audited project did not contain a complete environment lock file.
Future release improvement:
add requirements.txt or conda environment;
test reproduction from a clean environment.
---
10. Reproduction workflow
Recommended order:
Obtain permitted access to required external source datasets.
Restore the expected project directory structure.
Install required Python dependencies.
Execute Step 1 scripts.
Execute Step 2 analysis.
Generate Step 3 production outputs.
Run Step 4 transparency and interpretation audits.
The included scripts preserve the original analysis workflow rather than
being rewritten into a new package.
---
11. Reproducibility limitations
Current limitations:
Raw ARC-MOF-derived source files are not included.
Scripts retain original project-path assumptions.
No complete environment lock file was available.
Some renderer variants exist and require careful selection.
The workflow has not been rerun from a clean external clone.
These limitations are documented intentionally to preserve transparency.
---
12. Repository status
This repository represents the reproducibility archive for the
computational analysis.
Included:
processed datasets;
analysis scripts;
figure sources;
generated figures;
supplementary tables;
provenance records.
Excluded:
raw ARC-MOF source files;
exploratory validation branches;
temporary intermediate files.
