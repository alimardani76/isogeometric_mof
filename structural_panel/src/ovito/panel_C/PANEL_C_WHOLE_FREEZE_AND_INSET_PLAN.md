# Panel C — Whole-view freeze + final cautious local-inset plan

## Whole structure: FROZEN

After reviewing the complete `61_C_periodic_refine` round, freeze:

```text
Panel            = C
Scientific role  = Cu/Zn boundary / original pressure-exception case
Topology         = nbo

Camera normal    = c
Camera up        = b
Projection       = orthographic

Periodic context:
C_i (Zn)         = 4×4×1
C_ii (Cu)        = 4×4×1

Framing:
case             = BUFFER_441_ref
FOV factor       = 1.00 relative to the 2×2×1 reference

H                = hidden
AO               = off
cell outline     = off
```

### Why `BUFFER_441_ref` wins

- `CONTROL_221` is too finite and leaves obvious fragment-like boundary pieces.
- `BUFFER_331_ref` improves periodicity but still has a stronger finite-window impression.
- `BUFFER_441_tight` is too crowded and visually aggressive.
- `BUFFER_441_context` gives more breathing room but makes the chemistry smaller than necessary and
  introduces less efficient use of the panel area.
- `BUFFER_551_ref` is visually essentially the same as `BUFFER_441_ref`, so the larger atom count adds
  no publication value.
- `BUFFER_441_ref` gives the best balance of periodic context, matched global nbo architecture, readable
  metal identity, and figure-space efficiency.

Do not reopen the C whole-view search.

---

# Final C inset — interpretation boundary

Panel C is the one panel where the local view must be **deliberately more cautious than Panel B**.

The project-level structural audit says:
- all eight method-sensitive selected metal sites occur in this Cu/Zn boundary pair;
- the independent 298 K CO2 RASPA validation did not reproduce the original pressure-dependence.

Therefore the inset may show a corresponding Zn/Cu local region, but it must not imply:
- robust coordination certainty;
- a unique adsorption site;
- a validated pressure-effect mechanism.

The local shell used here is explicitly a **distance-defined rendering shell**.

For the corresponding first metal site in the two CIFs:

## C_i — Zn
four nearest O:
```text
~2.024–2.029 Å
```

## C_ii — Cu
four nearest O:
```text
~1.951–1.956 Å
```

There is a large gap to the next O shell.

This makes the nearest O4 set visually clean, but the scientific label remains:

> distance-defined local comparison

not:

> robust O4 coordination mechanism

---

# Final inset screen

The script identifies the corresponding `M1`-like metal site geometrically and renders three nested
descriptive contexts:

## CORE
```text
M + four nearest O
```

Very conservative, but may be too abstract.

## CARBOXY
```text
M + four nearest O
+ their four carboxylate C atoms
+ the companion O on each carboxylate
```

This shows the local carboxylate node geometry without becoming a large linker image.

## LINKER1
```text
CARBOXY
+ the first carbon beyond each carboxylate C
```

This adds one small amount of organic context.

Each is tested face-on and mild-oblique.

No polyhedra.
No coordination-number annotation.
No adsorption-site marker.

Run only:

```bash
python 06_C_render_boundary_inset_screen.py
```

Send:

`OVITO_screening/62_C_boundary_inset/contact_sheets`

After choosing one inset, **all six structural panels are scientifically frozen**.
