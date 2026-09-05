# Figures

This directory preserves the historical Step 3 paper-facing outputs while the
publication release is canonicalized.

## Release status

- **Figures 1-4:** final redesigned PDF + 200-dpi PNG assets are installed.
- **Figure 5:** **complete on the release branch.** The paper-facing
  `figures/main/Figure_05.pdf` is byte-identical to
  `structural_panel/figures/final/Structural_Panel_FINAL.pdf`.
- **Figure 6:** final selected-case RASPA validation PDF + 200-dpi PNG is installed.
- **SI Figures S01-S06:** final PDF + 200-dpi PNG assets are installed under
  `figures/supplementary/`.

The superseded quantitative SVGs for Figures 1-4 and 6 are intentionally absent.
The stale historical Figure 5 PNG/SVG variants also remain removed.

## Canonical quantitative/RASPA source layer

The finalized quantitative/RASPA publication renderer and frozen compact source
tables are under `../reproduce/figures/`.

Final panel-level source/provenance records are under
`../provenance/publication_figures/`, and the compact selected-case RASPA
release/audit layer is under `../validation/raspa/`.

Superseded quantitative Step 3 renderers are retained only for provenance under
`../archive/legacy_renderers/quantitative/`.

Historical `../data/figure_source_data/Figure_06/` material belongs to the
earlier audited figure architecture and is not the canonical source for the
final selected-case RASPA Figure 6.

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
