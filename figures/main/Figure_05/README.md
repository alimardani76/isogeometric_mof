# Figure 5 — final structural panel

## Canonical publication asset

The authoritative structural-panel handoff identifies the final manuscript Figure 5 as the six-panel A–F structural composite produced from frozen selected cases.

The final figure supersedes the historical Step 3 card-style Figure 5 and the historical Python `07_render_structure_case_figure*.py` renderers. Those older scripts remain provenance assets and are **not** the canonical renderer for the final structural composite.

The canonical production chain is:

1. six frozen non-overlapping framework pairs selected by predefined quantitative roles;
2. 12 selected CIF structures;
3. paired whole-framework and local-inset structural rendering;
4. 24 final source PNGs (12 whole + 12 local insets), each 3200 × 2400 px at approximately 600 dpi metadata;
5. one-slide PowerPoint assembly with vector labels/callouts;
6. final PDF export.

The exact OVITO version used for the final local rendering environment is not established by the handoff and must not be invented.

## Final panel roles

- **A — Strong linker / process aligned (pcu):** strong local linker-environment contrast.
- **B — Strong metal / process aligned (nbo):** cleanest selected Zn/Cu local-node comparison.
- **C — Cu/Zn boundary / pressure exception (nbo):** method-sensitive, distance-defined local comparison; not a robust coordination mechanism.
- **D — Near-null linker comparator (nbo):** real local linker difference with very small adsorption separation; not “inactive.”
- **E — Process-discordant linker comparator (fsc):** descriptive local chemistry only; the local motif is not assigned as the cause of process discordance.
- **F — Exploratory functional-motif example (sra):** exploratory cyano-bearing local environment; no class-wide causal claim.

## Displayed metrics

Each panel reports:

- median absolute log-adsorption separation;
- mean working-capacity concordance;
- mean selectivity concordance;
- maximum geometry-difference fraction relative to the primary acceptance caliper.

All six selected cases have maximum normalized geometry/caliper fraction below 1.

## Structural claim boundaries

The structural renderings are selected-case chemistry context. They are not:

- adsorption-site maps;
- mechanistic assignments;
- oxidation-state assignments;
- charge-transfer evidence;
- directional substitution mechanisms.

Panel C must remain explicitly method-sensitive. Panel F must remain explicitly exploratory.

## Source and provenance files

Compact publication-facing source data are stored under:

`data/figure_source_data/Figure_05/`

Release provenance is stored under:

- `provenance/structural_panel_release_manifest.json`
- `provenance/structural_panel_cif_sha256.csv`

The 12 selected CIF byte streams remain withheld from public Git pending explicit redistribution-rights resolution. Their identities and hashes are preserved.

## Binary asset status on the release branch

The final binary assets are identified by SHA-256 in the release manifest. The historical Figure 5 binaries must not be merged as the final paper figure.
