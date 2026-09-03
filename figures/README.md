# Figures

This directory currently preserves the audited historical Step 3 figure assets.

## Release status

The files already present under `figures/main/` and `figures/supplementary/` are retained as provenance while the Paper 7B publication release is being finalized.

They must **not** be assumed to be the final manuscript-facing set until the finalized figure packets are reconciled on the release branch.

In particular:

- the finalized redesigned quantitative figures will supersede the historical renderings where applicable;
- the finalized structural-panel handoff has now been verified and establishes the canonical Figure 5 content; the historical Figure 5 is superseded;
- the final Figure 6 is the selected-case RASPA validation figure and will supersede the historical Figure 6.

Associated historical manifests and source hashes remain under `../provenance/`.

## Canonical figure rule

For public release, every paper-facing figure must have:

1. one canonical final output set;
2. one clearly identified canonical renderer;
3. its exact compact source data or an explicit external-source provenance record;
4. a manifest/hash record linking source, renderer, and output.

Alternate historical renderers are provenance assets, not competing canonical implementations.

## Rights and structural inputs

Generated files are not, by themselves, evidence of an open-content license. Selected CIF redistribution remains conservative until source-data redistribution rights are explicitly established; see `../provenance/source_data_policy.md`.


## Figure 5 structural handoff status

The finalized structural-panel handoff has been audited on the release branch.

Verified:
- 6 frozen panels / 12 framework endpoints;
- 24 high-resolution source PNGs;
- all source PNGs 3200 × 2400 px at approximately 600 dpi metadata;
- one-slide editable PowerPoint source embedding the same 24 PNG byte streams;
- package hash verification PASS for all 86 pre-manifest files;
- final structural case, geometry-control, local-chemistry and CIF-hash records added to the repository.

The old Step 3 Figure 5 Python renderers are historical provenance, not the canonical source of the final structural composite.

See `main/Figure_05/README.md` and `../provenance/structural_panel_release_manifest.json`.
