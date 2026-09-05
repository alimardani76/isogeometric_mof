# Project 7B — Final High-Resolution Rendering Specification

## Decision
The scientific selection stage is complete. Do **not** reopen camera, supercell, chemistry, or inset selection.

The next stage is final production rendering.

## Recommended image specification

Use **600 dpi**, not 500 dpi.

DPI metadata alone is not enough; the actual pixel dimensions matter more.

Recommended master render size for every endpoint image:

```text
3200 × 2400 px
600 dpi metadata
4:3 aspect ratio
PNG, lossless
white background
orthographic projection
anti-aliasing ON
ambient occlusion OFF
shadows OFF
simulation-cell outline OFF
```

Why 600 dpi:
- conventional publication-grade target for structure/line-heavy raster artwork;
- gives headroom for cropping and PowerPoint placement;
- easy to downsample later if a journal asks for 300 dpi;
- avoids any need to upscale.

For the final figure, render **24 source PNGs**:
- 6 panels × 2 endpoints × 2 roles (whole + inset)

These 24 source PNGs become **12 logical paired assets** in PowerPoint:
- 6 whole-view pairs
- 6 inset pairs

Do not pre-combine i/ii endpoints into one raster image unless a final journal workflow specifically requires it.

---

# Frozen views — source of truth

## Panel A — strong linker / process aligned

### Whole
```text
A_i view        = a
A_ii view       = c
family          = mapped M1
A_i context     = 1×5×5
A_ii context    = 5×5×1
phase           = 00
FOV factor      = 0.88
projection      = orthographic
H               = hidden
AO              = off
cell box        = off
```

### Inset
```text
winner          = NITRO_plusZn_face
A_i target      = C6N1O6 + 2 Zn anchors
A_ii target     = C6N4O12 + 2 Zn anchors
orientation     = face-on
matched scale   = yes
```

---

## Panel B — strong metal / process aligned

### Whole
```text
view            = c_plus
context         = 3×3×1
phase           = phase_00
FOV factor      = 0.96
style           = B04 balanced
projection      = orthographic
H               = hidden
AO              = off
cell box        = off
```

### Inset
```text
winner          = D2_ab_plus
role            = metal-node comparison
use frozen B local extraction/camera settings
```

---

## Panel C — Cu/Zn boundary case

### Whole
```text
view normal     = c
camera up       = b
C_i context     = 4×4×1
C_ii context    = 4×4×1
case            = BUFFER_441_ref
FOV factor      = 1.00
projection      = orthographic
H               = hidden
AO              = off
cell box        = off
```

### Inset
```text
winner          = CARBOXY_face
C_i fragment    = Zn1 C4 O8
C_ii fragment   = Cu1 C4 O8
orientation     = face-on
matched scale   = yes
interpretation  = distance-defined / method-sensitive local comparison
```

Do not label this as robust coordination or a mechanism.

---

## Panel D — near-null linker comparator

### Whole
```text
view            = c_plus
context         = 3×3×1
phase           = half-a
FOV factor      = 0.75
projection      = orthographic
H               = hidden
AO              = off
cell box        = off
```

### Inset
```text
winner          = CTX2_ac_mixed
D_i             = backbone–CH2–CH3
D_ii            = backbone–CH3
matched context = yes
```

---

## Panel E — process-discordant linker comparator

### Whole
```text
family          = P1_U2_up_b_to_a

E_i:
  view          = a
  camera up     = b
  context       = 1×4×4

E_ii:
  view          = c
  camera up     = a
  context       = 4×4×1

case            = BUFFER_144_ref
FOV factor      = 1.00
projection      = orthographic
H               = hidden
AO              = off
cell box        = off
```

### Inset
```text
winner          = Nfam_face
E_i             = C28H12N2O8
E_ii            = C26H12N2O4
Zn anchors      = hidden
orientation     = face-on
matched scale   = yes
```

Descriptive chemistry contrast only; do not imply mechanism.

---

## Panel F — exploratory functional-motif example

### Whole
```text
view normal     = a
camera up       = c
F_i context     = 1×5×5
F_ii context    = 1×5×5
case            = PRIMARY_buffer_155_context
FOV factor      = 1.08
projection      = orthographic
H               = hidden
AO              = off
cell box        = off
```

### Inset
```text
winner          = DIST_D3_face
F_i local crop  = C9N3
F_ii local crop = C11N1
graph depth     = 3
orientation     = face-on
matched scale   = yes
```

Keep the inset visually quieter than A/B because F is exploratory.

---

# Final inset framing rule

The scientific selection is frozen, but the review inset renders were intentionally loose.

During high-resolution rendering:
- keep the selected local fragment exactly;
- keep matched physical scale between i and ii;
- rotate only to enforce the already-frozen face/oblique orientation;
- tighten the camera field so the fragment occupies about **55–70%** of the inset canvas;
- leave comfortable white margin;
- do not change which atoms are included.

This is production framing, not a new selection round.

---

# Recommended output folder

```text
Project7B_Final_HR/
│
├── A/
│   ├── A_i_whole_3200x2400_600dpi.png
│   ├── A_ii_whole_3200x2400_600dpi.png
│   ├── A_i_inset_3200x2400_600dpi.png
│   └── A_ii_inset_3200x2400_600dpi.png
│
├── B/
├── C/
├── D/
├── E/
└── F/
```

Total source renders: **24 PNG files**.

---

# Quality-control checklist after rendering

For every i/ii pair check:

1. exact frozen camera/view is preserved;
2. exact frozen replication/context is preserved;
3. i and ii use matched physical scale;
4. no PBC bond artifacts;
5. no clipped important atoms/bonds;
6. no accidental cell outline;
7. no hydrogens in whole views;
8. atom colors are consistent between panels;
9. white background is pure white;
10. no labels baked into the OVITO raster;
11. no PowerPoint arrows/text baked into the image;
12. inset object size is balanced between i and ii.

---

# What comes after high-resolution rendering

Only after all 24 source PNGs pass QC:

1. open PowerPoint;
2. build six panel containers A–F;
3. place i/ii whole renders;
4. place paired inset renders;
5. add panel letters and i/ii labels as vector PowerPoint text;
6. add small descriptive subtitles/callouts;
7. align spacing, scale, and inset placement;
8. export the final composite to PDF and high-resolution TIFF/PNG if required by the journal.

No scientific geometry selection should occur during PowerPoint assembly.
