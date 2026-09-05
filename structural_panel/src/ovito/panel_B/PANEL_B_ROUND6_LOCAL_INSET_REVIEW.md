# Panel B — Local inset round review and technical correction

## Files reviewed

The uploaded `08_B_local_inset.zip` contains:

- 12 individual local renders
- 2 contact-sheet pages

Candidates:
- `D1_a_plus`
- `D2_a_plus`
- `D2_ab_plus`
- `D2_abc_plus`
- `D2_abc_plus_AO`
- `D3_a_plus`

for both Zn and Cu endpoints.

---

# 1. What the current renders tell us

## D1_a_plus
Chemically clean and easy to interpret:
- metal center
- four first-shell O atoms

But it is too abstract for the final inset by itself. It looks like an isolated coordination cross and
does not preserve enough framework context.

Use only as a reference/control.

## D2_a_plus
Scientifically the strongest concept in the current batch:
- M + O4
- first carbon beyond each O

This is likely close to the final inset depth.

However, in a face-on projection the carbon atoms partially hide behind the O atoms, so it does not
yet use the local chemical context efficiently.

## D3_a_plus
Readable and compact, with enough extra carbon connectivity to show framework attachment.

This is the best *current visible* candidate, but it may be slightly more context than needed.

## D2_ab_plus / D2_abc_plus / D2_abc_plus_AO
Do NOT judge these images as scientific candidates yet.

The distant gray carbon atoms are a rendering artifact: the graph-neighborhood selection retained
atoms connected through periodic boundaries, but the selected atoms remained in their wrapped unit-cell
coordinates. In oblique views this appears as detached atoms far from the metal site.

The AO version repeats the same geometric problem; AO is not the cause.

---

# 2. Second technical issue

Every local object occupies only a small part of the 1200×900 frame.

The old local-inset script used the normal `zoom_all()` workflow, which is influenced by the large
simulation cell even after most particles are deleted.

For the inset, the camera should fit the **selected local cluster**, not the crystallographic cell.

---

# 3. Correct fix

Version 8 changes the inset logic in two ways:

1. Build a **3×3×3 periodic buffer** and select a metal site near the center of that buffer.
   This keeps the local bonded neighborhood physically contiguous and avoids wrapped/detached atoms.

2. Use a **particle-content camera fit** based on the radius of the retained local cluster.
   The local chemistry now fills the image instead of occupying a tiny central area.

This does not change the crystal structure or bonding rules. It only fixes the periodic representation
and viewport framing of the extracted local neighborhood.

---

# 4. What should be screened again

The corrected v8 script renders:

- Depth 1 / a_plus
- Depth 2 / a_plus
- Depth 2 / ab_plus
- Depth 2 / abc_plus
- Depth 2 / abc_plus + AO
- Depth 3 / a_plus
- Depth 3 / ab_plus
- Depth 3 / abc_plus

Current expectation:
- Depth 1 = too little context
- Depth 2 = likely best scientific balance
- Depth 3 = useful backup if Depth 2 remains too abstract
- mild oblique Depth 2 may become the final winner once the PBC artifact is removed

---

# 5. Scientific interpretation remains constrained

The inset is a structural comparison only.

Allowed:
- Zn vs Cu label
- first O coordination shell
- optional descriptive M–O distance later in PowerPoint

Not allowed:
- adsorption-site label
- causal mechanism claim
- oxidation-state inference from the rendering
- claim that the local geometry alone explains the adsorption/process contrast

---

# 6. Next action

Run:

```bash
python 13_render_B_local_inset_fixed.py
```

Then send the generated contact-sheet pages from:

`OVITO_screening/10_B_local_inset_fixed`

Do not use the old oblique inset images in the manuscript.
