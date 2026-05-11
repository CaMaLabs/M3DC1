# M3DC1 Validation Harness

This repository is being used as the M3D-C1-side validation workspace for the TCT/liquid-lithium fusion concept.

The current goal is **not** to prove TCT from scratch. Prior work is treated as the external foundation. This repo is for testing whether a TCT-like control translation produces useful edge/current-sheet stabilization behavior in an M3D-C1-compatible workflow.

## Frozen validation target

Candidate-0:

- blanket topology: `be_outer_killer`
- active TCT: enabled
- liquid lithium layer: enabled
- lithium current coupling: enabled
- purpose: compare baseline vs weak/moderate/aggressive TCT analogs

Canonical candidate data lives in:

```text
validation/candidate0_be_outer_killer.json
```

## Repository layout

```text
unstructured/              Upstream/raw M3D-C1 source and helper material
unstructured/spack/m3dc1/  Spack package recipe for M3D-C1
validation/                Chase's validation harness, candidate files, and case matrix tools
scripts/                   Bootstrap and smoke-check scripts
```

## First workflow

```bash
python3 scripts/smoke_check.py
python3 validation/generate_case_matrix.py
```

This produces:

```text
validation/generated/candidate0_case_matrix.json
validation/generated/candidate0_cases.csv
```

Those generated files are the bridge from the fusion/TCT optimizer repo into a controlled M3D-C1 validation campaign.

## Case matrix

The first campaign intentionally varies only the TCT analog strength and lithium-wall current proxy:

1. baseline: no TCT analog, no lithium current
2. weak TCT analog
3. moderate TCT analog
4. aggressive TCT analog
5. active TCT + lithium current coupling

The expected observables are:

- mode growth rate proxy
- reconnection/current-sheet onset proxy
- edge current response
- energy-loss/severity proxy
- wall/load transient proxy

## Build note

The upstream M3D-C1 stack is dependency-heavy. The included Spack recipe references MPI, HDF5, NetCDF, PETSc, SuperLU_DIST, GSL, FFTW, Zoltan, and PUMI. Use `scripts/bootstrap_spack_m3dc1.sh` as the starting point, but expect local HPC/Linux dependency tuning.
