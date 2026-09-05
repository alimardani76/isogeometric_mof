# Paper 7B final quantitative figure style

## Scope
This package regenerates main Figures 1–4 and 6 plus SI Figures S01–S06 from frozen supplied tables. Main Figure 5 is intentionally excluded because the structural panel is already finalized in the separate structural workstream.

## Output policy
- Final-use output: vector PDF.
- Fast-review output: PNG at 200 dpi.
- White background.
- PDF fonts are embedded as TrueType-compatible text where Matplotlib permits.
- Arial is requested first. If Arial is absent, the renderer falls back to Liberation Sans, Helvetica, then DejaVu Sans. The actually resolved font is written into every figure manifest.

## Typography
- Uppercase panel letters.
- Sentence-case panel titles and axis labels.
- No prose-heavy status cards.
- Unicode chemistry labels (CO₂, CH₄, H₂, N₂, Δ, ρ) are used where practical to reduce mixed math-font rendering.

## Semantic colors
- Linker-family change: deep blue.
- Metal substitution: vermillion/orange.
- Functional motif: muted purple and explicitly exploratory.
- Same-chemistry/control/background: graphite/gray.
- Energetic CO₂ accent: dark teal.
- RASPA full electrostatics: dark blue; charge-off counterpart: neutral gray.

## Main figure architecture
- Figure 1: matched-comparison design and support.
- Figure 2: chemistry above matched same-chemistry background, energetic association, and residual-geometry adjustment.
- Figure 3: guest/pressure dependence and high-pressure pre-combustion boundary.
- Figure 4: translation to working capacity/selectivity and selected process-aligned/discordant examples.
- Figure 5: not regenerated here; keep the finalized structural panel.
- Figure 6: RASPA selected-case validation replacing the old process-summary Figure 6.

## SI architecture
- S01: additional control scales and symmetric-design detail.
- S02: detailed HOA associations and pressure-change energetic associations.
- S03: detailed guest/pressure specificity.
- S04: robustness and measured-geometry sensitivity consolidated from the former audit-style main figure.
- S05: selected-case geometry-control proof; companion only to the already-finalized structural main panel.
- S06: full eight-pair RASPA detail; no density map.

## Scientific boundaries enforced by the plots
- Geometry matching is not described as true isostructural matching.
- Adjusted coefficients are sensitivity estimates, not direct/mediated causal effects.
- Guest/pressure plots show chemistry-associated separation, not raw uptake unless explicitly stated.
- Uptake agreement does not imply selectivity agreement.
- RASPA uses the supplied frozen closure tables and does not create new pair definitions.
- No RASPA density projection is generated.
