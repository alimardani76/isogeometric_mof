# Scientific claim boundaries

This file records interpretation boundaries that must remain stable during public-release engineering. Repository cleanup, figure canonicalization, path refactoring, and documentation work must not silently broaden the scientific claims.

## Supported within the frozen analysis

- Linker changes show adsorption separation beyond the same-chemistry background across the analyzed conditions.
- Metal-change effects are reproducible but conditional and have narrower support.
- Selected strong-linker RASPA cases retain large adsorption separation.
- Selected near-null RASPA cases remain near-null in the common validation setting.

## Explicitly not established

The repository and manuscript must not claim that:

- the functional-motif class is broadly generalizable from the six primary motif pairs/families;
- geometry has been fully removed;
- residual-adjustment coefficients are causal or direct effects;
- CO2 always exhibits the largest chemistry-associated separation;
- an uptake difference guarantees selectivity or process improvement;
- selected-case RASPA validates all population trends;
- the A4 pressure exception is reproduced by the common RASPA protocol;
- charge-off calculations prove an electrostatic mechanism;
- REPEAT charges establish linker-local charge transfer;
- selected structures identify adsorption sites;
- unavailable density-map assets support density-map claims.

## Release-engineering rule

The public-release branch may improve organization, portability, provenance, and reproducibility, but it must not:

1. redefine the frozen matched populations;
2. change scientific thresholds or model settings without an explicit new analysis;
3. silently regenerate paper-facing numbers from altered defaults;
4. convert associational evidence into causal language;
5. present selected-case validation as population-wide validation.
