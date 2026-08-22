# Scripts

The stage subfolders contain unmodified copies of scripts whose purpose, inputs, outputs, and imports were inspected during the audit.

- `step1/`: scripts `01`-`25` and `RUN_STEP1.bat` from `Step 1 computation`.
- `step2/`: scripts `01`-`06` from `Step 2 chemistry strengthening`.
- `step3/`: production scripts, including all observed alternate `06` and `07` renderer versions because the executing variant is unresolved.
- `step4/`: scripts `01`-`17` from `Step 4 extension`.

The copies retain original path calculations such as `Path(__file__).resolve().parents[1]` or `.parent`. Moving them under this folder changes what those expressions resolve to. They are preserved as audited source assets, not represented as directly runnable from their draft locations.

Excluded script-like files:

- `Step 1 computation/combiner.py`: a generic source concatenation utility, not part of `RUN_STEP1.bat` or a verified result/figure/table workflow.
- `Step 1 computation/26_audit_heat_of_adsorption.py`: not called by `RUN_STEP1.bat`, duplicates the Step 2 audit, and resolves `ROOT` to its own folder rather than the project root expected by its declared paths.

See `../provenance/02_reproducibility_assets.md` for per-script audit details.
