# Panel A — freeze status after corrected whole-view review

## Whole structure: FROZEN

Use this for the later high-resolution rerender:

```text
Panel            = A
Scientific role  = strong linker / process aligned
Topology         = pcu

Mapped family:
A_i view         = along a
A_ii view        = along c

Periodic context:
A_i replication = 1×5×5
A_ii replication= 5×5×1

Framing:
phase            = 00
FOV factor       = 0.88 relative to mapped M1 reference

Projection       = orthographic
H                = hidden
AO               = off
cell outline     = off

Connectivity:
C-C   <= 1.70 Å
C-H   <= 1.20 Å
C-N   <= 1.50 Å
C-O   <= 1.50 Å
N-H   <= 1.10 Å
N-O   <= 1.45 Å
O-H   <= 1.10 Å
Zn-O  <= 2.30 Å
Zn-N  <= 2.20 Å
all unspecified pairs OFF
```

### Why 0.88, not 0.82
The corrected 0.82 periodic-buffer images are too tight and cut important top/bottom framework motifs.
The 0.88 render preserves the strong mapped-pcu comparison while keeping the chemistry large enough
for a six-panel figure.

### Why M1, not M3
M1 reads as a framework/pore network. M3 is valid crystallographically but too sparse/ladder-like.

---

# Inset status: NOT YET FROZEN

The previous inset images are still invalid because:
- periodic bonds retained non-zero PBC display vectors after coordinate unwrapping;
- this generated very long gray lines;
- the A_i nitro component was also not reliably selected in the replicated-cell approach.

Round 6 fixes this by:
1. identifying the target linker in the original corrected 1×1×1 bond graph;
2. unwrapping that linker exactly with bond PBC vectors;
3. exporting the selected local cluster as a standalone non-periodic XYZ fragment;
4. re-importing the fragment into OVITO;
5. recreating only local Euclidean bonds;
6. fitting the camera to the fragment itself.

This should be the last A inset round.
