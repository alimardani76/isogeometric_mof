# Public-release path sanitization

Historical provenance files in this repository were originally generated on a Windows workstation and recorded absolute local paths.

For the public-release branch, workstation-identifying path prefixes were replaced with the neutral alias:

`HISTORICAL_PROJECT_ROOT`

This sanitization is release engineering only.

## What was changed

Only the historical absolute root prefix was replaced in:

- `figure_06_manifest.json`
- `figure_07_manifest.json`
- `output_hash_manifest.csv`
- `phase0_manifest.json`
- `phase2a_toolchain.json`

## What was not changed

The sanitization did **not** modify:

- scientific values;
- source/output SHA-256 values recorded inside the manifests;
- row counts;
- timestamps;
- package versions;
- analysis decisions;
- figure/source identities;
- case membership.

The alias preserves the relative historical layout while avoiding publication of a contributor's workstation path.

The final publication release will generate a new release-level SHA-256 manifest after all canonical assets are frozen; it will not reuse the historical manifest as a self-integrity record.
