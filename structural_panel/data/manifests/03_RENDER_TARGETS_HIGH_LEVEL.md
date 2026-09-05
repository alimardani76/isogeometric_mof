# Structural render targets by panel

## Global rule
Keep endpoint i and ii at the same camera direction and approximately the same visual scale whenever crystallographically meaningful. Use a white or transparent background. Added text belongs in PowerPoint and should use Arial. Carbon should remain visually quiet; metals/heteroatoms should carry the chemical contrast. Insets answer **what chemistry changed?**, not **where adsorption occurs?**.

## A. Strong linker / process aligned
- **Endpoint i:** `DB0-m3_o11_o17_f0_pcu.sym.32` - Zn2H15C26N3O10 - topology pcu
- **Endpoint ii:** `DB0-m3_o12_o20_f0_pcu.sym.24` - ZnH2C8N3O8 - topology pcu
- **Whole-structure target:** Whole view: show the matched pcu pore/framework architecture with the organic environment clearly readable; endpoints must use the same crystallographic camera and matched scale.
- **Inset target:** Paired inset: zoom a linker-rich local region in both endpoints so the organic-environment difference is visible. Do not mark an adsorption atom/site.
- **Geometry-control QA:** maximum normalized difference/caliper = 0.897 (< 1 accepted).

## B. Strong metal / process aligned
- **Endpoint i:** `DB0-m3_o7_o7_f0_nbo.sym.48` - ZnH4C16(IO)4 - topology nbo
- **Endpoint ii:** `DB0-m2_o7_o7_f0_nbo.sym.45` - CuH4C16(IO)4 - topology nbo
- **Whole-structure target:** Whole view: show the matched nbo framework/pore architecture with the two structures at the same camera and scale.
- **Inset target:** Paired inset: use the same metal node and first coordination shell in both endpoints; label Zn and Cu clearly. This is the safest case for a local-coordination inset.
- **Geometry-control QA:** maximum normalized difference/caliper = 0.666 (< 1 accepted).

## C. Cu-Zn pressure exception
- **Endpoint i:** `DB0-m3_o6_o27_f0_nbo.sym.33` - Zn3H20C40(N2O3)4 - topology nbo
- **Endpoint ii:** `DB0-m2_o6_o27_f0_nbo.sym.30` - Cu3H20C40(N2O3)4 - topology nbo
- **Whole-structure target:** Whole view: show the matched nbo architecture at identical camera/scale; keep the structural similarity obvious.
- **Inset target:** Paired inset: show corresponding Zn/Cu node environments only as a boundary-case comparison. Add a small boundary/method-sensitive tag; do not claim a robust Cu-vs-Zn mechanism.
- **Geometry-control QA:** maximum normalized difference/caliper = 0.842 (< 1 accepted).

## D. Near-null linker comparator
- **Endpoint i:** `DB0-m2_o23_o28_f0_nbo.sym.21` - Cu3H40C58(NO8)2 - topology nbo
- **Endpoint ii:** `DB0-m2_o23_o28_f0_nbo.sym.4` - Cu3H38C57(NO8)2 - topology nbo
- **Whole-structure target:** Whole view: emphasize how closely the nbo pore architecture matches across endpoints; this should read visually as a strong control/near-null comparator.
- **Inset target:** Paired inset: show the linker-level difference only; label near-null comparator, never inactive/no effect.
- **Geometry-control QA:** maximum normalized difference/caliper = 0.147 (< 1 accepted).

## E. Process-discordant linker comparator
- **Endpoint i:** `DB0-m3_o440_o155_f0_fsc.sym.26` - ZnH9C23NO8 - topology fsc
- **Endpoint ii:** `DB0-m3_o152_o155_f0_fsc.sym.27` - ZnH10C24NO6 - topology fsc
- **Whole-structure target:** Whole view: show the matched fsc framework with same camera/scale and a readable organic-region contrast.
- **Inset target:** Paired inset: show the chemistry difference only. Do not invent a structural reason for the process discordance.
- **Geometry-control QA:** maximum normalized difference/caliper = 0.790 (< 1 accepted).

## F. Exploratory functional-motif example
- **Endpoint i:** `DB0-m9_o17_o27_f0_sra.sym.117` - V2H15C35(NO2)5 - topology sra
- **Endpoint ii:** `DB0-m9_o17_o27_f0_sra.sym.116` - V2H15C35(NO2)5 - topology sra
- **Whole-structure target:** Whole view: show the matched sra framework with same camera/scale; preserve the repeat motif clearly.
- **Inset target:** Paired inset: show the functional-motif difference while making the panel explicitly exploratory; no class-wide mechanistic language.
- **Geometry-control QA:** maximum normalized difference/caliper = 0.449 (< 1 accepted).
