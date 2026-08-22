# Environment evidence

No installable environment file was found in the audited folders. The following is evidence recovered from scripts and manifests, not a complete dependency specification.

## Recorded versions

`Step 4 results/02_cif_chemistry/phase2a_preflight/phase2a_toolchain.json` records:

- operating system: Windows 11 (`Windows-11-10.0.26220-SP0`)
- Python: 3.13.13
- pandas: 2.3.2
- NumPy: 1.26.4
- pymatgen: 2025.10.7
- CrystalNN: available through pymatgen
- ChemEnv `LocalGeometryFinder`: available through pymatgen
- gemmi: not installed
- Zeo++, RASPA executables: not found

The Step 3 figure manifest records matplotlib 3.10.5.

## Imported packages without audited version pins

- PyArrow (`pyarrow`, `pyarrow.dataset`, `pyarrow.parquet`)
- SciPy (`scipy.spatial`, `scipy.stats`, `scipy.optimize`)
- scikit-learn (`sklearn.covariance.LedoitWolf`)
- joblib

Standard-library modules and Windows batch execution are also used.

Do not convert this list into a pinned requirements file without testing the workflow. Package compatibility, especially Python 3.13 support and the pymatgen stack, has not been reproduced during this inventory audit.
