# Scripts

The stage subfolders contain audited copies of the historical analysis and production scripts.

- `step1/`: scripts `01`-`25` and `RUN_STEP1.bat` from Step 1 computation.
- `step2/`: scripts `01`-`06` from Step 2 chemistry strengthening.
- `step3/`: production scripts, including all historically observed alternate `06` and `07` renderer variants.
- `step4/`: scripts `01`-`17` from the Step 4 extension.

## Historical provenance versus publication reproduction

These scripts retain original path calculations such as `Path(__file__).resolve().parents[1]` or `.parent`. Moving them under this repository changes what those expressions resolve to.

Accordingly, the historical copies are preserved as provenance assets and are **not yet represented as a clean-clone runnable package**.

The public-release work will add a smaller Tier-1 publication-reproduction layer for the final figures/tables without rewriting the historical scientific workflow in place.

## Step 3 renderer ambiguity

The historical repository contains multiple quantitative and structural renderer variants. Their presence is intentional because the August audit could not prove the exact executing variant from the old manifests.

No variant is declared canonical merely because it has the highest version suffix.

Canonical renderer selection will be made only from the finalized figure/structural/RASPA packets by matching:

- source data;
- renderer behavior;
- final output;
- provenance/hashes.

Superseded variants may then be moved or documented under `../archive/` while remaining available for provenance.

## Excluded script-like files

- `Step 1 computation/combiner.py`: generic source concatenation utility, not part of `RUN_STEP1.bat` or a verified result/figure/table workflow.
- `Step 1 computation/26_audit_heat_of_adsorption.py`: not called by `RUN_STEP1.bat`, duplicates the Step 2 audit, and resolves its root inconsistently relative to the expected project layout.

See `../provenance/02_reproducibility_assets.md` for the historical per-script audit and `../provenance/claim_boundaries.md` for the scientific freeze applied during release engineering.


## Final Figure 5 production chain

The finalized structural-panel handoff resolves the publication-facing Figure 5 source.

The historical `scripts/step3/07_render_structure_case_figure*.py` files are **not** the canonical renderer for the final paper Figure 5.

The canonical final production chain is:
1. frozen 12-CIF selected-case set;
2. whole-framework and local-inset rendering using the frozen structural-view specification;
3. 24 final 3200 × 2400 source PNGs;
4. PowerPoint vector assembly and labeling;
5. PDF export.

The exact OVITO version used for the final local rendering environment remains unresolved in the handoff and must not be invented.
