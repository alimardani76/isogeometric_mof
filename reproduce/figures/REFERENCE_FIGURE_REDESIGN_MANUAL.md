# Project 7B — Deep Quantitative Figure Redesign Manual

## 1. Mission

Regenerate the paper's quantitative visual system from the frozen source tables. The aim is not cosmetic recoloring alone. The redesign should make the scientific argument easier to understand and reduce the “internal report / audit dashboard” feel of the current figures.

The redesign must **not** recompute scientific estimates, alter conditions, change case selection, suppress uncertainty, or use outcome-driven filtering.

## 2. Final visual story

The visual sequence should read like a scientific argument:

1. **What was controlled and how much support exists?**
2. **Does chemistry separate beyond the matched background?**
3. **How does the signal depend on guest and pressure?**
4. **Does it survive into process-relevant metrics and where does it fail?**
5. **What do representative matched structures actually look like?**
6. **Do selected cases survive an independent common molecular model?**

This is much stronger than a sequence of workflow/status-card figures.

## 3. Main-text architecture

Use `FINAL_FIGURE_ARCHITECTURE.csv` as the governing source map.

### Figure 1 — matched-comparison architecture and support

Keep the conceptual design, but redesign panel A from a report flowchart into a compact scientific schematic:

`MOF population → exact topology/dimensionality → seven geometry calipers → chemistry-change class → matched contrast → dependence family`

Use actual numbers only where they advance the story. Avoid large rounded rectangles containing sentences.

Recommended panels:
- A: design schematic;
- B: cohort/support funnel;
- C: support as geometry constraints tighten;
- D: evidence units / dependence-family concept.

### Figure 2 — chemistry above matched background

This is the quantitative center of the paper.

Recommended:
- A: linker vs same-chemistry controls across 18 conditions, preferably compact point-range or paired estimate display;
- B: symmetric nearest-pair confirmation;
- C: HOA–adsorption association summary;
- D: unadjusted vs residual-geometry-adjusted linker contrast.

Avoid a 4-panel figure in which every panel uses a different grammar. Use one shared outcome/condition ordering and shared intervention colors.

### Figure 3 — guest and pressure boundary

The purpose is not to show every number. The purpose is to show that the hierarchy is guest/regime dependent.

Recommended:
- A/B: paired CO2–co-guest chemistry-associated adsorption separation by process family;
- C: energetic contrast counterpart;
- D: high-pressure precombustion boundary where chemistry-associated H2 adsorption separation can exceed CO2 while CO2 retains the larger energetic separation.

Never phrase this as “H2 has higher uptake” unless the plotted quantity is raw uptake. The paper is about **chemistry-associated separation**.

### Figure 4 — process translation and applicability boundary

Use the current process-translation science as a main figure because it converts adsorption contrast into a design boundary.

Recommended:
- A: working-capacity concordance;
- B: selectivity concordance;
- C: selected process-aligned vs discordant case examples;
- D: a small, data-driven applicability/boundary panel.

The old robustness/audit Figure 4 should mostly move to SI.

### Figure 5
Owned by the structural-panel workstream. Do not recreate it here.

### Figure 6 — RASPA selected-case validation

Use one compact main figure after the RASPA workstream locks the final scientific interpretation. The figure-redesign workstream can harmonize fonts, palette, axes, and panel spacing, but must not silently change pair definitions or metrics.

## 4. SI architecture

Do not generate more SI merely to look comprehensive. The SI should hold evidence that is necessary for auditability but would interrupt the main story.

Recommended:
- S1: matching/control/topology/family robustness;
- S2: detailed HOA associations;
- S3: detailed guest/pressure results;
- S4: residual geometry/balance/family dominance if not fully covered in S1;
- S5: structural geometry-control proof or extra endpoint details;
- S6: full RASPA eight-pair summary/protocol diagnostics.

Do not include the RASPA density projection because its raw grids and generation code are unavailable.

## 5. Typography specification

Use **Arial** wherever available; a metrically compatible sans-serif fallback is acceptable only if the environment does not contain Arial. Record the fallback in the manifest.

At final journal width, target approximately:
- panel letters: 11–12 pt equivalent, bold;
- axis titles: 8.5–9.5 pt, bold;
- tick labels: 7.5–8.5 pt;
- legend labels: 7.5–8.5 pt;
- annotation text: never below ~7.5 pt unless unavoidable.

Use sentence case for axis labels; use uppercase panel letters.

## 6. Line/marker specification

Suggested final-size values:
- main axes: 0.8–1.0 pt;
- data lines: 1.2–1.6 pt;
- uncertainty/error bars: 0.9–1.2 pt;
- marker edge: ~0.6 pt;
- marker size: chosen so symbols remain distinct after 50% reduction.

Do not rely on transparency alone to separate groups.

## 7. Palette strategy

Use a deliberate chemistry/science palette, not Matplotlib defaults.

Recommended semantic color roles:
- linker-family: deep blue/indigo;
- metal substitution: warm orange/vermillion;
- functional motif exploratory: muted purple or neutral secondary hue;
- same-chemistry controls: graphite/gray;
- CO2: one consistent dark teal/green-blue;
- co-guest: contrasting warm/neutral color;
- RASPA full electrostatics: dark saturated color;
- charge-off sensitivity: light/neutral counterpart.

The exact RGB/hex values should be frozen in one style module and reused across all figures. Color must encode the same semantic category everywhere.

Avoid:
- rainbow palettes;
- default tab10;
- pale pastel on white;
- red/green-only categorical distinctions;
- more than ~5 semantic colors in a single panel.

## 8. Layout rules

- White background.
- Remove top/right spines unless they carry information.
- Use shared axes where scientifically appropriate.
- Align panel plotting areas exactly.
- Minimize legends by direct labeling when possible.
- Never place a large legend over data.
- Use consistent condition ordering across all figures.
- Use compact panel titles, not prose paragraphs.
- Avoid card-like status summaries in main figures.
- Avoid excessive rounded boxes.

## 9. Data-integrity rules

Every final panel must have:
1. a plot-ready source CSV/JSON;
2. a single canonical plotting script;
3. PDF, SVG, and 600-dpi PNG outputs;
4. source/script/output SHA-256 manifest.

If a panel needs transformation from an existing source table, create a deterministic `source_panel_X.csv` from the frozen input and preserve the transformation code. Do not hand-edit plotted numbers in Illustrator/PowerPoint.

## 10. Historical renderer rule

The `historical_renderer_reference/` scripts are **references only**. Do not attempt to identify a sacred old v8/v9 file and continue patching it indefinitely. Create a new canonical submission renderer with clear input paths and a style helper.

Use `code_helpers/project7_publication_style.py` as a starting point, but modify it if the final visual system can be improved. The final code must be self-contained enough that another person can regenerate the figures from the supplied plot-ready tables.

## 11. Figure-by-figure scientific no-go rules

### Figure 1
Do not imply the geometry calipers make pairs truly isostructural or remove all geometric differences.

### Figure 2
Do not turn the adjusted linker coefficient into a mediated/direct causal effect. It is an associational sensitivity estimate.

### Figure 3
Do not confuse chemistry-associated difference with raw uptake. Keep pressure/guest comparisons tied to their actual process regimes.

### Figure 4
Do not imply uptake improvement guarantees process improvement. The purpose of the figure is partly to show the opposite.

### Figure 6 RASPA
Do not label all eight pairs “pre-frozen”; use six frozen primary structural cases plus two additional linker comparators unless stronger provenance is supplied. Do not use the density map.

## 12. Deliverables

For each final figure folder:

```text
Figure_0X/
  Figure_0X.pdf
  Figure_0X.svg
  Figure_0X_600dpi.png
  plot_Figure_0X.py
  source_panel_A.csv
  source_panel_B.csv
  ...
  manifest.json
  render_log.txt
```

Also deliver:
- `FINAL_FIGURE_STYLE_SPEC.md`;
- `FINAL_FIGURE_PALETTE.json`;
- `all_figure_manifest.csv`;
- one contact-sheet PNG showing all main figures at similar apparent size;
- one contact-sheet PNG showing all SI figures.

## 13. Acceptance tests

A redesigned figure passes only if:
- a reader can understand the intended scientific claim before reading the caption;
- all numerical values trace to supplied source data;
- uncertainty is visible where appropriate;
- text remains readable at final width;
- colors have consistent semantics across the paper;
- no main panel looks like an internal project-management dashboard;
- the figure can be regenerated from code without manual number edits.
