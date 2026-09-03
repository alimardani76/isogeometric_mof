# Selected-case RASPA validation

This directory is the publication-facing home for the selected-case RASPA validation associated with Paper 7B.

## Verified production scope

The audited closure record available during release preparation contains:

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
- production cycles: 50,000;
- GCMC initialization cycles: 10,000;
- one thread per audited run;
- Ewald electrostatics;
- van der Waals cutoff: 12.0 Å;
- Ewald precision: 1e-6;
- reported production version: RASPA 3.0.29.

The archived closure contains 2,115 files totaling approximately 4.05 GiB. The full raw closure is intentionally **not** stored in normal Git history.

## Publication boundary

This is a selected-case validation layer, not a population-scale rerun of the complete matched analysis.

The release must not overstate the validation:

- selected-case RASPA does not validate every population trend;
- the A4 pressure exception was not reproduced under the common 298 K CO2 protocol;
- charge-off comparisons are sensitivity tests and do not independently prove an electrostatic mechanism;
- the selected structures do not establish adsorption sites;
- no density-map claim is made without preserved density-map raw assets.

## Files to be finalized

The final RASPA packet will populate this directory with the compact publication layer, including the canonical final summaries, the final Figure 6 source package, the run-level audit, and an external-archive manifest/checksum.

The large raw closure should be deposited in an immutable external archive and linked here by DOI or equivalent persistent identifier plus SHA-256 checksum.

## Provenance note

The audited production results report RASPA 3.0.29. A separate RASPA 3.0.30 Windows compilation experiment is not the source of the reported production results and must remain clearly separated from the production provenance.
