# Panel F — Whole-view freeze and final inset plan

## Whole structure: FROZEN

After reviewing the complete `51_F_repeat_refine` round, freeze:

```text
Panel            = F
Scientific role  = exploratory functional-motif example
Topology         = sra

Camera normal    = a
Camera up        = c
Projection       = orthographic

Periodic context:
F_i              = 1×5×5
F_ii             = 1×5×5

Framing:
case             = PRIMARY_buffer_155_context
FOV factor       = 1.08 relative to the original 1×2×2 reference
absolute review FOV ≈ 37.9707

H                = hidden
AO               = off
cell outline     = off
```

### Why `PRIMARY_buffer_155_context` wins

- `PRIMARY_control_122` is too finite; the structure reads as a clipped patch.
- `PRIMARY_buffer_133_ref` still shows obvious truncated side nodes/linkers.
- `PRIMARY_buffer_155_ref` is scientifically clean but visually too dense and crowded for a six-panel composite.
- `PRIMARY_buffer_155_tight` is too aggressive.
- `PRIMARY_buffer_155_context` keeps the same winning sra camera, removes the finite-supercell impression, and gives the repeated framework enough breathing room.
- the `up=b` backups are valid but more diagonal/energetic and less calm than the primary `up=c` roll.

Do not reopen the F whole-view search.

---

# Final inset task

The validated F graph contains two cyano/nitrile motifs in each endpoint.

The scientifically interesting difference is **where the cyano motif sits among linker environments**:

## F_i
Both cyano motifs occur on the N-rich linker class:

```text
C17H7N5O4
C17H7N5O4
```

## F_ii
One remains on the same N-rich class:

```text
C17H7N5O4
```

while the second occurs on a much less N-rich carbonaceous linker environment:

```text
C19H7N1O4
```

The final inset must remain explicitly exploratory.

Safe interpretation:
> exploratory difference in cyano-functional-motif placement / linker environment.

Do not claim:
> cyano placement causes the adsorption response.

---

# Round-3 inset strategy

The final screen uses the robust standalone-fragment method learned from Panels A/E:

1. identify the cyano motif from the validated original CIF bond graph;
2. identify the organic component containing that cyano motif;
3. choose:
   - F_i: one `C17H7N5O4` cyano-bearing linker;
   - F_ii: the distinctive `C19H7N1O4` cyano-bearing linker;
4. unwrap the selected graph across periodic boundaries;
5. export a standalone non-periodic XYZ fragment;
6. recreate only local Euclidean bonds;
7. render matched-scale face-on / oblique candidates.

The screen includes:
- local depth-2 neighborhood;
- local depth-3 neighborhood;
- full cyano-bearing linker;
- one shared-environment control showing `C17H7N5O4` in both endpoints.

The control is for scientific sanity checking; it is not expected to be the final inset.

Run only:

```bash
python 06_F_render_cyano_inset_screen.py
```

Send:
`OVITO_screening/52_F_cyano_inset/contact_sheets`

After selecting one inset, Panel F is structurally frozen.
