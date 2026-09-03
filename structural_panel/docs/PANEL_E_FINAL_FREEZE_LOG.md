# Project 7B Structural Panel — Panel E Final Freeze Log

## Status
**Panel E is structurally frozen.**

The uploaded `43_E_linker_inset.zip` was reviewed in full:
- 12 individual inset renders
- 2 contact sheets
- 12 standalone XYZ fragments

The standalone fragments have the expected compositions, confirming that the extraction step is behaving correctly.

---

## E whole structure — FINAL

**Scientific role:** process-discordant linker comparator  
**Topology:** fsc

### Camera / periodic framing
- camera family: `P1_U2_up_b_to_a`
- E_i view normal: `a`
- E_i camera up: `b`
- E_ii view normal: `c`
- E_ii camera up: `a`
- E_i periodic context: `1×4×4`
- E_ii periodic context: `4×4×1`
- final framing case: `BUFFER_144_ref`
- FOV factor: `1.00`
- projection: orthographic
- H: hidden
- AO: off
- simulation-cell outline: off

### Controlled connectivity
- C–C ≤ 1.60 Å
- C–H ≤ 1.20 Å
- C–N ≤ 1.50 Å
- C–O ≤ 1.50 Å
- O–H ≤ 1.10 Å
- Zn–O ≤ 2.20 Å
- Zn–N ≤ 1.90 Å
- all unspecified pairs OFF
- Zn–Zn OFF

---

## E local inset — FINAL

### Winner
`Nfam_face`

### Exact descriptive comparison
- E_i: `C28H12N2O8`
- E_ii: `C26H12N2O4`

### Why this inset wins
- It gives the most direct chemistry comparison.
- Both fragments retain the same N2 motif class.
- The large O-content change is immediately visible.
- It avoids adding Zn nodes that could visually push the panel toward an unintended metal/mechanistic interpretation.
- Face-on presentation is cleaner and more diagnostic than the oblique option.

### Rejected as main inset
- `Nfam_oblique`: valid but no scientific advantage over face-on.
- `Nfam_plusZn_face`: valid, but Zn anchors shift the visual story toward coordination/metal context.
- `Ofam_*`: valid backup chemistry, but the principal contrast is mostly carbon-backbone size and is less immediately interpretable than the N-family oxygen-decoration contrast.

### Important interpretation boundary
The inset is **descriptive only**.

Allowed wording:
> Matched fsc framework with a local organic-chemistry contrast.

Do not claim:
> The selected linker motif causes or explains the process discordance.

---

## Final-export note

The review insets are intentionally small in the 1200×900 screening canvas.

At the final high-resolution rendering stage:
- keep the same selected `Nfam_face` geometry;
- keep the same matched physical scale between E_i and E_ii;
- align the in-plane PCA major axis consistently between the two fragments;
- tighten the viewport so the molecular fragment occupies roughly 55–70% of the inset width/height;
- do **not** change the chemistry selection or choose a different inset.

This is a production/framing adjustment, not another scientific-selection round.

---

## Project status

- Panel A: whole + inset frozen
- Panel B: whole + inset frozen
- Panel D: whole + inset frozen
- Panel E: whole + inset frozen
- Panel F: next
- Panel C: last

After F and C:
1. generate the 12 final high-resolution structural assets;
2. assemble all six panels in PowerPoint;
3. add panel letters, labels, callouts, and final layout.
