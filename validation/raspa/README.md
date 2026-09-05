# Selected-case RASPA validation

This directory is the publication-facing home for the selected-case RASPA validation associated with Paper 7B.

## Verified production scope

The audited production/closure record contains:

- 192 production runs;
- 192/192 audited runs with PASS status;
- 8 selected framework pairs;
- 16 unique frameworks;
- 3 replicates per framework/mode;
- 4 simulation modes:
  - `henry_full`
  - `henry_chargeoff`
  - `gcmc_0p1bar`
  - `gcmc_1bar`
- temperature: 298 K;
- Henry production cycles: 50,000;
- GCMC initialization cycles: 10,000;
- GCMC production cycles: 50,000;
- one thread per audited run;
- Ewald electrostatics;
- framework–guest van der Waals cutoff: 12.0 Å;
- Ewald precision: 1e-6;
- Coulomb real-space cutoff selected automatically by RASPA for the simulation cell;
- reported production version: RASPA 3.0.29.

The full raw closure contains 2,115 files totaling 4,348,937,351 bytes
(approximately 4.05 GiB). It is intentionally **not** stored in normal Git history.

## Publication boundary

This is a selected-case validation layer, not a population-scale rerun of the complete matched analysis.

The release must not overstate the validation:

- selected-case RASPA does not validate every population trend;
- the A4 pressure exception was not reproduced under the common 298 K CO2 protocol;
- charge-off comparisons are electrostatic-sensitivity tests and do not independently prove a microscopic mechanism;
- the selected structures do not establish adsorption sites;
- no density-map claim is made without preserved density-map raw assets.

## Compact public layer in this repository

The public repository contains the compact publication/provenance layer needed for
main Figure 6 and SI Figure S06:

- `data/canonical/` — canonical publication-oriented summary tables;
- `data/reproducibility/` — run-level audit and compact frozen summaries;
- `code/` — validation/rendering helpers;
- `reports/` — publication validation reports.

The raw multi-gigabyte run tree remains external.

## External raw-closure checksum

The authoritative external raw closure archive is recorded with SHA-256:

`ccf7abe9bdf3131bf7c13d6707f56f3d97ad5030a6b48e71a0c4bd17f1e28f00`

If the archive is later deposited in Zenodo or another immutable repository,
add its persistent identifier here and in the root README.

## Public-path sanitization

The authoritative handoff includes author-local Windows filesystem paths in some
run-location fields. Public copies replace only those location/path strings with
portable basenames or job identifiers. Scientific values, protocol settings,
job IDs, seeds, status fields, and recorded hashes are unchanged.

The untouched authoritative handoff remains external and must not be committed
as a ZIP archive.

## Provenance note

The audited production results report RASPA 3.0.29. A separate RASPA 3.0.30
Windows compilation experiment is **not** the source of the reported production
results and must remain clearly separated from the production provenance.
