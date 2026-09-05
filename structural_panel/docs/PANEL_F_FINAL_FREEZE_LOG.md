# Project 7B Structural Panel — Panel F Final Freeze Log

## Status
**Panel F is structurally frozen.**

The final inset-screen ZIP was reviewed in full:
- 14 individual inset PNGs
- 2 contact sheets
- 14 standalone XYZ fragments

The standalone fragments confirm that the selected local neighborhoods are being extracted correctly and without periodic-boundary bond artifacts.

---

## F whole structure — FINAL

**Scientific role:** exploratory functional-motif example  
**Topology:** sra

### Camera / periodic framing
- camera normal: `a`
- camera up: `c`
- projection: orthographic
- F_i replication: `1×5×5`
- F_ii replication: `1×5×5`
- final case: `PRIMARY_buffer_155_context`
- FOV factor: `1.08` relative to the original `1×2×2` reference
- review FOV: approximately `37.9707`
- H: hidden
- AO: off
- simulation-cell outline: off

### Controlled connectivity
- C–C ≤ 1.65 Å
- C–H ≤ 1.20 Å
- C–N ≤ 1.50 Å
- C–O ≤ 1.50 Å
- N–N ≤ 1.40 Å
- V–O ≤ 2.15 Å
- all unspecified pairs OFF
- V–V OFF

Each V center is represented as `V(O6)`.

---

## F local inset — FINAL

### Winner
`DIST_D3_face`

### What the selected local fragments contain
The inset is a graph-depth-3 neighborhood around the cyano motif.

- F_i local fragment: `C9N3` (12 heavy atoms)
- F_ii local fragment: `C11N1` (12 heavy atoms)

These are local crops from the larger cyano-bearing linker environments:

- F_i parent linker: `C17H7N5O4`
- F_ii parent linker: `C19H7N1O4`

### Why `DIST_D3_face` wins
- `DIST_D2_face` is too chemically minimal and looks generic.
- `DIST_D3_face` shows the cyano group plus enough surrounding linker chemistry to make the local-environment difference immediately legible.
- `DIST_D3_oblique` adds perspective but no useful chemistry and slightly reduces direct comparability.
- `DIST_FULL_*` are chemically complete but too large/complex for a small exploratory inset and visually push the panel toward a full-linker comparison rather than a functional-motif comparison.
- `SHARED_*` cases are controls, not the intended main inset.

### Interpretation boundary
Safe wording:
> Exploratory contrast in the local cyano-bearing linker environment.

Also acceptable:
> Exploratory difference in cyano-functional-motif placement among linker environments.

Do **not** claim:
> The cyano motif or its placement causes the adsorption/process response.

---

## Final-export note

At the final high-resolution stage:
- keep `DIST_D3_face`;
- preserve the same 12-heavy-atom graph depth for both endpoints;
- preserve matched physical scale;
- align the local fragments consistently in-plane;
- tighten the viewport so the local motif occupies roughly 55–70% of the inset region;
- do not add Zn/V anchors;
- do not switch to the full-linker render;
- keep the visual treatment quieter than Panels A/B because Panel F is explicitly exploratory.

---

## Structural-panel project status

- Panel A: whole + inset frozen
- Panel B: whole + inset frozen
- Panel D: whole + inset frozen
- Panel E: whole + inset frozen
- Panel F: whole + inset frozen
- Panel C: remaining final panel

After Panel C is frozen:
1. render all 12 final high-resolution structural assets;
2. assemble the six-panel composite in PowerPoint;
3. add A–F letters, i/ii endpoint labels, tiny descriptive subtitles, and any necessary callouts;
4. export the final composite.
