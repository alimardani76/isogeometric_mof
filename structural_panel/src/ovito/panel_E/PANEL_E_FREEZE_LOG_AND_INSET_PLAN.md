# Panel E — whole-view freeze + local-inset plan

## Whole structure: FROZEN

After reviewing the full Round-3 periodic/crop sheet, freeze:

```text
Panel            = E
Role             = process-discordant linker comparator
Topology         = fsc

Camera family    = P1_U2_up_b_to_a

E_i:
  view normal    = a
  camera up      = b
  periodic rep   = 1×4×4

E_ii:
  view normal    = c
  camera up      = a
  periodic rep   = 4×4×1

FOV factor       = 1.00 relative to the mapped P1 plane-22 reference
Projection       = orthographic
H                = hidden
AO               = off
cell outline     = off
```

This corresponds to the Round-3 image:

```text
BUFFER_144_ref
```

### Why BUFFER_144_ref wins

- `REF_plane22` is clean, but too finite and leaves too much unused white space.
- `BUFFER_144_tight` is unnecessarily tight and cuts more chemistry at the outer frame.
- `BUFFER_144_context` gives more periodic context but makes the chemistry smaller than needed for a six-panel figure.
- `BUFFER_133_mid` is visually dense and crops major motifs too aggressively.
- `BUFFER_144_ref` is the best compromise: enough periodic context, readable node/linker chemistry, and a stable matched scaffold impression.

Do not reopen the E whole-view camera/replication search.

---

# Local inset: next and final E task

Panel E must remain descriptive.

Allowed message:

> Same broad fsc scaffold; visible local organic-chemistry contrast; process behavior is discordant.

Not allowed:

> This local motif causes the process discordance.

The corrected E bond graph contains two Zn-connected organic-component families in each endpoint:

## N-containing family
E_i:
```text
C28 H12 N2 O8
```

E_ii:
```text
C26 H12 N2 O4
```

This family preserves N2 but changes carbon and, especially, oxygen decoration.

## N-free / O8 family
E_i:
```text
C18 H6 O8
```

E_ii:
```text
C22 H8 O8
```

This family preserves O8 but changes carbon-backbone size.

Both are scientifically defensible descriptive contrasts.

Round 4 screens both once using the robust standalone-fragment workflow learned from Panel A:
1. identify the exact linker component in the original corrected CIF graph;
2. unwrap it using bond PBC vectors;
3. optionally add its Zn anchors;
4. write a standalone non-periodic XYZ fragment;
5. recreate only local Euclidean bonds;
6. render face-on / mild-oblique candidates at matched scale.

After choosing one inset, Panel E is structurally frozen.
