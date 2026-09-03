# Project 7B — Final Inset Tightening Pack

## Purpose

The 12 final whole-structure images are already accepted.
This package rerenders **only the 12 frozen inset images** with tighter framing.

Nothing scientific is changed:
- same CIFs;
- same selected atoms/fragments;
- same winner for every panel;
- same face/oblique choice;
- same paired physical scale;
- same colors and bonds;
- 3200 × 2400 px;
- 600 dpi metadata.

Only the orthographic field of view is tightened so each inset uses the canvas efficiently.

## Frozen inset winners

| Panel | Winner | Tightening factor |
|---|---|---:|
| A | `NITRO_plusZn_face` | 0.50 |
| B | `D2_ab_plus` | 0.58 |
| C | `CARBOXY_face` | 0.65 |
| D | `CTX2_ac_mixed` | 0.49 |
| E | `Nfam_face` | 0.51 |
| F | `DIST_D3_face` | 0.55 |

These factors were calculated from the current 3200×2400 renders to bring the major object dimension to approximately **60% of the canvas**.

---

# Where to run

The curated Git tree can run with `P7B_ROOT` unset; the scripts then use `structural_panel/data/cifs/` and write generated screening output below the module root. Set `P7B_ROOT` only when intentionally using the historical starter-pack layout.


Use the same Anaconda/terminal environment that successfully rendered the previous OVITO images.

```bash
conda activate ovito_render
cd structural_panel/scripts/final_production
```

If your project is still at the usual location, no path setting is needed:

```text
<path-to-structural-panel-or-starter-pack>
```

If not, set `P7B_ROOT` to the starter-pack folder.

Windows CMD:
```cmd
set P7B_ROOT=<path-to-structural-panel-or-starter-pack>
```

PowerShell:
```powershell
$env:P7B_ROOT="<path-to-structural-panel-or-starter-pack>"
```

---

# Exact commands

## 1. Check environment and paths

```bash
python 01_check_paths_and_environment.py
```

## 2. Render all six frozen inset pairs

```bash
python 20_run_tight_insets.py
```

This creates the six tight inset pairs inside the project `OVITO_screening` folder.

## 3. Collect the 12 final inset PNGs

```bash
python 30_collect_tight_insets.py
```

Final folder:

```text
<ProjectRoot>\OVITO_final_insets_tight\
```

## 4. Run automatic framing / resolution QA

```bash
python 40_validate_tight_insets.py
```

This creates:
- `tight_inset_QA.csv`
- `tight_inset_QA.md`
- 2 contact sheets

## 5. Zip the validation package

```bash
python 50_zip_for_review.py
```

This creates:

```text
<ProjectRoot>\OVITO_final_insets_tight_REVIEW.zip
```

---

# What to send back to ChatGPT

Send **one file only**:

```text
OVITO_final_insets_tight_REVIEW.zip
```

It should contain:
- 12 corrected inset PNGs;
- `tight_inset_QA.csv`;
- `tight_inset_QA.md`;
- 2 contact-sheet PNGs.

I will then compare all 12 corrected insets against the already accepted whole-structure renders.
If all 12 pass, the OVITO stage is finished and we move to PowerPoint.

---

# Do not change

Do not manually crop or edit the PNGs before sending them.
Do not resize them in Photoshop/PowerPoint.
Do not change atom radii, colors, bonds, camera family, fragment selection, or orientation.

We want to validate the raw OVITO output first.
