
# Project 7B — Structural Panel PowerPoint MASTER ROADMAP
## Reviewed / Expanded V2 — Exact 84 × 56 cm construction manual

**Purpose:** build the final six-panel structural figure manually in PowerPoint from the already validated OVITO assets.

**Working-canvas decision:** **84.00 cm × 56.00 cm**, landscape, white background.

This is intentionally much larger than the normal PowerPoint template and larger than the previous working layouts. It gives enough room for:

- six panels,
- four images per panel,
- titles and subtitles,
- topology and status labels,
- four quantitative metrics per panel,
- paired local-chemistry labels,
- concise interpretation text,
- scientific caution notes.

> **Important:** a larger PowerPoint canvas is a *working-layout convenience*. It does not magically make tiny text readable after journal reduction. Therefore this roadmap gives you much more room, but it still limits visible text to information that deserves to be in the figure. Full provenance and long explanations belong in the manuscript caption/SI.

---

# 0. FINAL READINESS VERDICT — ARE THE IMAGES COMPLETE?

## Yes: the structural-image stage is complete enough to proceed to PowerPoint.

The final production package contains:

- **12 whole-structure images**
- **12 tightened inset images**
- all source PNGs = **3200 × 2400 px**
- metadata ≈ **600 dpi**
- lossless PNG
- white background
- frozen scientific selections

### Final inset automatic QA

| Panel | Endpoint i major occupancy | Endpoint ii major occupancy | Final decision |
|---|---:|---:|---|
| A | 60.1% | 58.7% | PASS |
| B | 60.5% | 58.9% | PASS |
| C | 59.8% | 58.2% | PASS |
| D | 59.6% | 50.7% | PASS WITH NOTE |
| E | 52.2% | 59.7% | PASS WITH NOTE |
| F | 56.8% | 59.5% | PASS |

The D_ii and E_i insets are slightly more conservative in occupancy than the nominal target, but they are not clipped and are acceptable for final composition. **Do not rerender them merely to chase a few percent more fill.**

### From this point onward

Do not reopen:
- CIF selection,
- camera selection,
- supercell search,
- inset chemistry selection,
- FOV screening,
- atom/bond palette selection.

Only fix something if a genuine technical error is discovered.

---

# 1. SCIENTIFIC SOURCE OF TRUTH

The figure is a **paired structural audit**.

The logic must remain:

- **whole view = global framework / geometry matching**
- **inset = local chemical contrast**
- **neither = mechanistic adsorption proof**

The six frozen panel roles and four panel metrics are:

| Panel | Role | Topology | Median |Δlog adsorption| | WC concordance | Selectivity concordance | Max geometry fraction/caliper |
|---|---|---|---:|---:|---:|---:|
| A | Strong linker / process aligned | pcu | 0.8119 | 1.00 | 1.00 | 0.897 |
| B | Strong metal / process aligned | nbo | 0.3067 | 1.00 | 1.00 | 0.666 |
| C | Cu–Zn boundary / pressure exception | nbo | 0.0820 | 1.00 | 1.00 | 0.842 |
| D | Near-null linker comparator | nbo | 0.0125 | 1.00 | 0.75 | 0.147 |
| E | Process-discordant linker comparator | fsc | 0.0641 | 0.20 | 0.25 | 0.790 |
| F | Exploratory functional-motif example | sra | 0.0596 | 0.80 | 1.00 | 0.449 |

Do not alter those numbers manually.

---

# 2. POWERPOINT DOCUMENT SETUP

## 2.1 Create the file

1. Open PowerPoint.
2. `New → Blank Presentation`.
3. `Home → Layout → Blank`.
4. Delete all default title/content placeholders.

## 2.2 Set the exact large slide

Go to:

`Design → Slide Size → Custom Slide Size`

Set:

- **Width = 84.00 cm**
- **Height = 56.00 cm**
- Orientation = **Landscape**
- Background = **solid white**
- Background RGB = **(255,255,255)**
- Background Hex = **#FFFFFF**

If PowerPoint shows a scaling dialogue, choose **Ensure Fit**.

## 2.3 Disable image compression BEFORE inserting PNGs

Go to:

`File → Options → Advanced → Image Size and Quality`

Set:

- **Do not compress images in file = ON**
- **Default resolution = High fidelity**

Do this before inserting any structural image.

## 2.4 Turn on build aids

Use:

`View → Ruler = ON`  
`View → Guides = ON`  
`View → Gridlines = ON while constructing`

Also enable:
- Snap objects to grid
- Snap objects to other objects

Use the **Selection Pane** throughout the build.

---

# 3. MASTER 3 × 2 GRID

## 3.1 Global geometry

- Slide: **84.00 × 56.00 cm**
- Outer margin: **1.40 cm**
- Column gap: **1.00 cm**
- Row gap: **1.20 cm**
- Panel width: **26.40 cm**
- Panel height: **26.00 cm**

## 3.2 Panel origins


| Panel | X | Y | W | H |
|---|---:|---:|---:|---:|
| A | 1.40 | 1.40 | 26.40 | 26.00 |
| B | 28.80 | 1.40 | 26.40 | 26.00 |
| C | 56.20 | 1.40 | 26.40 | 26.00 |
| D | 1.40 | 28.60 | 26.40 | 26.00 |
| E | 28.80 | 28.60 | 26.40 | 26.00 |
| F | 56.20 | 28.60 | 26.40 | 26.00 |


## 3.3 Exact guide coordinates

### Vertical

- 1.40 cm — left outer margin
- 27.80 cm — right edge A/D
- 28.80 cm — left edge B/E
- 55.20 cm — right edge B/E
- 56.20 cm — left edge C/F
- 82.60 cm — right edge C/F

### Horizontal

- 1.40 cm — top outer margin
- 27.40 cm — bottom edge A/B/C
- 28.60 cm — top edge D/E/F
- 54.60 cm — bottom edge D/E/F

---

# 4. GLOBAL COLOUR SYSTEM — EXACT RGB / HEX

## 4.1 Neutral system

| Use | RGB | Hex |
|---|---|---|
| Slide / panel white | (255,255,255) | `#FFFFFF` |
| Main text | (34,34,34) | `#222222` |
| Secondary text | (89,89,89) | `#595959` |
| Muted/caution text | (105,105,105) | `#696969` |
| Panel frame | (231,233,236) | `#E7E9EC` |
| Image border | (230,232,235) | `#E6E8EB` |
| Neutral border | (218,221,226) | `#DADDE2` |
| Metric-chip fill | (247,248,250) | `#F7F8FA` |
| Common accent | (63,108,142) | `#3F6C8E` |

## 4.2 Status palette

| Panel | Status | Fill | Text | Border |
|---|---|---|---|---|
| A | ALIGNED | `#EDF4F8` | `#3F6C8E` | `#A8C0D0` |
| B | ALIGNED | `#EDF4F8` | `#3F6C8E` | `#A8C0D0` |
| C | BOUNDARY | `#FFF4E5` | `#8A5D1F` | `#D7B277` |
| D | NEAR-NULL | `#F3F4F5` | `#5D6166` | `#C4C7CB` |
| E | DISCORDANT | `#FBF1EE` | `#8B4A3D` | `#D4A092` |
| F | EXPLORATORY | `#EFF7F5` | `#416F68` | `#9FC4BC` |

**Rule:** status colour encodes *scientific role*, not adsorption magnitude.

Do not create a blue-to-red heat map across A–F.

---

# 5. TYPOGRAPHY — ARIAL ONLY

Use **Arial everywhere**.

| Object | Font size on 84-cm canvas | Weight/style | Colour |
|---|---:|---|---|
| Panel letter | **42 pt** | Bold | `#3F6C8E` |
| Panel title | **34 pt** | Bold | `#222222` |
| Topology capsule | **20 pt** | Bold | `#595959` |
| Status capsule | **18 pt** | Bold | status text colour |
| Scientific subtitle | **24 pt** | Regular | `#595959` |
| Metric label | **21 pt** | Bold | `#696969` |
| Metric value | **30 pt** | Bold | `#222222` |
| Endpoint i / ii label | **23 pt** | Bold | `#222222` |
| Inset section heading | **22 pt** | Bold | `#595959` |
| Inset chemical label | **21 pt** | Regular | `#222222` |
| Interpretation sentence | **20 pt** | Regular | `#222222` |
| Caution/evidence footer | **19 pt** | Regular | `#595959` |

## 5.1 Text-box internal margins

For normal text boxes:
- left = **0.08 cm**
- right = **0.08 cm**
- top = **0.03 cm**
- bottom = **0.03 cm**
- vertical alignment = **Middle**
- paragraph before = **0 pt**
- paragraph after = **0 pt**
- line spacing = **1.0**
- **Do not automatically shrink text**

If text does not fit:
1. use the exact shorter wording in this roadmap,
2. never independently shrink one panel.

---

# 6. SHAPE / BOX / LINE RULES

## Panel frame

- Shape: Rectangle
- Corner: **square**
- Fill: white
- Line: `#E7E9EC`
- Width: **1.25 pt**
- Shadow: OFF
- Send to Back

## Common accent rule

- Solid horizontal line
- Colour: `#3F6C8E`
- Width: **3.00 pt**
- No arrowhead

## Whole-image border

- `#E6E8EB`
- **1.00 pt**
- square corners
- no shadow

## Inset-image border

- `#DADDE2`
- **1.50 pt**
- square corners
- no shadow

## Metric chips

- Shape: Rectangle
- **square corners**
- Fill: `#F7F8FA`
- Outline: `#DADDE2`
- Outline width: **1.25 pt**
- no shadow

## Topology capsule

- Shape: **Rounded Rectangle**
- Fill: `#F3F5F7`
- Border: `#DADDE2`
- Width: **1.25 pt**
- Use maximum PowerPoint roundness so it reads as a capsule

## Status capsule

- Shape: **Rounded Rectangle**
- Fill/text/border: panel-specific status palette
- Border width: **1.25 pt**
- maximum capsule roundness

## Footer accent

Put a short vertical line immediately to the left of the caution/evidence footer:
- colour = status text colour
- width = **3.00 pt**
- height ≈ **1.10 cm**

## Forbidden effects

Do not use:
- shadow
- glow
- soft edges
- bevel
- 3D
- gradient
- reflection
- SmartArt
- decorative icons

---

# 7. MASTER PANEL ANATOMY — RELATIVE X / Y / W / H

All coordinates are measured from the top-left corner of one 26.40 × 26.00 cm panel.


| Object | X | Y | W | H |
|---|---:|---:|---:|---:|
| Panel frame | 0.00 | 0.00 | 26.40 | 26.00 |
| Panel letter | 0.45 | 0.30 | 1.05 | 0.95 |
| Panel title | 1.70 | 0.22 | 16.25 | 0.82 |
| Topology capsule | 18.20 | 0.29 | 2.05 | 0.78 |
| Status capsule | 20.55 | 0.29 | 5.10 | 0.78 |
| Scientific subtitle | 1.70 | 1.12 | 23.95 | 0.70 |
| Accent rule | 0.45 | 1.98 | 25.50 | 0.00 |
| Metric chip 1 | 0.45 | 2.20 | 6.00 | 1.55 |
| Metric chip 2 | 6.80 | 2.20 | 6.00 | 1.55 |
| Metric chip 3 | 13.15 | 2.20 | 6.00 | 1.55 |
| Metric chip 4 | 19.50 | 2.20 | 6.00 | 1.55 |
| Endpoint i label | 0.45 | 3.96 | 12.25 | 0.52 |
| Endpoint ii label | 13.70 | 3.96 | 12.25 | 0.52 |
| Whole image i | 0.45 | 4.58 | 12.25 | 9.19 |
| Whole image ii | 13.70 | 4.58 | 12.25 | 9.19 |
| Inset section heading | 0.45 | 14.05 | 25.50 | 0.58 |
| Inset image i | 2.18 | 14.78 | 8.80 | 6.60 |
| Inset image ii | 15.43 | 14.78 | 8.80 | 6.60 |
| Inset label i | 2.18 | 21.52 | 8.80 | 0.70 |
| Inset label ii | 15.43 | 21.52 | 8.80 | 0.70 |
| Interpretation box | 0.45 | 22.42 | 25.50 | 1.32 |
| Caution / evidence footer | 0.45 | 23.92 | 25.50 | 1.48 |

### Why this anatomy is intentionally image-heavy

Each panel contains four images, but the two whole-framework images remain dominant.

The internal reading order is:

1. role / topology / status,
2. four quantitative evidence metrics,
3. whole-framework pair,
4. local inset pair,
5. one interpretation sentence,
6. one scientific caution/evidence footer.

There is **no arrow from i to ii**, because the two endpoints are a pair, not a physical transformation.

There are **no leader lines from whole structures to insets by default**. The vertical column structure already establishes pairing.

---

# 8. ABSOLUTE X / Y / W / H FOR EVERY OBJECT

Enter these values directly in `Format Shape → Size & Properties`.

All values are **cm**.


## Panel A


| Object | X | Y | W | H |
|---|---:|---:|---:|---:|
| Panel frame | 1.40 | 1.40 | 26.40 | 26.00 |
| Panel letter | 1.85 | 1.70 | 1.05 | 0.95 |
| Panel title | 3.10 | 1.62 | 16.25 | 0.82 |
| Topology capsule | 19.60 | 1.69 | 2.05 | 0.78 |
| Status capsule | 21.95 | 1.69 | 5.10 | 0.78 |
| Scientific subtitle | 3.10 | 2.52 | 23.95 | 0.70 |
| Accent rule | 1.85 | 3.38 | 25.50 | 0.00 |
| Metric chip 1 | 1.85 | 3.60 | 6.00 | 1.55 |
| Metric chip 2 | 8.20 | 3.60 | 6.00 | 1.55 |
| Metric chip 3 | 14.55 | 3.60 | 6.00 | 1.55 |
| Metric chip 4 | 20.90 | 3.60 | 6.00 | 1.55 |
| Endpoint i label | 1.85 | 5.36 | 12.25 | 0.52 |
| Endpoint ii label | 15.10 | 5.36 | 12.25 | 0.52 |
| Whole image i | 1.85 | 5.98 | 12.25 | 9.19 |
| Whole image ii | 15.10 | 5.98 | 12.25 | 9.19 |
| Inset section heading | 1.85 | 15.45 | 25.50 | 0.58 |
| Inset image i | 3.58 | 16.18 | 8.80 | 6.60 |
| Inset image ii | 16.83 | 16.18 | 8.80 | 6.60 |
| Inset label i | 3.58 | 22.92 | 8.80 | 0.70 |
| Inset label ii | 16.83 | 22.92 | 8.80 | 0.70 |
| Interpretation box | 1.85 | 23.82 | 25.50 | 1.32 |
| Caution / evidence footer | 1.85 | 25.32 | 25.50 | 1.48 |


## Panel B


| Object | X | Y | W | H |
|---|---:|---:|---:|---:|
| Panel frame | 28.80 | 1.40 | 26.40 | 26.00 |
| Panel letter | 29.25 | 1.70 | 1.05 | 0.95 |
| Panel title | 30.50 | 1.62 | 16.25 | 0.82 |
| Topology capsule | 47.00 | 1.69 | 2.05 | 0.78 |
| Status capsule | 49.35 | 1.69 | 5.10 | 0.78 |
| Scientific subtitle | 30.50 | 2.52 | 23.95 | 0.70 |
| Accent rule | 29.25 | 3.38 | 25.50 | 0.00 |
| Metric chip 1 | 29.25 | 3.60 | 6.00 | 1.55 |
| Metric chip 2 | 35.60 | 3.60 | 6.00 | 1.55 |
| Metric chip 3 | 41.95 | 3.60 | 6.00 | 1.55 |
| Metric chip 4 | 48.30 | 3.60 | 6.00 | 1.55 |
| Endpoint i label | 29.25 | 5.36 | 12.25 | 0.52 |
| Endpoint ii label | 42.50 | 5.36 | 12.25 | 0.52 |
| Whole image i | 29.25 | 5.98 | 12.25 | 9.19 |
| Whole image ii | 42.50 | 5.98 | 12.25 | 9.19 |
| Inset section heading | 29.25 | 15.45 | 25.50 | 0.58 |
| Inset image i | 30.98 | 16.18 | 8.80 | 6.60 |
| Inset image ii | 44.23 | 16.18 | 8.80 | 6.60 |
| Inset label i | 30.98 | 22.92 | 8.80 | 0.70 |
| Inset label ii | 44.23 | 22.92 | 8.80 | 0.70 |
| Interpretation box | 29.25 | 23.82 | 25.50 | 1.32 |
| Caution / evidence footer | 29.25 | 25.32 | 25.50 | 1.48 |


## Panel C


| Object | X | Y | W | H |
|---|---:|---:|---:|---:|
| Panel frame | 56.20 | 1.40 | 26.40 | 26.00 |
| Panel letter | 56.65 | 1.70 | 1.05 | 0.95 |
| Panel title | 57.90 | 1.62 | 16.25 | 0.82 |
| Topology capsule | 74.40 | 1.69 | 2.05 | 0.78 |
| Status capsule | 76.75 | 1.69 | 5.10 | 0.78 |
| Scientific subtitle | 57.90 | 2.52 | 23.95 | 0.70 |
| Accent rule | 56.65 | 3.38 | 25.50 | 0.00 |
| Metric chip 1 | 56.65 | 3.60 | 6.00 | 1.55 |
| Metric chip 2 | 63.00 | 3.60 | 6.00 | 1.55 |
| Metric chip 3 | 69.35 | 3.60 | 6.00 | 1.55 |
| Metric chip 4 | 75.70 | 3.60 | 6.00 | 1.55 |
| Endpoint i label | 56.65 | 5.36 | 12.25 | 0.52 |
| Endpoint ii label | 69.90 | 5.36 | 12.25 | 0.52 |
| Whole image i | 56.65 | 5.98 | 12.25 | 9.19 |
| Whole image ii | 69.90 | 5.98 | 12.25 | 9.19 |
| Inset section heading | 56.65 | 15.45 | 25.50 | 0.58 |
| Inset image i | 58.38 | 16.18 | 8.80 | 6.60 |
| Inset image ii | 71.63 | 16.18 | 8.80 | 6.60 |
| Inset label i | 58.38 | 22.92 | 8.80 | 0.70 |
| Inset label ii | 71.63 | 22.92 | 8.80 | 0.70 |
| Interpretation box | 56.65 | 23.82 | 25.50 | 1.32 |
| Caution / evidence footer | 56.65 | 25.32 | 25.50 | 1.48 |


## Panel D


| Object | X | Y | W | H |
|---|---:|---:|---:|---:|
| Panel frame | 1.40 | 28.60 | 26.40 | 26.00 |
| Panel letter | 1.85 | 28.90 | 1.05 | 0.95 |
| Panel title | 3.10 | 28.82 | 16.25 | 0.82 |
| Topology capsule | 19.60 | 28.89 | 2.05 | 0.78 |
| Status capsule | 21.95 | 28.89 | 5.10 | 0.78 |
| Scientific subtitle | 3.10 | 29.72 | 23.95 | 0.70 |
| Accent rule | 1.85 | 30.58 | 25.50 | 0.00 |
| Metric chip 1 | 1.85 | 30.80 | 6.00 | 1.55 |
| Metric chip 2 | 8.20 | 30.80 | 6.00 | 1.55 |
| Metric chip 3 | 14.55 | 30.80 | 6.00 | 1.55 |
| Metric chip 4 | 20.90 | 30.80 | 6.00 | 1.55 |
| Endpoint i label | 1.85 | 32.56 | 12.25 | 0.52 |
| Endpoint ii label | 15.10 | 32.56 | 12.25 | 0.52 |
| Whole image i | 1.85 | 33.18 | 12.25 | 9.19 |
| Whole image ii | 15.10 | 33.18 | 12.25 | 9.19 |
| Inset section heading | 1.85 | 42.65 | 25.50 | 0.58 |
| Inset image i | 3.58 | 43.38 | 8.80 | 6.60 |
| Inset image ii | 16.83 | 43.38 | 8.80 | 6.60 |
| Inset label i | 3.58 | 50.12 | 8.80 | 0.70 |
| Inset label ii | 16.83 | 50.12 | 8.80 | 0.70 |
| Interpretation box | 1.85 | 51.02 | 25.50 | 1.32 |
| Caution / evidence footer | 1.85 | 52.52 | 25.50 | 1.48 |


## Panel E


| Object | X | Y | W | H |
|---|---:|---:|---:|---:|
| Panel frame | 28.80 | 28.60 | 26.40 | 26.00 |
| Panel letter | 29.25 | 28.90 | 1.05 | 0.95 |
| Panel title | 30.50 | 28.82 | 16.25 | 0.82 |
| Topology capsule | 47.00 | 28.89 | 2.05 | 0.78 |
| Status capsule | 49.35 | 28.89 | 5.10 | 0.78 |
| Scientific subtitle | 30.50 | 29.72 | 23.95 | 0.70 |
| Accent rule | 29.25 | 30.58 | 25.50 | 0.00 |
| Metric chip 1 | 29.25 | 30.80 | 6.00 | 1.55 |
| Metric chip 2 | 35.60 | 30.80 | 6.00 | 1.55 |
| Metric chip 3 | 41.95 | 30.80 | 6.00 | 1.55 |
| Metric chip 4 | 48.30 | 30.80 | 6.00 | 1.55 |
| Endpoint i label | 29.25 | 32.56 | 12.25 | 0.52 |
| Endpoint ii label | 42.50 | 32.56 | 12.25 | 0.52 |
| Whole image i | 29.25 | 33.18 | 12.25 | 9.19 |
| Whole image ii | 42.50 | 33.18 | 12.25 | 9.19 |
| Inset section heading | 29.25 | 42.65 | 25.50 | 0.58 |
| Inset image i | 30.98 | 43.38 | 8.80 | 6.60 |
| Inset image ii | 44.23 | 43.38 | 8.80 | 6.60 |
| Inset label i | 30.98 | 50.12 | 8.80 | 0.70 |
| Inset label ii | 44.23 | 50.12 | 8.80 | 0.70 |
| Interpretation box | 29.25 | 51.02 | 25.50 | 1.32 |
| Caution / evidence footer | 29.25 | 52.52 | 25.50 | 1.48 |


## Panel F


| Object | X | Y | W | H |
|---|---:|---:|---:|---:|
| Panel frame | 56.20 | 28.60 | 26.40 | 26.00 |
| Panel letter | 56.65 | 28.90 | 1.05 | 0.95 |
| Panel title | 57.90 | 28.82 | 16.25 | 0.82 |
| Topology capsule | 74.40 | 28.89 | 2.05 | 0.78 |
| Status capsule | 76.75 | 28.89 | 5.10 | 0.78 |
| Scientific subtitle | 57.90 | 29.72 | 23.95 | 0.70 |
| Accent rule | 56.65 | 30.58 | 25.50 | 0.00 |
| Metric chip 1 | 56.65 | 30.80 | 6.00 | 1.55 |
| Metric chip 2 | 63.00 | 30.80 | 6.00 | 1.55 |
| Metric chip 3 | 69.35 | 30.80 | 6.00 | 1.55 |
| Metric chip 4 | 75.70 | 30.80 | 6.00 | 1.55 |
| Endpoint i label | 56.65 | 32.56 | 12.25 | 0.52 |
| Endpoint ii label | 69.90 | 32.56 | 12.25 | 0.52 |
| Whole image i | 56.65 | 33.18 | 12.25 | 9.19 |
| Whole image ii | 69.90 | 33.18 | 12.25 | 9.19 |
| Inset section heading | 56.65 | 42.65 | 25.50 | 0.58 |
| Inset image i | 58.38 | 43.38 | 8.80 | 6.60 |
| Inset image ii | 71.63 | 43.38 | 8.80 | 6.60 |
| Inset label i | 58.38 | 50.12 | 8.80 | 0.70 |
| Inset label ii | 71.63 | 50.12 | 8.80 | 0.70 |
| Interpretation box | 56.65 | 51.02 | 25.50 | 1.32 |
| Caution / evidence footer | 56.65 | 52.52 | 25.50 | 1.48 |



---

# 9. EXACT IMAGE FILES — WHAT TO INSERT WHERE

Use **whole images from `OVITO_final_HR`**.

Use **insets from `OVITO_final_insets_tight`**.

Do not use the older loose inset PNGs in `OVITO_final_HR`.


## Panel A

- Whole i → `OVITO_final_HR/A/A_i_whole_3200x2400_600dpi.png`
- Whole ii → `OVITO_final_HR/A/A_ii_whole_3200x2400_600dpi.png`
- Inset i → `OVITO_final_insets_tight/A/A_i_inset_TIGHT_3200x2400_600dpi.png`
- Inset ii → `OVITO_final_insets_tight/A/A_ii_inset_TIGHT_3200x2400_600dpi.png`


## Panel B

- Whole i → `OVITO_final_HR/B/B_i_whole_3200x2400_600dpi.png`
- Whole ii → `OVITO_final_HR/B/B_ii_whole_3200x2400_600dpi.png`
- Inset i → `OVITO_final_insets_tight/B/B_i_inset_TIGHT_3200x2400_600dpi.png`
- Inset ii → `OVITO_final_insets_tight/B/B_ii_inset_TIGHT_3200x2400_600dpi.png`


## Panel C

- Whole i → `OVITO_final_HR/C/C_i_whole_3200x2400_600dpi.png`
- Whole ii → `OVITO_final_HR/C/C_ii_whole_3200x2400_600dpi.png`
- Inset i → `OVITO_final_insets_tight/C/C_i_inset_TIGHT_3200x2400_600dpi.png`
- Inset ii → `OVITO_final_insets_tight/C/C_ii_inset_TIGHT_3200x2400_600dpi.png`


## Panel D

- Whole i → `OVITO_final_HR/D/D_i_whole_3200x2400_600dpi.png`
- Whole ii → `OVITO_final_HR/D/D_ii_whole_3200x2400_600dpi.png`
- Inset i → `OVITO_final_insets_tight/D/D_i_inset_TIGHT_3200x2400_600dpi.png`
- Inset ii → `OVITO_final_insets_tight/D/D_ii_inset_TIGHT_3200x2400_600dpi.png`


## Panel E

- Whole i → `OVITO_final_HR/E/E_i_whole_3200x2400_600dpi.png`
- Whole ii → `OVITO_final_HR/E/E_ii_whole_3200x2400_600dpi.png`
- Inset i → `OVITO_final_insets_tight/E/E_i_inset_TIGHT_3200x2400_600dpi.png`
- Inset ii → `OVITO_final_insets_tight/E/E_ii_inset_TIGHT_3200x2400_600dpi.png`


## Panel F

- Whole i → `OVITO_final_HR/F/F_i_whole_3200x2400_600dpi.png`
- Whole ii → `OVITO_final_HR/F/F_ii_whole_3200x2400_600dpi.png`
- Inset i → `OVITO_final_insets_tight/F/F_i_inset_TIGHT_3200x2400_600dpi.png`
- Inset ii → `OVITO_final_insets_tight/F/F_ii_inset_TIGHT_3200x2400_600dpi.png`



## 9.1 Exact picture settings

For all 24 images:

- `Insert → Pictures → This Device`
- do not paste screenshots
- do not drag from a browser
- lock aspect ratio
- no rotation in PowerPoint
- no colour correction
- no artistic effect
- no transparency
- no shadow
- no PowerPoint sharpening

### Whole image boxes

- W = **12.25 cm**
- H = **9.19 cm**
- native aspect ratio preserved

### Inset image boxes

- W = **8.80 cm**
- H = **6.60 cm**
- native aspect ratio preserved
- use the already-tightened final PNGs
- **do not crop them again**

---

# 10. METRIC CHIP SPECIFICATION

All panels use the same four metric labels in the same order:

1. `MEDIAN |ΔLOG ADS.|`
2. `WC CONCORD.`
3. `SELECTIVITY CONCORD.`
4. `MAX GEO./CALIPER`

Each chip contains two centered lines.

Example:

```text
MEDIAN |ΔLOG ADS.|
0.8119
```

Label:
- Arial 21 pt Bold
- `#696969`

Value:
- Arial 30 pt Bold
- `#222222`

## Exact values


| Panel | Median |Δlog adsorption| | WC concordance | Selectivity concordance | Max geometry fraction/caliper |
|---|---:|---:|---:|---:|
| A | 0.8119 | 1.00 | 1.00 | 0.897 |
| B | 0.3067 | 1.00 | 1.00 | 0.666 |
| C | 0.0820 | 1.00 | 1.00 | 0.842 |
| D | 0.0125 | 1.00 | 0.75 | 0.147 |
| E | 0.0641 | 0.20 | 0.25 | 0.790 |
| F | 0.0596 | 0.80 | 1.00 | 0.449 |

Do not:
- round them further,
- recolour chips based on magnitude,
- add “high/low” adjectives not present in the frozen interpretation.

---

# 11. EXACT COPY-PASTE TEXT FOR EACH PANEL

The wording below is designed to be copied directly into PowerPoint.


## PANEL A

**Panel letter**
```text
A
```

**Title**
```text
Strong linker / process aligned
```

**Topology capsule**
```text
pcu
```

**Status capsule**
```text
ALIGNED
```

**Scientific subtitle**
```text
Strong linker-family contrast under good geometric control
```

**Endpoint i label**
```text
i · whole framework
```

**Endpoint ii label**
```text
ii · whole framework
```

**Inset heading**
```text
Paired local linker / organic-environment contrast
```

**Inset i label**
```text
i · C₆NO₆ + 2 Zn anchors
```

**Inset ii label**
```text
ii · C₆N₄O₁₂ + 2 Zn anchors
```

**Interpretation box**
```text
Global pcu architecture remains matched while the local linker environment changes strongly.
```

**Caution / evidence footer**
```text
Strong chemistry/process-aligned linker case. The local view is structural context only; do not label it an adsorption site.
```


## PANEL B

**Panel letter**
```text
B
```

**Title**
```text
Strong metal / process aligned
```

**Topology capsule**
```text
nbo
```

**Status capsule**
```text
ALIGNED
```

**Scientific subtitle**
```text
Metal-identity contrast with the strongest local node comparison
```

**Endpoint i label**
```text
i · whole framework
```

**Endpoint ii label**
```text
ii · whole framework
```

**Inset heading**
```text
Paired local metal-node comparison
```

**Inset i label**
```text
i · Zn local node
```

**Inset ii label**
```text
ii · Cu local node
```

**Interpretation box**
```text
The global nbo scaffold is matched while the principal local contrast is metal identity.
```

**Caution / evidence footer**
```text
This is the safest local metal-node example. Keep the interpretation structural/descriptive rather than mechanistic.
```


## PANEL C

**Panel letter**
```text
C
```

**Title**
```text
Cu–Zn boundary / pressure-exception case
```

**Topology capsule**
```text
nbo
```

**Status capsule**
```text
BOUNDARY
```

**Scientific subtitle**
```text
Matched Cu/Zn boundary case with method-sensitive local chemistry
```

**Endpoint i label**
```text
i · whole framework
```

**Endpoint ii label**
```text
ii · whole framework
```

**Inset heading**
```text
Distance-defined local comparison
```

**Inset i label**
```text
i · ZnC₄O₈ · Zn–O ≈ 2.024–2.029 Å
```

**Inset ii label**
```text
ii · CuC₄O₈ · Cu–O ≈ 1.951–1.956 Å
```

**Interpretation box**
```text
Strong global nbo matching; local Zn/Cu context is shown cautiously as a boundary comparison.
```

**Caution / evidence footer**
```text
Method-sensitive selected sites = 8. Use “distance-defined / method-sensitive local comparison”; never “active site” or validated mechanism.
```


## PANEL D

**Panel letter**
```text
D
```

**Title**
```text
Near-null linker comparator
```

**Topology capsule**
```text
nbo
```

**Status capsule**
```text
NEAR-NULL
```

**Scientific subtitle**
```text
Control-like linker comparison under the strongest geometric control
```

**Endpoint i label**
```text
i · whole framework
```

**Endpoint ii label**
```text
ii · whole framework
```

**Inset heading**
```text
Paired local linker contrast
```

**Inset i label**
```text
i · backbone–CH₂–CH₃
```

**Inset ii label**
```text
ii · backbone–CH₃
```

**Interpretation box**
```text
The endpoints are globally extremely similar; a real local linker difference remains visible.
```

**Caution / evidence footer**
```text
Near-null comparator, not “inactive” and not “no effect.” Preserve the intentionally subtle visual contrast.
```


## PANEL E

**Panel letter**
```text
E
```

**Title**
```text
Process-discordant linker comparator
```

**Topology capsule**
```text
fsc
```

**Status capsule**
```text
DISCORDANT
```

**Scientific subtitle**
```text
Visible local organic-chemistry contrast; process interpretation remains descriptive
```

**Endpoint i label**
```text
i · whole framework
```

**Endpoint ii label**
```text
ii · whole framework
```

**Inset heading**
```text
Paired local organic-chemistry contrast
```

**Inset i label**
```text
i · C₂₈H₁₂N₂O₈
```

**Inset ii label**
```text
ii · C₂₆H₁₂N₂O₄
```

**Interpretation box**
```text
The matched fsc scaffold contains a visible local chemistry difference despite discordant process behavior.
```

**Caution / evidence footer**
```text
Do not claim that this chosen local motif explains the process discordance. Show the chemistry difference only.
```


## PANEL F

**Panel letter**
```text
F
```

**Title**
```text
Exploratory functional-motif example
```

**Topology capsule**
```text
sra
```

**Status capsule**
```text
EXPLORATORY
```

**Scientific subtitle**
```text
Exploratory cyano-bearing local-environment contrast within a repeated sra scaffold
```

**Endpoint i label**
```text
i · whole framework
```

**Endpoint ii label**
```text
ii · whole framework
```

**Inset heading**
```text
Graph-depth-3 cyano-bearing local contrast
```

**Inset i label**
```text
i · C₉N₃ local crop
```

**Inset ii label**
```text
ii · C₁₁N local crop
```

**Interpretation box**
```text
A repeated sra scaffold is retained while the local cyano-bearing linker environment differs.
```

**Caution / evidence footer**
```text
Parent cyano-bearing linker classes: C₁₇H₇N₅O₄ vs C₁₉H₇NO₄. Keep this explicitly exploratory; no class-wide causal law.
```



---

# 12. PANEL-BY-PANEL SCIENTIFIC GUARDRAILS

## A — strong linker / process aligned

Endpoint IDs:
- i: `DB0-m3_o11_o17_f0_pcu.sym.32`
- ii: `DB0-m3_o12_o20_f0_pcu.sym.24`

The figure may say:
- strong linker contrast
- matched pcu scaffold
- geometry-controlled

The figure must not say:
- this linker is the adsorption site
- this atom causes the response

---

## B — strong metal / process aligned

Endpoint IDs:
- i: `DB0-m3_o7_o7_f0_nbo.sym.48`
- ii: `DB0-m2_o7_o7_f0_nbo.sym.45`

Allowed:
- Zn local node
- Cu local node
- strong metal-node contrast

Avoid:
- causal adsorption mechanism

---

## C — Cu/Zn boundary case

Endpoint IDs:
- i: `DB0-m3_o6_o27_f0_nbo.sym.33`
- ii: `DB0-m2_o6_o27_f0_nbo.sym.30`

Additional validated local context:
- ZnC₄O₈ local fragment
- CuC₄O₈ local fragment
- Zn–O ≈ 2.024–2.029 Å
- Cu–O ≈ 1.951–1.956 Å
- method-sensitive selected sites = 8

Required caution words:
- boundary
- method-sensitive
- distance-defined

Never write:
- robust coordination mechanism
- active site
- adsorption site
- validated pressure-effect mechanism

---

## D — near-null comparator

Endpoint IDs:
- i: `DB0-m2_o23_o28_f0_nbo.sym.21`
- ii: `DB0-m2_o23_o28_f0_nbo.sym.4`

Local contrast:
- i: backbone–CH₂–CH₃
- ii: backbone–CH₃

Allowed:
- near-null comparator
- strong geometric control

Never:
- inactive
- no effect

---

## E — process-discordant comparator

Endpoint IDs:
- i: `DB0-m3_o440_o155_f0_fsc.sym.26`
- ii: `DB0-m3_o152_o155_f0_fsc.sym.27`

Local inset:
- i: C₂₈H₁₂N₂O₈
- ii: C₂₆H₁₂N₂O₄

Allowed:
- process-discordant
- descriptive chemistry contrast

Never:
- this motif causes the discordance
- this motif explains the process behavior

---

## F — exploratory motif example

Endpoint IDs:
- i: `DB0-m9_o17_o27_f0_sra.sym.117`
- ii: `DB0-m9_o17_o27_f0_sra.sym.116`

Local crop:
- i: C₉N₃
- ii: C₁₁N

Parent cyano-bearing linker classes:
- C₁₇H₇N₅O₄
- C₁₉H₇NO₄

Allowed:
- exploratory
- local cyano-bearing environment contrast

Never:
- universal functional-group law
- causal mechanism

---

# 13. WHAT TO KEEP OUT OF THE VISIBLE FIGURE

The following are important for provenance, but **do not print them inside each panel**:

- full database endpoint IDs
- OVITO camera names
- supercell replication values
- FOV factors
- phase values
- script filenames
- long validation explanations

Why?

Because the final journal figure will be reduced substantially. If you force all provenance into the artwork, you will end up with unreadable text and the structures will become secondary.

Keep the full endpoint IDs in:
- the manuscript caption,
- SI,
- or this roadmap.

---

# 14. Z-ORDER / LAYER ORDER

For each panel, use this z-order from back to front:

1. Panel frame
2. Whole images
3. Inset images
4. Metric-chip rectangles
5. Topology/status capsules
6. Accent rule
7. All text boxes
8. Footer vertical accent line

No transparent objects should cover the structural images.

---

# 15. SELECTION PANE NAMING

Name every object.

Example for Panel A:

```text
A_FRAME
A_LETTER
A_TITLE
A_TOPOLOGY
A_STATUS
A_SUBTITLE
A_RULE
A_METRIC1
A_METRIC2
A_METRIC3
A_METRIC4
A_LABEL_i
A_LABEL_ii
A_WHOLE_i
A_WHOLE_ii
A_INSET_HEADING
A_INSET_i
A_INSET_ii
A_INSET_LABEL_i
A_INSET_LABEL_ii
A_INTERPRETATION
A_FOOTER
A_FOOTER_RULE
```

Repeat exactly with B, C, D, E, F.

This makes later revisions dramatically safer.

---

# 16. MANUAL BUILD ORDER — DO THIS EXACTLY

## Stage 1 — create the master slide

1. Blank slide.
2. 84 × 56 cm.
3. White background.
4. Disable image compression.
5. Add guides.
6. Save immediately as:
   `Project7B_StructuralPanel_MASTER_v01.pptx`

## Stage 2 — build Panel A completely

Build only A first.

Order:
1. A frame
2. A letter
3. title
4. topology capsule
5. status capsule
6. subtitle
7. accent rule
8. metric chips
9. endpoint labels
10. whole i
11. whole ii
12. inset heading
13. inset i
14. inset ii
15. inset labels
16. interpretation box
17. footer
18. footer vertical accent

Then compare all X/Y/W/H against this roadmap.

## Stage 3 — duplicate the A skeleton

Duplicate A panel skeleton five times.

Move each copy to:
- B origin
- C origin
- D origin
- E origin
- F origin

Do not rebuild the geometry from scratch.

## Stage 4 — replace panel-specific content

For B–F replace:
- letter
- title
- topology
- status
- subtitle
- metrics
- four PNGs
- inset labels
- interpretation
- footer

## Stage 5 — group only after QC

After each panel passes:
- group that panel,
- name group `PANEL_A`, `PANEL_B`, etc.

Do not group all six panels together until the entire figure is complete.

---

# 17. ALIGNMENT / DISTRIBUTION RULES

For every panel:

- title left aligned
- subtitle left aligned
- topology/status aligned on same baseline
- metric chips equal W/H
- metric chips equally spaced
- endpoint labels centered over whole images
- whole i/ii top edges identical
- whole i/ii bottom edges identical
- inset i/ii top edges identical
- inset i/ii bottom edges identical
- inset labels centered below corresponding inset
- interpretation and footer aligned to whole-image left edge
- nothing crosses panel border

Do not visually “nudge” one panel if exact coordinates already exist.

---

# 18. SHOULD YOU ADD ARROWS OR CALLOUTS?

Default answer: **no**.

The structural images and paired inset labels already carry the message.

Do not add:
- arrows between i and ii
- “transition” arrows
- adsorption arrows
- active-site circles
- magnifying-glass icons
- molecular-mechanism annotations

Only add a connector later if a final manuscript review shows that a reader genuinely cannot associate an inset with its endpoint.

---

# 19. POWERPOINT IMAGE QUALITY — WHAT NOT TO DO

Do not:

- use screenshots
- paste from clipboard
- export images from WhatsApp/Telegram
- save a contact sheet and use it instead of the source PNG
- crop and then re-save the PNG in Paint
- recolour OVITO atoms
- sharpen with PowerPoint
- apply transparency
- rescale one endpoint differently just to make it look more similar

The final source PNGs are already high quality.

---

# 20. EXPORT WORKFLOW

## Master

Keep the `.pptx`.

Recommended name:
`Project7B_StructuralPanel_MASTER_v01.pptx`

Increment:
- v02
- v03
- FINAL

Do not overwrite every previous milestone.

## Primary publication master

Use:

`File → Export → Create PDF/XPS`

Choose:
- Standard / publishing quality
- full slide
- no notes/comments

Why PDF:
- Arial text remains vector
- PowerPoint shapes remain vector
- the 600-dpi molecular PNGs remain embedded at high quality

## Raster version

If the journal requires TIFF/PNG:

1. export the high-quality PDF,
2. rasterize the PDF at the required final width and dpi,
3. inspect the raster at 100% and 200%.

Do not depend on PowerPoint's default low-resolution “Save as PNG” output as the journal master.

---

# 21. FINAL QC — BEFORE YOU CALL THE FIGURE DONE

## Files

- [ ] 12 whole PNGs from `OVITO_final_HR`
- [ ] 12 tightened inset PNGs from `OVITO_final_insets_tight`
- [ ] no old loose inset used

## Canvas

- [ ] 84 × 56 cm
- [ ] white background
- [ ] 3 × 2 panel grid
- [ ] identical panel dimensions

## Typography

- [ ] Arial only
- [ ] no auto-shrunk text
- [ ] titles same size
- [ ] metrics same size
- [ ] panel letters uppercase A–F

## Numbers

- [ ] A = 0.8119 / 1.00 / 1.00 / 0.897
- [ ] B = 0.3067 / 1.00 / 1.00 / 0.666
- [ ] C = 0.0820 / 1.00 / 1.00 / 0.842
- [ ] D = 0.0125 / 1.00 / 0.75 / 0.147
- [ ] E = 0.0641 / 0.20 / 0.25 / 0.790
- [ ] F = 0.0596 / 0.80 / 1.00 / 0.449
- [ ] C note = method-sensitive selected sites = 8

## Scientific interpretation

- [ ] A = strong linker case
- [ ] B = strong metal-node case
- [ ] C = boundary / method-sensitive case
- [ ] D = near-null comparator
- [ ] E = process-discordant descriptive case
- [ ] F = explicitly exploratory
- [ ] no active-site claims
- [ ] no mechanistic arrows
- [ ] no causal explanation invented

## Visual

- [ ] whole structures dominate
- [ ] all images keep 4:3 aspect ratio
- [ ] no image is stretched
- [ ] no one panel looks like a different design system
- [ ] status capsule is the only panel-specific semantic colour
- [ ] no heavy black panel borders
- [ ] no shadows
- [ ] no gradients

---

# 22. FINAL “DO NOT DO” LIST

Do not:

1. reopen OVITO screening,
2. change a frozen inset winner,
3. use the loose inset files,
4. change frozen numbers,
5. infer mechanism from local structure,
6. call C a robust coordination example,
7. call D inactive,
8. explain E discordance structurally,
9. generalize F as a universal motif law,
10. use non-Arial fonts,
11. shrink everything just to fit more text,
12. add full CIF IDs inside every panel,
13. create decorative arrows,
14. use dark backgrounds,
15. apply PowerPoint image corrections,
16. use rounded cards everywhere,
17. use excessive colour,
18. export the final journal figure from a screenshot.

---

# 23. WHAT TO DO IF THE FIGURE STILL FEELS CROWDED

Remove content in this order:

1. shorten the caution/evidence footer,
2. shorten the scientific subtitle,
3. shorten inset label text,
4. move endpoint IDs to caption/SI,
5. remove interpretation box only if the manuscript caption already carries the point.

Do **not**:
- shrink whole structures,
- shrink all fonts,
- shrink insets,
- hide quantitative evidence.

---

# 24. EXACT ENDPOINT PROVENANCE — CAPTION / SI REFERENCE


| Panel | Endpoint i | Endpoint ii |
|---|---|---|
| A | DB0-m3_o11_o17_f0_pcu.sym.32 | DB0-m3_o12_o20_f0_pcu.sym.24 |
| B | DB0-m3_o7_o7_f0_nbo.sym.48 | DB0-m2_o7_o7_f0_nbo.sym.45 |
| C | DB0-m3_o6_o27_f0_nbo.sym.33 | DB0-m2_o6_o27_f0_nbo.sym.30 |
| D | DB0-m2_o23_o28_f0_nbo.sym.21 | DB0-m2_o23_o28_f0_nbo.sym.4 |
| E | DB0-m3_o440_o155_f0_fsc.sym.26 | DB0-m3_o152_o155_f0_fsc.sym.27 |
| F | DB0-m9_o17_o27_f0_sra.sym.117 | DB0-m9_o17_o27_f0_sra.sym.116 |

---

# 25. FINAL RECOMMENDATION

Use this **84 × 56 cm V2** layout as the manual PowerPoint master.

It is intentionally much larger than the original PowerPoint template and larger than the previous structural-panel layout.

The correct balance is:

- structures = visual center of gravity,
- quantitative metrics = compact evidence layer,
- text = interpretation and scientific boundaries,
- full provenance = caption/SI.

The final figure should look like one coherent matched-pair experiment, not six unrelated crystal screenshots.

## Final workflow from here

```text
Validated OVITO whole structures
+
validated tightened local insets
        ↓
84 × 56 cm PowerPoint master
        ↓
Panel A exact template
        ↓
duplicate skeleton to B–F
        ↓
replace text / metrics / images
        ↓
manual alignment QC
        ↓
scientific wording QC
        ↓
high-quality PDF export
        ↓
journal-specific raster conversion only if required
```

**There is no reason to reopen the structural rendering stage unless a true error is discovered.**
