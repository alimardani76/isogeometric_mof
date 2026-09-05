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

The authoritative structural-panel private handoff supplied 12 selected CIFs as
frozen rendering inputs. For the public Git release, those third-party CIF byte
files are intentionally not redistributed. Their framework identities, source
references, sizes, and SHA-256 values remain recorded in the structural
manifests, so the frozen figure provenance remains auditable without this
repository granting or assuming upstream redistribution rights.

## Large RASPA closure

The multi-gigabyte RASPA raw closure is intentionally outside the scope of this
GitHub publication release and is not committed to ordinary Git history.

The public release layer consists of:

1. compact audited summary/reproducibility tables on GitHub;
2. exact protocol/version/seed/hash records needed to identify the selected-case
   production calculations;
3. manuscript-facing Figure 6 / Figure S06 provenance and claim boundaries.

No external upload of the raw multi-gigabyte closure is required by this
repository release. If the authors later choose to deposit the raw closure,
that deposit can be linked as an optional archival supplement without changing
the scientific identity of the GitHub release.


## Curated structural-panel CIF provenance

The authoritative private structural-panel handoff freezes 12 panel-prefixed CIF
identities and hashes. The public Git release retains those provenance records
but excludes the 12 CIF byte files themselves.

This conservative boundary avoids treating repository publication as a grant of
rights in upstream ARC-MOF-derived structure files. Users who wish to rerun the
structure rendering should obtain the corresponding source structures through
the upstream/permitted access route and match them against the recorded
identifiers/hashes.
