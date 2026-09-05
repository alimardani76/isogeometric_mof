# Project 7B — Final OVITO High-Resolution QA Report

## Overall verdict

The uploaded `OVITO_final_HR.zip` contains the complete requested production set:

- 24 final source PNGs = 6 panels × 2 endpoints × (whole + inset)
- 4 review contact sheets
- 1 freeze manifest

All 24 source PNGs are:

- **3200 × 2400 px**
- **~600 dpi metadata** (`599.9988 × 599.9988 dpi`)
- lossless PNG
- white background

The source images are technically high-resolution and visually sharp at 1:1 inspection.
The contact sheets look softer because they are intentionally downsampled review thumbnails.

The low file sizes of several inset PNGs are **not** evidence of low quality; PNG compresses large white backgrounds extremely efficiently.

---

## Main production issue found

The scientific selections are correct, but the inset objects occupy a relatively small fraction of their 3200×2400 canvases.
This creates a *perception* of low quality when the whole canvas is fitted to screen.

Approximate non-white bounding-box occupancy:

| Panel | i inset | ii inset | QA note |
|---|---:|---:|---|
| A | 30% × 16% | 29% × 22% | correct; crop/zoom in PowerPoint |
| B | 22% × 35% | 21% × 34% | correct; crop/zoom in PowerPoint |
| C | 29% × 39% | 28% × 38% | correct; crop/zoom in PowerPoint |
| D | 15% × 29% | 17% × 25% | **smallest inset; definitely crop tightly** |
| E | 23% × 27% | 20% × 30% | correct; crop/zoom in PowerPoint |
| F | 23% × 31% | 23% × 33% | correct; crop/zoom in PowerPoint |

This is a framing/whitespace issue, not a pixel-resolution problem.

---

# Panel-by-panel visual QA

## Panel A
### Whole pair
**PASS**
- frozen mapped pcu view preserved;
- strong i/ii structural comparability;
- atoms/bonds are sharp at native resolution;
- periodic edge continuation is visible as intended.

### Inset pair
**PASS — production crop needed**
- `NITRO_plusZn_face` selection is present;
- expected Zn-anchor/local-linker contrast is preserved;
- object is visually small because of white margin.

## Panel B
### Whole pair
**PASS**
- frozen nbo whole-view language preserved;
- Zn/Cu colors are distinct;
- pore/network architecture is clear;
- no obvious long-bond/PBC artifact in the selected whole images.

### Inset pair
**PASS — production crop needed**
- `D2_ab_plus` local Zn/Cu comparison is present;
- local objects are sharp;
- large surrounding white space should be cropped during layout.

## Panel C
### Whole pair
**PASS**
- frozen `c / up b` grid-like nbo view preserved;
- Zn/Cu endpoints remain strongly matched globally;
- visual quality is good.

### Inset pair
**PASS — production crop needed**
- `CARBOXY_face` is present;
- matching `M1 C4 O8` local context is clear;
- keep wording method-sensitive / distance-defined.

## Panel D
### Whole pair
**PASS**
- frozen near-null whole view preserved;
- i/ii pair remains appropriately similar;
- no obvious image-quality problem.

### Inset pair
**PASS — strongest crop requirement**
- `CTX2_ac_mixed` ethyl/methyl local comparison is present;
- the object is the smallest relative to canvas among the selected insets;
- crop very tightly in PowerPoint so the motif is legible.

## Panel E
### Whole pair
**PASS**
- frozen mapped fsc pair is preserved;
- local/whole chemistry is sharp;
- network scale is appropriate.

### Inset pair
**PASS — production crop needed**
- `Nfam_face` comparison is present;
- correct descriptive chemistry contrast is maintained;
- white margin can be reduced strongly in layout.

## Panel F
### Whole pair
**PASS**
- frozen repeated sra architecture is preserved;
- exploratory visual language remains restrained;
- output is sharp.

### Inset pair
**PASS — production crop needed**
- `DIST_D3_face` local cyano-bearing environments are present;
- both motifs are clear at native resolution;
- crop the white space in layout.

---

# Quality recommendation

## Do we need to rerender all 24 at more than 3200×2400?
**No, not at this stage.**

The 12 whole images are already comfortably publication-grade source rasters for a six-panel composite.
Increasing from 3200×2400 to 4800×3600 would substantially increase render time/file size but is unlikely to create a visible improvement at final journal dimensions.

## What should be improved instead?
1. Keep the 12 whole images as they are.
2. In PowerPoint, crop the large white margins from the 12 inset images.
3. Scale each inset to a consistent physical box while preserving paired i/ii scale logic.
4. Do not resample or screenshot the PNGs.
5. Keep the original PNG files linked/embedded directly.

If the final composed figure later requires a very large inset (e.g. >1–1.5 inches wide), rerender only that specific inset with a tighter OVITO FOV. There is no reason to rerender all 24 pre-emptively.

---

# Next step

The correct next stage is **PowerPoint layout prototyping**, not another broad OVITO render round.

Before final export, inspect the composed figure at 100% and 200% zoom. If any specific inset becomes visibly soft after being cropped and enlarged, rerender only that inset with a tighter FOV.
