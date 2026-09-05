# Panel D — Round-2 periodic/crop review

## Decision status

### D whole-view geometry/framing: **DONE**

Freeze:

```text
camera          = c_plus
projection      = orthographic
periodic buffer = 3×3×1
crop phase      = half-a
FOV factor      = 0.75
H               = hidden
pairwise bonds  = validated D rules
AO              = off
cell box        = off
```

`phase_half_b / 0.75` is numerically and visually almost identical because of the symmetry/translation
of this view, so `half-a` is chosen simply as the canonical reproducible phase.

## Why 0.75 wins

- `0.65`: too tight; important motifs are cut aggressively at the frame boundaries.
- `0.85`: clean but slightly too zoomed out for a six-panel figure.
- `0.75`: best balance of pore/network context and atom-level readability.

## Why half-a wins

- cleaner boundary placement than phase-00;
- balanced repetition of the large pores;
- no single local substituent dominates the whole image;
- D_i and D_ii remain visually extremely similar;
- half-b is effectively equivalent, so there is no reason to preserve both.

## Important status distinction

We are **not finished with Panel D as a whole**.

Finished:
- chemistry audit
- explicit connectivity
- whole-view camera
- periodic context
- crop/framing

Remaining:
- local ethyl↔methyl inset
- later high-resolution export with the other five panels

PowerPoint is still intentionally postponed until all six panels have one frozen whole view and one frozen inset.

---

# Next scientific task: D linker inset

The actual local difference is:

```text
D_i   backbone–CH2–CH3   (ethyl)
D_ii  backbone–CH3       (methyl)
```

The inset should make that subtle change visible without making the pair look dramatically different.

The Round-3 script:
- uses a 3×3×3 periodic buffer;
- finds a central ethyl motif in D_i and the corresponding methyl-type motif class in D_ii;
- extracts local heavy-atom neighborhoods only;
- fits the viewport to the local cluster;
- screens two context depths and four camera directions.

Run:

```bash
python 05_D_render_linker_inset_screen.py
```

Then send the generated contact-sheet pages from:

`OVITO_screening/22_D_linker_inset`
