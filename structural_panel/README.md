# Project 7B structural panel

This directory contains the curated final state of the structural-panel workflow: selected-structure provenance, evidence, canonical OVITO scripts, final source images, and final composite artwork. The 12 ARC-MOF-derived CIF byte files from the private handoff are not redistributed in the public Git release; their identities and SHA-256 hashes remain in the manifests.

## Final panels

| Panel | Role | Topology | Endpoint i | Endpoint ii |
|---|---|---|---|---|
| A | Strong linker / process-aligned linker contrast | pcu | `DB0-m3_o11_o17_f0_pcu.sym.32` | `DB0-m3_o12_o20_f0_pcu.sym.24` |
| B | Strong metal-node / process-aligned Zn/Cu node contrast | nbo | `DB0-m3_o7_o7_f0_nbo.sym.48` | `DB0-m2_o7_o7_f0_nbo.sym.45` |
| C | Cu/Zn boundary / pressure-exception · method-sensitive | nbo | `DB0-m3_o6_o27_f0_nbo.sym.33` | `DB0-m2_o6_o27_f0_nbo.sym.30` |
| D | Near-null linker / subtle contrast · strongest geometry control | nbo | `DB0-m2_o23_o28_f0_nbo.sym.21` | `DB0-m2_o23_o28_f0_nbo.sym.4` |
| E | Process-discordant / descriptive local chemistry contrast | fsc | `DB0-m3_o440_o155_f0_fsc.sym.26` | `DB0-m3_o152_o155_f0_fsc.sym.27` |
| F | Exploratory motif / cyano-bearing environment contrast | sra | `DB0-m9_o17_o27_f0_sra.sym.117` | `DB0-m9_o17_o27_f0_sra.sym.116` |


## Reproducibility notes

The panel-specific scripts under `src/ovito/` are the selected final/preflight
scripts from the tested workflow. Because third-party CIF byte files are not
redistributed in the public Git release, rerunning structure rendering requires
the user to obtain permitted source structures independently and supply the
expected Project 7B starter-pack-style CIF tree (or an equivalent `P7B_ROOT`
configuration) as defined by the config modules. The approved/frozen source
PNGs, PPTX, and PDF remain the publication assets.

The final figures in `figures/final/` are the current editable (`.pptx`) and exported (`.pdf`) artwork. The 24 source PNGs used in the finalized PPTX are stored under `figures/source_images/`.

See `docs/FINAL_FREEZE_LOG.md` and the handoff package for scientific guardrails and Git finalization instructions.

## Public-repository layout

For public redistribution, the structural module retains the selected structure
identifiers/hashes but not the third-party CIF byte files. Users who have
permitted source structures should set `P7B_ROOT` to the compatible local
starter-pack layout. Generated screening/review outputs remain ignored by Git.

`data/manifests/99_PACKAGE_MANIFEST.csv` and
`data/manifests/REPO_PAYLOAD_SHA256.csv` are retained as provenance from the
authoritative handoff. The latter still records all 100 original payload entries;
the public-release integrity checker verifies all 87 frozen non-CIF/non-README
payload files, requires the release-adapted README to remain tracked, and also
verifies that the 12 CIF byte files are not tracked.
