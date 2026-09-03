# Project 7B — Final Structural-Panel Freeze Log

## Status

**Scientific selection is complete for all six panels.**

All 12 structural assets are now frozen at the decision level:

- 6 whole-structure views
- 6 local inset views

What remains is **production only**:
1. high-resolution rerendering of the 12 frozen assets;
2. consistent final cropping / scale cleanup;
3. PowerPoint assembly;
4. panel letters, i/ii endpoint labels, concise subtitles/callouts;
5. final export.

No panel should return to broad camera or chemistry screening unless a true rendering bug is discovered.

---

# Panel A — strong linker / process aligned

## Whole — FINAL
- mapped M1 family
- A_i view: `a`
- A_ii view: `c`
- A_i periodic context: `1×5×5`
- A_ii periodic context: `5×5×1`
- phase: `00`
- FOV factor: `0.88`
- orthographic
- H hidden
- AO off
- cell box off
- final corrected Zn–O + Zn–N connectivity retained

## Inset — FINAL
- `NITRO_plusZn_face`
- A_i target: `C6N1O6 + 2 Zn anchors`
- A_ii target: `C6N4O12 + 2 Zn anchors`
- face-on
- matched physical scale

---

# Panel B — strong metal / process aligned

## Whole — FINAL
- `c_plus`
- periodic context: `3×3×1`
- phase: `phase_00`
- FOV factor: `0.96`
- B04 balanced style
- orthographic
- H hidden
- AO off
- cell box off

## Inset — FINAL
- `D2_ab_plus`
- metal-node comparison
- frozen B local extraction / camera settings

---

# Panel C — Cu/Zn boundary / original pressure-exception case

## Whole — FINAL
- view normal: `c`
- camera up: `b`
- C_i (Zn) periodic context: `4×4×1`
- C_ii (Cu) periodic context: `4×4×1`
- final case: `BUFFER_441_ref`
- FOV factor: `1.00`
- orthographic
- H hidden
- AO off
- cell box off

## Inset — FINAL
### Winner: `CARBOXY_face`

Local standalone fragment:
- C_i: `Zn1 C4 O8` = 13 heavy atoms
- C_ii: `Cu1 C4 O8` = 13 heavy atoms

The four metal-bound O atoms are the distance-defined nearest shell:
- Zn–O: approximately `2.024–2.029 Å`
- Cu–O: approximately `1.951–1.956 Å`

The four companion O atoms and four carboxylate C atoms give enough local chemical context without turning the inset into a full-linker or mechanistic picture.

### Interpretation boundary
Use:
- `Cu/Zn boundary case`
- `method-sensitive local comparison`
- `distance-defined local view`

Do **not** use:
- `robust coordination`
- `active site`
- `adsorption site`
- `validated pressure-effect mechanism`

---

# Panel D — near-null linker comparator

## Whole — FINAL
- `c_plus`
- periodic context: `3×3×1`
- phase: `half-a`
- FOV factor: `0.75`
- orthographic
- H hidden
- AO off
- cell box off

## Inset — FINAL
- `CTX2_ac_mixed`
- D_i: ethyl-like `backbone–CH2–CH3`
- D_ii: methyl-like `backbone–CH3`
- matched local context

---

# Panel E — process-discordant linker comparator

## Whole — FINAL
- camera family: `P1_U2_up_b_to_a`
- E_i view: `a`, camera up: `b`
- E_ii view: `c`, camera up: `a`
- E_i periodic context: `1×4×4`
- E_ii periodic context: `4×4×1`
- final case: `BUFFER_144_ref`
- FOV factor: `1.00`
- orthographic
- H hidden
- AO off
- cell box off

## Inset — FINAL
- `Nfam_face`
- E_i: `C28H12N2O8`
- E_ii: `C26H12N2O4`
- Zn anchors hidden
- face-on
- descriptive chemistry contrast only

Do not imply the chosen local motif explains the process discordance.

---

# Panel F — exploratory functional-motif example

## Whole — FINAL
- view normal: `a`
- camera up: `c`
- F_i periodic context: `1×5×5`
- F_ii periodic context: `1×5×5`
- final case: `PRIMARY_buffer_155_context`
- FOV factor: `1.08`
- orthographic
- H hidden
- AO off
- cell box off

## Inset — FINAL
- `DIST_D3_face`
- graph-depth-3 cyano-bearing local environment
- F_i local crop: `C9N3`
- F_ii local crop: `C11N1`
- both 12 heavy atoms
- face-on
- matched physical scale

Interpret as an **exploratory local cyano-bearing linker-environment contrast**, not a causal mechanism.

---

# Final production rules for all 12 assets

## Whole structures
- keep every frozen camera / roll / replication / FOV decision;
- do not reopen broad geometry searches;
- rerender at publication resolution;
- preserve matched physical scale inside each i/ii pair;
- white background;
- orthographic projection;
- H hidden;
- AO off unless a later production-only test proves essential;
- no simulation-cell outline;
- no accidental PBC fragment artifacts;
- use the frozen atom palette consistently.

## Insets
- keep the frozen chemistry selection exactly;
- keep matched scale within each pair;
- tighten the viewport so the local object uses roughly 55–70% of the inset area;
- align paired fragments consistently in-plane where possible;
- no new chemistry selection;
- no polyhedra unless already scientifically frozen (none required here);
- keep Panel C and Panel F visually quieter than Panels A/B.

---

# Final project sequence

## Stage 1 — COMPLETE
Scientific selection of:
- A whole + inset
- B whole + inset
- C whole + inset
- D whole + inset
- E whole + inset
- F whole + inset

## Stage 2 — NEXT
Generate the **12 final high-resolution renders** from the frozen settings.

## Stage 3
Assemble the six-panel figure in PowerPoint:
- A–F panel letters
- i / ii endpoint labels
- concise topology / role subtitles
- inset placement
- small arrows/callouts only where useful
- consistent spacing and scale

## Stage 4
Final export and manuscript integration.
