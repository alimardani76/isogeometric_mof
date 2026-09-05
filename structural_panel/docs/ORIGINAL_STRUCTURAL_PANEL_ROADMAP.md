# Project 7B Structural Panel Roadmap  
**VESTA + PowerPoint manual for 6 panels / 12 CIFs**

## 0. Purpose of this document

This is the working manual for building the **new structural Figure 05 / structural panel** for Project 7B using **VESTA** and **PowerPoint**.

This figure should be treated as a **paired structural audit**: it shows **matched quasi-isostructural pairs under geometry control**, and it helps the reader visually understand what changed between the two endpoints in each case. It is **not** an adsorption-site figure and **not** a mechanistic simulation figure. That same “post-hoc visualization, not mechanistic proof” discipline is explicitly important in the reference structural-audit style we discussed. 
The goal is to make a figure that is:

1. **scientifically faithful**,  
2. **visually strong**,  
3. **consistent across six panels**, and  
4. **easy to assemble in PowerPoint**.

---

# 1. The six panels and the 12 CIFs

## 1.1 Panel map

| Panel | Role | Topology | Endpoint i | Endpoint ii |
|---|---|---|---|---|
| **A** | Strong linker / process aligned | pcu | `DB0-m3_o11_o17_f0_pcu.sym.32` | `DB0-m3_o12_o20_f0_pcu.sym.24` |
| **B** | Strong metal / process aligned | nbo | `DB0-m3_o7_o7_f0_nbo.sym.48` | `DB0-m2_o7_o7_f0_nbo.sym.45` |
| **C** | Cu–Zn pressure exception | nbo | `DB0-m3_o6_o27_f0_nbo.sym.33` | `DB0-m2_o6_o27_f0_nbo.sym.30` |
| **D** | Near-null linker comparator | nbo | `DB0-m2_o23_o28_f0_nbo.sym.21` | `DB0-m2_o23_o28_f0_nbo.sym.4` |
| **E** | Process-discordant linker comparator | fsc | `DB0-m3_o440_o155_f0_fsc.sym.26` | `DB0-m3_o152_o155_f0_fsc.sym.27` |
| **F** | Exploratory functional-motif example | sra | `DB0-m9_o17_o27_f0_sra.sym.117` | `DB0-m9_o17_o27_f0_sra.sym.116` |

---

## 1.2 The values you should keep in mind while drawing

These numbers are not necessarily all shown in the final figure, but they should guide **how you treat** each panel.

| Panel | Main contrast | Median \|Δlog adsorption\| | WC concordance | Selectivity concordance | Max geometry fraction of caliper | Special note |
|---|---:|---:|---:|---:|---:|---|
| **A** | Linker-family contrast | 0.8119 | 1.00 | 1.00 | 0.897 | very strong chemistry/process-aligned linker case |
| **B** | Metal identity contrast | 0.3067 | 1.00 | 1.00 | 0.666 | safest robust local metal-node inset |
| **C** | Metal identity boundary case | 0.0820 | 1.00 | 1.00 | 0.842 | **method-sensitive** local chemistry, do not overclaim |
| **D** | Near-null linker contrast | 0.0125 | 1.00 | 0.75 | 0.147 | strongest visual control / near-null comparator |
| **E** | Process-discordant linker contrast | 0.0641 | 0.20 | 0.25 | 0.790 | show chemistry difference only, no invented mechanism |
| **F** | Exploratory motif contrast | 0.0596 | 0.80 | 1.00 | 0.449 | explicitly exploratory |

---

# 2. What you are trying to show in every panel

Each panel must answer **two different questions**:

## 2.1 Whole-structure image answers:
**“Do these two endpoints really share the same global framework / pore architecture?”**

So in the whole view, you are seeking:

- same overall scaffold,
- same topology character,
- same or very close pore/channel/cage impression,
- visually fair comparison,
- same camera and same scale.

## 2.2 Inset answers:
**“What chemistry changed locally?”**

So in the inset, you are seeking:

- linker difference, or
- metal-node difference, or
- functional-motif difference,

**without claiming adsorption mechanism**.

### Golden rule
- **Whole view = global sameness / geometric control**
- **Inset = local chemical contrast**

That is the main logic of the entire figure.

---

# 3. What not to do

## 3.1 Do not use the figure to claim:
- a specific adsorption site,
- “this atom is the reason for the performance,”
- oxidation state inferred from the picture,
- charge transfer inferred from the picture,
- a robust Cu-vs-Zn mechanism for **panel C**,
- “inactive” or “no effect” for **panel D**,
- a structural reason for process discordance in **panel E**,
- a class-wide conclusion from **panel F**.

## 3.2 Practical consequence
That means:

- do **not** put arrows saying “CO₂ binds here”,
- do **not** circle one atom and call it “active site”,
- do **not** draw polyhedra in panel C if that visually implies false certainty,
- do **not** overload the panel with too many labels.

---

# 4. Final figure grammar you should build

For **every** panel A–F, use the same internal structure:

```text
Panel label + role
small subtitle (topology / short meaning)

whole endpoint i    whole endpoint ii
      ↓                    ↓
     paired local inset / local comparison
      ↓
tiny footer with 1–2 evidence cues
```

## Recommended content layout per panel
- **Top line:** panel letter + short role
- **Middle:** two whole-structure renders, side by side
- **Lower-right or lower-center:** paired inset
- **Bottom mini-footer:** one compact note (for example `pcu · geometry-controlled`, or `boundary case`, or `exploratory`)

---

# 5. One-time VESTA setup rules

This section is the common setup for all 12 CIFs.

## 5.1 Before opening anything
Create a folder for exports, for example:

```text
Figure05_work/
  A/
  B/
  C/
  D/
  E/
  F/
```

Inside each panel folder, save:

- `whole_i.png`
- `whole_ii.png`
- `inset_i.png`
- `inset_ii.png`
- optional backups:
  - `whole_i_alt.png`
  - `whole_ii_alt.png`
  - `inset_i_alt.png`
  - `inset_ii_alt.png`

---

## 5.2 Common visual settings in VESTA

Use these principles consistently:

### Background
- White background is safest.
- Transparent background is also acceptable if your PowerPoint workflow handles it cleanly.

### Style
- Prefer **ball-and-stick** or a restrained stick style.
- Do **not** use extremely thick atoms/bonds.
- The framework must remain readable.

### Atoms
- Keep **carbon visually quiet**.
- Let **metals and heteroatoms** carry the contrast.
- Hydrogen can be:
  - hidden in **whole views** if cluttered,
  - optionally shown in **insets** only if it genuinely helps the motif.

### Bonds
- Keep bonds visible enough to read connectivity.
- Avoid overly thick bonds.

### Unit-cell / boundary
- Start from the basic cell.
- If the framework looks cut off or unreadable, expand boundaries just enough to make the structure intelligible.
- Do not over-expand until the panel becomes spaghetti.

### Projection
- Prefer a **non-distorting** view.
- If available, keep projection visually neutral rather than dramatic/perspective-heavy.

### Labels
- Do **not** place final text labels inside VESTA unless absolutely necessary.
- Add labels later in PowerPoint, in **Arial**.

---

# 6. The camera-selection algorithm you should use for every pair

This is the most important part of the workflow.

## 6.1 Start with endpoint i
For each pair, open **endpoint i first**.

Test at least these candidate views:

- View 1: approximately along **a**
- View 2: approximately along **b**
- View 3: approximately along **c**
- View 4: one **oblique** view, only if the axis-aligned views are poor

## 6.2 Score each candidate view using 4 questions

For every candidate view, ask:

### Q1. Is the global framework readable?
- Can I see the scaffold clearly?
- Can I visually understand the pore/window/cage/network?

### Q2. Does this view support pair comparison?
- Will the same camera likely work for endpoint ii?
- Does this orientation emphasize structural sameness rather than random visual difference?

### Q3. Does the view give a good inset source?
- Is there a local region I can crop later?
- Can I identify a linker region, node region, or motif region worth enlarging?

### Q4. Is the view clean?
- Low overlap?
- Not too crowded?
- Not too flat / not too collapsed?

## 6.3 Choose the best whole-view camera
Pick the candidate that best satisfies all 4 questions.

Then:

- **freeze that camera**
- apply it to endpoint ii
- keep **same zoom** or as close as possible
- export both whole-structure images

## 6.4 Only after freezing the whole view, move to the inset
Do **not** start from the inset first.

Whole view comes first because the whole pair must be visually matched.

---

# 7. How to decide if a whole-structure view is good or bad

## Good whole-structure view
A good whole view does the following:

- makes the topology readable,
- makes the global framework look controlled/matched,
- leaves enough empty space around the structure,
- does not excessively overlap bonds/atoms,
- can be repeated for the paired endpoint.

## Bad whole-structure view
Reject the view if:

- it looks like a random blob,
- the structure is too edge-on and flattened,
- the pore architecture is invisible,
- the paired endpoint looks too different only because of camera distortion,
- it is pretty but scientifically unhelpful.

---

# 8. How to decide if an inset is good or bad

## Good inset
A good inset:

- isolates the **changed local chemistry**,
- is still connected enough to make chemical sense,
- is readable at small size,
- does not rely on a mechanistic claim,
- can be mirrored between endpoint i and ii.

## Bad inset
Reject the inset if:

- it is too zoomed-in to understand context,
- it is too zoomed-out and shows nothing specific,
- it highlights a site that is not actually the intended contrast,
- it implies adsorption or catalysis without evidence,
- it cannot be reproduced comparably between both endpoints.

---

# 9. PowerPoint assembly rules

## 9.1 General
Use PowerPoint only for:

- layout,
- labels,
- connectors,
- panel letters,
- subtle boxes,
- final scaling.

## 9.2 Typography
- **Arial**
- clean, readable
- not too small

## 9.3 Panel construction
For each panel:

1. place whole endpoint i on the left,
2. place whole endpoint ii on the right,
3. place paired inset below or at the lower side,
4. add a tiny role/interpretation label,
5. add panel letter in uppercase: **A, B, C, D, E, F**.

## 9.4 Connectors
If you use connector lines from the whole view to the inset:

- keep them thin,
- neutral color,
- avoid dramatic arrows,
- use them only if they improve readability.

## 9.5 What text should appear inside the panel
Keep it minimal. Good examples:

- `pcu · linker contrast`
- `nbo · Zn/Cu node comparison`
- `boundary case`
- `near-null comparator`
- `process-discordant`
- `exploratory`

Do **not** place large paragraphs inside the panel.

---

# 10. Panel-by-panel roadmap

---

## PANEL A — Strong linker / process aligned  
**Pair:**  
- **A_i:** `DB0-m3_o11_o17_f0_pcu.sym.32`  
- **A_ii:** `DB0-m3_o12_o20_f0_pcu.sym.24`  
**Topology:** pcu  
**Scientific role:** strong linker-family contrast under good geometric control  
**Key numbers:**  
- median \|Δlog adsorption\| = **0.8119**
- WC concordance = **1.00**
- selectivity concordance = **1.00**
- max geometry fraction of caliper = **0.897**

### 10.A.1 What you are seeking
This panel should say:

> The pair is globally matched, but the local **linker / organic environment** is clearly different, and the adsorption/process contrast is strong.

### 10.A.2 What to seek in the whole structure
Seek:
- the **pcu framework character**,
- a clear pore/window or open framework impression,
- a view where the organic skeleton is readable,
- a view that can be copied to endpoint ii.

### 10.A.3 What to avoid in the whole structure
Avoid:
- a view that hides the pore opening,
- a view where only one linker fragment is visible,
- too much overlap from periodic repetition,
- a view that makes the two endpoints look less matched than they are.

### 10.A.4 Whole-structure VESTA workflow
1. Open **A_i**.
2. Test the three principal orientations.
3. Ask: which view best shows an **open pcu scaffold**?
4. Keep the one where:
   - the pore/window reads clearly,
   - the framework is centered,
   - the structure is not visually compressed.
5. Freeze that camera.
6. Open **A_ii**.
7. apply the same camera and comparable zoom.
8. Export `whole_i.png` and `whole_ii.png`.

### 10.A.5 What to seek in the inset
Seek:
- a **linker-rich local region**,
- a region where the organic environment difference is visually obvious,
- enough local context to understand how the linker sits in the framework.

### 10.A.6 What to avoid in the inset
Avoid:
- zooming into a single atom,
- implying the linker fragment is an adsorption site,
- choosing a region that does not visibly differ between endpoints.

### 10.A.7 Inset VESTA workflow
1. Use the whole-view camera as reference.
2. Rotate only as much as needed to isolate the chosen local region.
3. Crop a local fragment that clearly shows the organic/linker environment.
4. Export one local inset for **A_i** and the corresponding local inset for **A_ii**.
5. In PowerPoint, place them side by side as a **paired inset**.

### 10.A.8 Final reading test for panel A
If the panel works, the reader should immediately understand:

- same global framework,
- different linker environment,
- this is a strong chemistry/process-aligned case.

### 10.A.9 Suggested tiny footer
- `pcu · strong linker contrast`
- or `geometry-controlled · linker-rich inset`

---

## PANEL B — Strong metal / process aligned  
**Pair:**  
- **B_i:** `DB0-m3_o7_o7_f0_nbo.sym.48`  
- **B_ii:** `DB0-m2_o7_o7_f0_nbo.sym.45`  
**Topology:** nbo  
**Scientific role:** strong metal identity contrast  
**Key numbers:**  
- median \|Δlog adsorption\| = **0.3067**
- WC concordance = **1.00**
- selectivity concordance = **1.00**
- max geometry fraction of caliper = **0.666**
- local chemistry audit status: **robust metal local chemistry**

### 10.B.1 What you are seeking
This panel should say:

> The scaffold is matched, but the metal-node identity differs in a way that is appropriate to show locally.

This is the **best panel for a metal-node inset**.

### 10.B.2 What to seek in the whole structure
Seek:
- a clean **nbo** architecture view,
- a view that makes global similarity obvious,
- a view that leaves room for a metal-node story in the inset.

### 10.B.3 Whole-structure workflow
1. Open **B_i**.
2. Test three axis-based views.
3. Choose the view where:
   - the nbo scaffold is readable,
   - the framework is not overcrowded,
   - the paired endpoint will look nearly identical globally.
4. Apply same camera to **B_ii**.
5. Export both whole views.

### 10.B.4 What to seek in the inset
Seek:
- the **same metal node and first coordination shell** in both structures,
- a local crop where the node is central and readable,
- enough surrounding atoms to understand coordination.

### 10.B.5 What to label
This is one of the few places where explicit local labels are helpful:
- `Zn node`
- `Cu node`

Use these labels in **PowerPoint**, not inside VESTA if possible.

### 10.B.6 What to avoid
Avoid:
- a huge local crop that loses the focus,
- overuse of coordination polyhedron if it complicates the view,
- wording that turns the local view into a mechanistic claim.

### 10.B.7 Inset workflow
1. In **B_i**, identify a representative metal node.
2. Crop to the first coordination shell.
3. Export `inset_i.png`.
4. In **B_ii**, capture the corresponding node and shell.
5. Export `inset_ii.png`.
6. In PowerPoint, place them side by side and clearly label Zn vs Cu.

### 10.B.8 Final reading test for panel B
The reader should think:

- same scaffold,
- different metal node,
- this local comparison is robust and intentionally shown.

### 10.B.9 Suggested tiny footer
- `nbo · Zn/Cu node comparison`
- or `robust local node contrast`

---

## PANEL C — Cu–Zn pressure exception  
**Pair:**  
- **C_i:** `DB0-m3_o6_o27_f0_nbo.sym.33`  
- **C_ii:** `DB0-m2_o6_o27_f0_nbo.sym.30`  
**Topology:** nbo  
**Scientific role:** metal identity boundary case  
**Key numbers:**  
- median \|Δlog adsorption\| = **0.0820**
- WC concordance = **1.00**
- selectivity concordance = **1.00**
- max geometry fraction of caliper = **0.842**
- **method-sensitive sites total = 8**

### 10.C.1 What you are seeking
This panel should say:

> This is a matched Cu/Zn comparison, but it is a **boundary case**, so the local chemistry must be shown cautiously.

### 10.C.2 What to seek in the whole structure
Seek:
- an nbo view similar in logic to panel B,
- strong visual sameness,
- clear matched scaffold.

### 10.C.3 Whole-structure workflow
1. Open **C_i**.
2. Test three principal views.
3. Choose the one where the global nbo architecture is cleanest.
4. Apply the same camera to **C_ii**.
5. Export both whole views.

### 10.C.4 What to seek in the inset
Seek:
- a **corresponding** Zn/Cu local node environment,
- a visually matched local comparison,
- a descriptive crop, not an interpretive one.

### 10.C.5 What to avoid
Avoid:
- heavy coordination-polyhedron styling,
- any annotation that suggests “this is the validated local mechanism,”
- strong mechanistic language.

### 10.C.6 Inset workflow
1. Choose a local metal-node region in **C_i**.
2. Keep the crop modest and descriptive.
3. Export `inset_i.png`.
4. Match the corresponding region in **C_ii**.
5. Export `inset_ii.png`.
6. In PowerPoint add a small text tag like:
   - `boundary case`
   - or `method-sensitive local comparison`

### 10.C.7 Final reading test for panel C
The reader should think:

- this pair is globally matched,
- there is a Cu/Zn local comparison,
- but the authors are being careful not to overclaim.

### 10.C.8 Suggested tiny footer
- `nbo · boundary case`
- or `method-sensitive local contrast`

---

## PANEL D — Near-null linker comparator  
**Pair:**  
- **D_i:** `DB0-m2_o23_o28_f0_nbo.sym.21`  
- **D_ii:** `DB0-m2_o23_o28_f0_nbo.sym.4`  
**Topology:** nbo  
**Scientific role:** near-null control-like linker comparison  
**Key numbers:**  
- median \|Δlog adsorption\| = **0.0125**
- WC concordance = **1.00**
- selectivity concordance = **0.75**
- max geometry fraction of caliper = **0.147**

### 10.D.1 What you are seeking
This panel should say:

> These two structures are extremely similar globally, and the chemistry contrast is visually real but functionally near-null.

This is the **cleanest “control-like” visual panel**.

### 10.D.2 What to seek in the whole structure
Seek:
- the strongest possible visual impression of **global sameness**,
- a matched nbo view where the reader almost feels they are looking at the same structure twice,
- a view that supports the “near-null comparator” role.

### 10.D.3 Whole-structure workflow
1. Open **D_i**.
2. Test the standard three views.
3. Prefer the one that makes the nbo scaffold look very controlled and symmetric.
4. Apply exactly the same camera to **D_ii**.
5. Export both whole views.

### 10.D.4 What to seek in the inset
Seek:
- a local linker-level difference,
- something visible enough that the reader sees “yes, there is a chemistry difference”,
- but not something that invites a false “active vs inactive” story.

### 10.D.5 What to avoid
Avoid:
- writing `no effect`,
- writing `inactive`,
- choosing an inset that looks too dramatic.

This is a **near-null comparator**, not “nothing changed.”

### 10.D.6 Inset workflow
1. Find a local region where the linker difference is visible.
2. Export comparable local crops for both endpoints.
3. In PowerPoint, place the paired inset underneath the whole structures.
4. Add a small label:
   - `near-null comparator`

### 10.D.7 Final reading test for panel D
The reader should think:

- these structures are almost identical globally,
- there is a small local chemistry difference,
- this panel acts as a careful control-like comparison.

### 10.D.8 Suggested tiny footer
- `nbo · near-null comparator`
- or `strong geometric control`

---

## PANEL E — Process-discordant linker comparator  
**Pair:**  
- **E_i:** `DB0-m3_o440_o155_f0_fsc.sym.26`  
- **E_ii:** `DB0-m3_o152_o155_f0_fsc.sym.27`  
**Topology:** fsc  
**Scientific role:** process-discordant chemistry comparison  
**Key numbers:**  
- median \|Δlog adsorption\| = **0.0641**
- WC concordance = **0.20**
- selectivity concordance = **0.25**
- max geometry fraction of caliper = **0.790**

### 10.E.1 What you are seeking
This panel should say:

> There is a valid matched chemistry comparison here, but the process behavior is discordant, so the structure panel must remain descriptive.

### 10.E.2 What to seek in the whole structure
Seek:
- a readable **fsc** framework view,
- same global camera for both endpoints,
- a view that gives a compact but readable scaffold.

### 10.E.3 Whole-structure workflow
1. Open **E_i**.
2. Test the candidate axis-based views.
3. Choose the view where the framework is most readable and least cluttered.
4. Apply same camera to **E_ii**.
5. Export both whole views.

### 10.E.4 What to seek in the inset
Seek:
- the local chemistry difference,
- a region where the organic environment contrast is visible.

### 10.E.5 What to avoid
This is important:

Do **not** make the inset look like it explains the process discordance.

The inset is only there to say:

- these two matched structures do have a visible local chemistry difference.

It should **not** claim:
- “this motif is why the process becomes discordant.”

### 10.E.6 Inset workflow
1. Identify the most readable local chemistry contrast.
2. Export paired local crops.
3. Use minimal labels.
4. In PowerPoint, if you want a micro-note, use:
   - `process-discordant`
   - not an explanatory phrase.

### 10.E.7 Final reading test for panel E
The reader should think:

- matched global scaffold,
- visible chemistry difference,
- authors are intentionally not over-explaining the discordance.

### 10.E.8 Suggested tiny footer
- `fsc · process-discordant comparison`
- or `descriptive chemistry contrast only`

---

## PANEL F — Exploratory functional-motif example  
**Pair:**  
- **F_i:** `DB0-m9_o17_o27_f0_sra.sym.117`  
- **F_ii:** `DB0-m9_o17_o27_f0_sra.sym.116`  
**Topology:** sra  
**Scientific role:** exploratory functional-motif case  
**Key numbers:**  
- median \|Δlog adsorption\| = **0.0596**
- WC concordance = **0.80**
- selectivity concordance = **1.00**
- max geometry fraction of caliper = **0.449**

### 10.F.1 What you are seeking
This panel should say:

> This is an exploratory structural example where a repeated motif / functional motif difference is worth showing, but it should not be generalized too strongly.

### 10.F.2 What to seek in the whole structure
Seek:
- a view that preserves the **repeat motif** clearly,
- a readable **sra** scaffold,
- a camera that makes the repeated architecture obvious.

### 10.F.3 Whole-structure workflow
1. Open **F_i**.
2. Test principal views.
3. Ask: which view best preserves the repeated motif and scaffold?
4. Apply same camera to **F_ii**.
5. Export both whole views.

### 10.F.4 What to seek in the inset
Seek:
- the local **functional-motif difference**,
- a neat, compact local crop,
- something visually distinctive enough to justify its inclusion.

### 10.F.5 What to avoid
Avoid:
- presenting the panel like a definitive class conclusion,
- overloading it with claims,
- making the inset bigger or more assertive than B or A.

### 10.F.6 Inset workflow
1. Capture the relevant motif in **F_i**.
2. Capture the corresponding motif in **F_ii**.
3. Export both.
4. In PowerPoint, mark this panel explicitly as:
   - `exploratory`

### 10.F.7 Final reading test for panel F
The reader should think:

- this is a valid structural motif comparison,
- it is interesting,
- but the authors are appropriately cautious.

### 10.F.8 Suggested tiny footer
- `sra · exploratory motif case`
- or `exploratory structure example`

---

# 11. What you should physically export from VESTA for each panel

For **every panel**, export exactly these four core images:

- `whole_i.png`
- `whole_ii.png`
- `inset_i.png`
- `inset_ii.png`

## Optional backup exports
If time allows, also export:

- `whole_i_alt.png`
- `whole_ii_alt.png`
- `inset_i_alt.png`
- `inset_ii_alt.png`

This helps if PowerPoint assembly later reveals that the first crop is too tight or too cluttered.

---

# 12. Practical order of work

Do **not** jump randomly across panels.

Use this order:

## Phase 1 — easiest / highest-confidence panels
1. **B**
2. **D**
3. **A**

These three will establish your visual system.

## Phase 2 — moderate caution panels
4. **E**
5. **F**

## Phase 3 — boundary panel
6. **C**

Why this order?

- **B** is the cleanest metal-node case.
- **D** is the cleanest near-null control-like case.
- **A** is the main strong linker showcase.
- **E** and **F** are descriptive and exploratory.
- **C** needs the most caution and is easiest to mishandle.

---

# 13. Acceptance checklist before you move to PowerPoint finalization

For each panel, ask:

## Whole-view checklist
- [ ] Same camera used for endpoint i and ii  
- [ ] Same approximate scale used for endpoint i and ii  
- [ ] Global scaffold readable  
- [ ] Pore / architecture impression visible  
- [ ] Not cluttered  

## Inset checklist
- [ ] Insets show the intended local contrast  
- [ ] Insets are paired and comparable  
- [ ] Insets do not imply an adsorption mechanism  
- [ ] Insets remain readable at small size  

## Scientific checklist
- [ ] Panel role is obvious  
- [ ] No overclaiming  
- [ ] Panel C is clearly cautious  
- [ ] Panel D is not called “inactive”  
- [ ] Panel E is not given an invented explanation  
- [ ] Panel F is clearly exploratory  

## Typography / assembly checklist
- [ ] Arial used in PowerPoint  
- [ ] Panel letters are uppercase A–F  
- [ ] Labels are short and readable  
- [ ] White/clean background  
- [ ] Visual balance is consistent across all six panels  

---

# 14. My strongest recommendations

If you want the best outcome, I would strongly recommend these choices:

## Recommendation 1
**Build the whole views first for all six panels before touching the insets.**

This prevents inconsistency.

## Recommendation 2
**Use B, D, and A as the style anchors.**

Once those three look good, the rest become easier.

## Recommendation 3
**Keep the local insets paired, not single.**

That is what makes this figure better suited to Project 7B than the unrelated example figure.

## Recommendation 4
**Be visually conservative in C and conceptually conservative in E and F.**

That caution will make the figure more credible, not weaker.

## Recommendation 5
**Let the structures dominate the panel.**

Try to make the panel about:
- **70–80% crystal imagery**
- **20–30% labels and small evidence cues**

That is the right balance.

---

# 15. If you want the fastest possible working plan

If you are short on time, do exactly this:

1. Open **B_i**, find the best whole view, copy to **B_ii**.
2. Export both.
3. Make the Zn/Cu local inset pair.
4. Repeat the same workflow for **D**.
5. Repeat for **A**.
6. Then do **E**, **F**, and finally **C**.
7. Assemble all six in PowerPoint with identical visual grammar.
8. Only then do the final polishing pass.

That is the most efficient route.

---

# 16. Final one-line reminder for each panel

- **A:** seek a **strong linker contrast** inside a matched **pcu** scaffold.  
- **B:** seek the cleanest **Zn/Cu node comparison** inside a matched **nbo** scaffold.  
- **C:** seek a **descriptive** Zn/Cu comparison only; this is a **boundary case**.  
- **D:** seek the strongest impression of **global sameness**; this is the **near-null comparator**.  
- **E:** seek a clear local chemistry contrast, but **do not explain the discordance**.  
- **F:** seek a readable motif contrast and mark it **exploratory**.  

---

# 17. Closing note

If you follow this workflow, you will not just produce six screenshots. You will produce a structurally coherent, scientifically disciplined figure system.

That is the real target.