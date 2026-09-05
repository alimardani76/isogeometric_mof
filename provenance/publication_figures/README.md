# Source/provenance contents

This folder lets the main manuscript chat verify exactly what each final panel shows without reopening the large historical archives.

- `manifests/` — final per-figure manifests. These record input/source hashes, output hashes, and resolved font. All final quantitative/SI manifests report Arial.
- `panel_sources/` — exact panel-level CSVs written by the final renderer. Use these to validate caption statements or extract exact values if the manuscript needs them.
- `raspa/` — compact RASPA selected-case statistics and closure notes used for Figure 6 / Figure S06 integration.

If a manuscript sentence needs a numerical value that is not already verified, read the corresponding panel-source CSV rather than estimating it from the plotted marker position.
