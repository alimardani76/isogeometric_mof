# Paper 7B — Publication Figure Reproduction Package

This is the canonical portable publication-figure renderer built from the frozen source tables supplied for Paper 7B. It does not re-fit the core study.

## What it generates

### Main text
- `Figure_01.pdf` + `Figure_01_200dpi.png`
- `Figure_02.pdf` + `Figure_02_200dpi.png`
- `Figure_03.pdf` + `Figure_03_200dpi.png`
- `Figure_04.pdf` + `Figure_04_200dpi.png`
- `Figure_06.pdf` + `Figure_06_200dpi.png`

**Figure 05 is intentionally NOT generated.** Keep the structural Figure 5 that is already finalized in the structural workstream.

`Figure_06` is now the **RASPA selected-case validation figure**, not the old process-summary Figure 6.

### Supporting Information
- `Figure_S01_Additional_Controls.pdf`
- `Figure_S02_HOA_Associations.pdf`
- `Figure_S03_Guest_Pressure_Specificity.pdf`
- `Figure_S04_Robustness_Geometry_Sensitivity.pdf`
- `Figure_S05_Structural_Geometry_Control.pdf`
- `Figure_S06_RASPA_Eight_Pair_Detail.pdf`

A 200-dpi PNG is saved beside every PDF for quick inspection/editing.

## Recommended way to run on Windows 11

### Option A — clean Conda environment (safest)

1. Use a clean clone of this repository and enter the package folder, for example:
   `C:\\path\\to\\isogeometric_mof\\reproduce\\figures`
2. Open **Anaconda Prompt**.
3. Go to the package folder:

```bat
cd /d "C:\\path\\to\\isogeometric_mof\\reproduce\\figures"
```

4. Create the environment once:

```bat
conda env create -f environment.yml
```

5. Activate it:

```bat
conda activate paper7b_figures
```

6. Render everything:

```bat
python render_all.py --set all
```

That is the command I recommend for the first full run.

### Option B — use your existing Python/Anaconda environment

From the package folder:

```bat
pip install -r requirements.txt
python render_all.py --set all
```

For reproducibility, the clean-Conda route above is preferred.

## Commands you will use later

Render all main figures only:

```bat
python render_all.py --set main
```

Render the complete SI figure set only:

```bat
python render_all.py --set si
```

Render one figure while you are changing its code:

```bat
python render_one.py Figure_02
python render_one.py Figure_04
python render_one.py Figure_06
python render_one.py Figure_S04
```

Available single-figure names are:
`Figure_01`, `Figure_02`, `Figure_03`, `Figure_04`, `Figure_06`, `Figure_S01` … `Figure_S06`.

## Running from Spyder

Set Spyder's working directory to the **root of this package**, then run in the IPython console:

```python
%run render_all.py --set all
```

For one figure:

```python
%run render_one.py Figure_02
```

Do **not** run the individual modules inside `src/` directly; run `render_all.py` or `render_one.py` from the package root.

## Where the files appear

Main figures:

```text
outputs/main/Figure_01/
outputs/main/Figure_02/
outputs/main/Figure_03/
outputs/main/Figure_04/
outputs/main/Figure_06/
```

SI figures:

```text
outputs/si/Figure_S01/
...
outputs/si/Figure_S06/
```

Quick overview sheets:

```text
outputs/previews/MAIN_contact_sheet.png
outputs/previews/SI_contact_sheet.png
```

Each figure folder also contains:
- deterministic plot-ready `source_panel_*.csv` files;
- `manifest.json` with source/output SHA-256 hashes;
- the resolved font used on that machine.

Global checksums are written under `manifests/`.

## Font behavior

The scripts request **Arial first**. On a normal Windows installation, Matplotlib should find Arial. If it does not, the code falls back to Liberation Sans/Helvetica/DejaVu Sans and records the actual choice in each manifest.

No font files are included in this package.

The approved manuscript binaries under `../../figures/` remain authoritative.
A clean-clone render on another platform is expected to preserve the plotted
science and frozen source tables, but byte-identical PDF/PNG files are not
promised when fonts or rendering stacks differ.

## What to edit when changing appearance

Global colors/fonts/style:

```text
src/style.py
config.json
```

Main figure layouts/data displays:

```text
src/main_figures.py
```

SI figure layouts/data displays:

```text
src/si_figures.py
```

PNG DPI can be changed in `config.json`. It is currently fixed at **200 dpi** as requested. PDF output remains vector and should be the file used for the manuscript/Overleaf.

## Data-integrity rule

All plots are generated from the frozen CSV tables in `data/`. The renderer does not re-fit the core study, create new matched pairs, alter case selection, or perform outcome-driven filtering.

The main RASPA Figure 6 and SI Figure S06 use the supplied RASPA 3.0.29 closure summary tables. The density-map analysis is deliberately not reproduced.

## Release-test status

The environment definition is present (`environment.yml` and
`requirements.txt`), but the clean-clone/fresh-environment release gate remains
open until this workflow is actually run successfully in a separate fresh
clone/environment and the result is recorded.

The canonical renderer must not be confused with historical Step 3 renderer
variants retained under `../../archive/legacy_renderers/quantitative/`.
