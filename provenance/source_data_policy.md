# Source-data and redistribution policy

## ARC-MOF-derived inputs

The project uses ARC-MOF-derived structure and adsorption data. The audited source version is associated with ARC-MOF v7, Zenodo DOI `10.5281/zenodo.16802743`.

The public repository follows a conservative redistribution policy:

- raw ARC-MOF source files are not committed;
- source archives are not committed;
- raw/source CIF collections are not mirrored wholesale; only explicitly
  curated and reviewed release inputs may be versioned as narrow exceptions
  with provenance and hashes;
- source filenames, identifiers, version information, hashes, and provenance records may be used to make the workflow traceable;
- compact derived tables may be included only when their release has been reviewed for the intended public repository.

Public availability of a source archive is not treated by this repository as automatic permission to republish its bytes under a new project license.

## Selected structural cases

For structural figures, the preferred public provenance record is:

- framework/MOF identifier;
- upstream source/version;
- source file or archive member identifier where available;
- SHA-256 hash;
- transformation/rendering method.

The authoritative structural-panel Git handoff explicitly supplies 12 selected
CIFs as frozen rendering inputs. They are tracked on the private release branch
under `structural_panel/data/cifs/` with exact SHA-256 provenance. This
project-level inclusion decision does not itself relicense the upstream data;
source-rights sign-off remains part of the repository-wide gate before changing
the repository to public visibility.

## Large RASPA closure

The multi-gigabyte RASPA closure is not appropriate for ordinary Git history. The release strategy is:

1. compact summary/audit tables on GitHub;
2. immutable external archive for the raw closure;
3. persistent identifier plus archive SHA-256 and manifest in this repository.


## Curated structural-panel CIF exception

The authoritative structural-panel Git handoff explicitly freezes 12 panel-prefixed CIF files as versioned rendering inputs under `structural_panel/data/cifs/`. Those 12 files are intended to be tracked together with their source identities and SHA-256 provenance manifest as part of the curated `structural_panel/` module.

This narrow project decision does not relicense the upstream dataset and does not change the conservative policy for other raw ARC-MOF files/CIFs. The structural-panel CIFs should not be replaced with unrelated structures or expanded into a broader raw-data mirror without a separate rights/provenance review.
