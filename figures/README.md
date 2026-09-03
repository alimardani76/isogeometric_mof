# Figures

This directory currently preserves the audited historical Step 3 figure assets.

## Release status

The files already present under `figures/main/` and `figures/supplementary/` are retained as provenance while the Paper 7B publication release is being finalized.

They must **not** be assumed to be the final manuscript-facing set until the finalized figure packets are reconciled on the release branch.

In particular:

- the finalized redesigned quantitative figures will supersede the historical renderings where applicable;
- the authoritative structural-panel Git handoff has been verified; its curated public-release module is `structural_panel/`, while the historical Step 3 Figure 5 remains preserved until that module is fully committed;
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

## Figure 5 structural Git-handoff status

The authoritative Project7B StructuralPanel GitHandoff Pack has been audited for repository integration.

Verified in the handoff:
- 100-file curated candidate repository tree;
- 12 frozen panel CIF inputs;
- 24 final high-resolution source PNGs;
- final editable PowerPoint and exported PDF;
- canonical OVITO/preflight source and final-production validation scripts;
- candidate manifest integrity 100/100 PASS;
- package checksum integrity 117/117 PASS.

The handoff defines `structural_panel/` as the publication-facing module. Historical Step 3 Figure 5 files and renderers remain provenance until the curated module is fully committed; they must not be mistaken for the final structural-panel source.

No false-handoff `main/Figure_05/README.md` or `provenance/structural_panel_release_manifest.json` path is used.
