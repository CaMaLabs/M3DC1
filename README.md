# M3DC1 Validation Harness

This repository is Chase Lunsford's public M3D-C1-side validation workspace for the TCT / liquid-lithium fusion concept.

The current goal is **not** to prove TCT from scratch. Prior optimizer and blanket-design work is treated as the external foundation. This repo is for testing whether a TCT-like control translation produces useful edge/current-sheet stabilization behavior in an M3D-C1-compatible workflow.

## Research purpose

This repository exists to bridge the fusion blanket / TCT concept into a more mainstream plasma-validation direction.

The core validation question is:

> Can the candidate reactor/control concept be translated into a plasma-side validation campaign that tests baseline behavior against weak, moderate, and aggressive TCT-like stabilization analogs, including lithium-wall current coupling?

The repository is public to preserve provenance, assumptions, candidate definitions, harness code, generated case matrices, and validation boundaries in a timestamped development history.

## Current status

This is an active independent research and validation-harness repository. It should be read as a staging and translation layer, not as a completed M3D-C1 physics result.

Current emphasis:

- keep the frozen Candidate-0 target explicit,
- generate a controlled case matrix,
- preserve deterministic proxy checks for harness testing,
- define a backend diagnostics extraction contract,
- avoid silent false-success outputs,
- and prepare for real M3D-C1 / backend diagnostic ingestion when available.

## What is validated vs. exploratory

### More concrete / implemented

- Public repository and timestamped development history.
- Candidate-0 configuration target.
- Case-matrix generation.
- Deterministic proxy physics harness for workflow testing.
- Constraint gates and explicit status labels.
- Backend diagnostics JSON ingestion contract.
- CSV output intended to keep failed or partial cases inspectable.

### Exploratory / not yet proven here

- Real M3D-C1 compiled-solver validation of the TCT analog.
- Physical effectiveness of TCT-style control in the real plasma edge.
- Physical effectiveness of lithium-current coupling as an actuator.
- Whether proxy improvements survive high-fidelity plasma simulation.
- Whether this candidate is reactor-practical after full plasma, neutronics, thermal, and materials analysis.

## Provenance

Author / researcher: Chase Lunsford (`@chaseakat`).

This repo was made public to establish visible provenance for the M3D-C1 validation path connected to the fusion blanket / thickness-controlled tokamak research. The commit history, candidate JSON, generated matrices, scripts, and README notes should be treated as part of the public timestamped record of development.

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
validation/                Chase's validation harness, candidate files, case matrix tools, and physics harness
scripts/                   Bootstrap and smoke-check scripts
```

## Current validation workflow

Run the full local harness check:

```bash
python3 scripts/smoke_check.py
```

Or run the steps manually:

```bash
python3 validation/generate_case_matrix.py
python3 validation/physics_engine.py
```

This produces:

```text
validation/generated/candidate0_case_matrix.json
validation/generated/candidate0_cases.csv
validation/generated/candidate0_physics_results.csv
```

The generated files bridge the fusion/TCT optimizer concept into a controlled M3D-C1 validation campaign.

For open-source verification targets that complement the M3D-C1 smoke cases, see:

- [`validation/open_source_verification_matrix.md`](validation/open_source_verification_matrix.md)
- [`validation/helical_author_map.md`](validation/helical_author_map.md)
- [`validation/helical_benchmark_note.md`](validation/helical_benchmark_note.md)
- [`scripts/run_freegsnke_verifier.py`](scripts/run_freegsnke_verifier.py)

The current helical benchmark proxy artifact is written here:

- [`validation/generated/helical_benchmark_proxy/C1.h5`](validation/generated/helical_benchmark_proxy/C1.h5)

It is a source-inspired reconstruction, not the hidden PPPL `helical5g` or
`helical5f` file. The file carries explicit proxy metadata so the reconstructed
TBR gate can be traced back to the benchmark assumptions instead of the
validator. In this harness, TCT affects stability and edge-response proxies,
not TBR directly.

## Physics harness boundary

`validation/physics_engine.py` is the current validation engine layer. It is **not** a replacement for the compiled M3D-C1 solver. It provides:

- deterministic proxy physics for harness testing,
- a backend diagnostics JSON extraction contract,
- hard constraint checks,
- explicit candidate status labels,
- debug-friendly CSV output,
- no silent conversion of failed physics extraction into successful zero-output rows.

When no backend diagnostics are supplied, rows are labeled with:

```text
backend_source = proxy
```

When real M3D-C1 post-processing is available, place JSON diagnostics in one of these forms:

```text
<backend-dir>/<case_name>.json
<backend-dir>/<case_name>/diagnostics.json
```

Then run:

```bash
python3 validation/physics_engine.py --backend-dir path/to/backend_diagnostics
```

The smoke runner also accepts a backend diagnostics directory:

```bash
M3DC1_BACKEND_DIR=path/to/backend_diagnostics bash scripts/run_first_smoke_tests.sh
```

If you have raw M3D-C1 HDF5 output instead, point the runner at the case
directories and let it generate backend JSON first:

```bash
M3DC1_H5_DIR=path/to/m3dc1_runs bash scripts/run_first_smoke_tests.sh
```

The FreeGSNKE open-source verifier can also be run directly:

```bash
python3 scripts/run_freegsnke_verifier.py
```

Recognized backend physics fields include:

```text
Te_keV
Ti_keV
density_20_m3
tau_E_s
Pfus_MW
alpha_power_MW
neutron_power_MW
blanket_heat_MW
wall_loading_MW_m2
TBR
Q
Paux_MW
Pnet_MW
attenuation
event_severity_mean
R_less_than_1_fraction
backend_returncode
```

If backend diagnostics exist but contain no recognized physics fields, the row is marked:

```text
status = empty_plasma_state
```

If constraints reject a candidate, the row is marked:

```text
status = constraints_failed
```

Raw/proxy values are still preserved in the CSV so failures remain inspectable.

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
- net power proxy / backend extracted power
- tritium breeding proxy / backend extracted TBR
- neutron wall loading
- R < 1 fraction when available

## Hard constraints currently enforced

The physics harness currently applies these conservative gates:

```text
betaN <= 3.5
greenwald_fraction <= 0.95
neutron wall loading <= 4.0 MW/m^2
TBR >= 1.05
Pnet_MW >= 1.0
Pfus_MW > 0
```

These are validation gates, not final reactor licensing limits. Update them only when a stronger constraint basis is available.

## Build note

The upstream M3D-C1 stack is dependency-heavy. The included Spack recipe references MPI, HDF5, NetCDF, PETSc, SuperLU_DIST, GSL, FFTW, Zoltan, and PUMI. Use `scripts/bootstrap_spack_m3dc1.sh` as the starting point, but expect local HPC/Linux dependency tuning.

## Citation / attribution request

If this repository, its candidate structures, scripts, or TCT-related validation framing influence downstream work, please cite or link back to this repo and credit Chase Lunsford / `@chaseakat`.
