# Draft inclusion and exclusion record

Prepared before the first repository commit on 2026-08-22.

## Included

The exact included paths, sizes, SHA-256 hashes, and reasons are in `draft_inclusion_manifest.csv`.

Included classes:

- repository and folder README files plus `.gitignore`;
- the complete 17,024-row inventory and the inspected reproducibility-assets report;
- 63 unmodified workflow files: 62 Python scripts and `RUN_STEP1.bat`;
- 83 copied processed data/metadata files plus `data/README.md`;
- 24 generated figure files plus `figures/README.md`;
- nine generated SI LaTeX tables plus `tables/README.md`;
- existing frozen-output, availability, Phase 0, toolchain, and figure manifests;
- a newly computed 19-row raw-data SHA-256 table containing metadata only.

## Excluded

| Excluded source | Scope | Reason |
|---|---:|---|
| `raw/` file contents | 19 files, about 2,820.9 MB | ARC-MOF-derived source data; no local license/provenance terms established redistribution permission |
| all CIF files | 101 files | structure data are source-derived and redistribution status is unresolved |
| `analysis/*.parquet` and result Parquets | 16,211 files overall, about 462.6 MB | large processed/intermediate datasets; unnecessary for the lightweight draft and many are restart shards |
| `analysis/full_pair_rules_work/` | thousands of Parquet shards plus JSONL restart state | intermediate/restart material, not final release assets |
| raw/source archives and project ZIPs | one GZ and two ZIP files | large or duplicate archive content; source/provenance constraints and no need to duplicate |
| `Step 1 computation/combiner.py` | one Python file | generic code-concatenation utility; not in a verified result, figure, or table workflow |
| `Step 1 computation/26_audit_heat_of_adsorption.py` | one Python file | not invoked by the Step 1 runner, duplicates the corrected Step 2 audit, and has an inconsistent root path in its current location |
| Python bytecode and logs | 27 PYC and two LOG files | generated cache/execution artifacts |
| nonselected analysis/result CSV/JSON/TXT files | enumerated in `01_inventory_report.csv` | not required by the copied figure/SI/case packages; retained at original locations |
| `Step 5 results/`, `Step 5 validation/` | not inventoried | present at top level but outside the user-specified audit scope |

No license, citation, GitHub configuration, remote, or environment lockfile was added because the audited files did not support one.
