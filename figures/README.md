# Figures

This directory preserves the historical Step 3 paper-facing outputs while the
publication release is canonicalized.

## Release status

- **Figures 1-4 / SI figures:** historical outputs remain until the finalized
  redesigned-figure packet is reconciled.
- **Figure 5:** **complete on the release branch.** The legacy paper-facing path
  `figures/main/Figure_05.pdf` points to the same verified final PDF as
  `structural_panel/figures/final/Structural_Panel_FINAL.pdf`.
- **Figure 6:** historical output remains until the finalized selected-case
  RASPA packet is reconciled.

The stale historical Figure 5 PNG/SVG variants were removed from the release
branch rather than left beside the canonical PDF.

## Canonical structural-panel module

The authoritative structural-panel Git handoff is versioned under
`../structural_panel/`.

Verified release contents:

- 101 tracked structural-panel files;
- 12 frozen panel CIF inputs;
- 35 Python rendering/validation source files;
- 24 final high-resolution source PNGs;
- final editable PowerPoint and exported PDF;
- panel/evidence/provenance manifests;
- final freeze and QA documentation.

The structural payload is frozen by
`structural_panel/data/manifests/REPO_PAYLOAD_SHA256.csv`. The release
integrity workflow recomputes the listed byte sizes and SHA-256 hashes.

## Canonical figure rule

Every final paper-facing figure should have:

1. one canonical final output;
2. one clearly identified canonical renderer/source path;
3. exact compact source data or explicit upstream provenance;
4. a manifest/hash record linking source and output.

Historical renderers are provenance assets, not competing canonical
implementations.

## Source-rights note

The authoritative structural-panel handoff includes the 12 curated CIF inputs
as normal repository assets. Their inclusion is narrow to this frozen module
and does not relicense or mirror the broader upstream dataset. See
`../provenance/source_data_policy.md` for the repository-wide policy and
remaining public-release rights gate.
