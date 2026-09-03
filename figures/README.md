# Figures

This directory currently preserves the audited historical Step 3 figure assets.

## Release status

The files already present under `figures/main/` and `figures/supplementary/` are retained as provenance while the Paper 7B publication release is being finalized.

They must **not** be assumed to be the final manuscript-facing set until the finalized figure packets are reconciled on the release branch.

In particular:

- the finalized redesigned quantitative figures will supersede the historical renderings where applicable;
- the final Figure 5 is the separately finalized structural composite and will supersede the historical Figure 5;
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
