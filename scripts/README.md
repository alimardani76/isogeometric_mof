# Scripts

The stage subfolders contain audited copies of the historical analysis and production scripts.

- `step1/`: scripts `01`-`25` and `RUN_STEP1.bat` from Step 1 computation.
- `step2/`: scripts `01`-`06` from Step 2 chemistry strengthening.
- `step3/`: historical production/source-generation scripts. Superseded quantitative `06` renderer variants are now archived under `../archive/legacy_renderers/quantitative/`; historical structural `07` variants remain provenance only.
- `step4/`: scripts `01`-`17` from the Step 4 extension.

## Historical provenance versus publication reproduction

These scripts retain original path calculations such as `Path(__file__).resolve().parents[1]` or `.parent`. Moving them under this repository changes what those expressions resolve to.

Accordingly, the historical copies are preserved as provenance assets rather
than rewritten in place.

A separate Tier-1 publication-figure reproduction layer is now present at
`../reproduce/figures/`. It uses frozen compact source tables and generates the
final quantitative/RASPA main and SI figures without re-fitting the core study
or rebuilding the matched population. Its clean-clone/fresh-environment test
remains a release gate.

## Step 3 renderer canonicalization

The August historical archive contained competing quantitative and structural
renderer variants because the old manifests alone did not prove which variant
produced every final manuscript asset.

That ambiguity is now resolved for the publication layer without rewriting the
historical science:

- final quantitative/RASPA publication rendering is canonicalized under
  `../reproduce/figures/`;
- superseded quantitative `06` variants are retained under
  `../archive/legacy_renderers/quantitative/` for provenance only;
- final structural Figure 5 is canonicalized under `../structural_panel/`;
- historical structural `07` renderer variants remain provenance and are not
  the canonical source of the final structural composite.

Canonical selection is based on finalized source data, renderer behavior,
approved final output, and manifests/hashes — not on version-number suffixes.

## Excluded script-like files

- `Step 1 computation/combiner.py`: generic source concatenation utility, not part of `RUN_STEP1.bat` or a verified result/figure/table workflow.
- `Step 1 computation/26_audit_heat_of_adsorption.py`: not called by `RUN_STEP1.bat`, duplicates the Step 2 audit, and resolves its root inconsistently relative to the expected project layout.

See `../provenance/02_reproducibility_assets.md` for the historical per-script audit and `../provenance/claim_boundaries.md` for the scientific freeze applied during release engineering.

## Final Figure 5 structural source

The authoritative structural-panel Git handoff resolves the publication-facing source layout.

The historical `scripts/step3/07_render_structure_case_figure*.py` files are provenance assets and are not the canonical source for the final structural composite.

The curated release module is fully committed and manifest-verified under:

- `structural_panel/src/ovito/panel_A/` through `panel_F/` for selected final/preflight OVITO source;
- `structural_panel/scripts/final_production/` for final-production path/environment, collection, validation, and review-packaging utilities;
- `structural_panel/data/` for frozen CIF inputs and scientific/provenance evidence;
- `structural_panel/figures/` for the 24 final source PNGs and final composite artwork.

The Git-adapted scripts must preserve scientific selections/cameras/cutoffs while using portable repository-relative paths. The exact OVITO version is not invented when it is not established by the handoff.


The release integrity workflow verifies the structural module against
`structural_panel/data/manifests/REPO_PAYLOAD_SHA256.csv` on every PR update.

## Release audit helpers

- `release/check_repository_integrity.py`: CI-facing integrity check.
- `release/audit_public_release.py`: broader pre-publication audit helper for
  final assets, paths, syntax/data readability, RASPA invariants, and open
  release gates.
