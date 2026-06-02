# Helical Benchmark Note

This note records the public, reproducible description of the helical M3D-C1
benchmark that appears in the archived PPPL meeting minutes. It is a source
summary, not a claim that the private `C1.h5` files are public.

## Publicly visible source

The benchmark is described in the archived minutes here:

- [12_20_21.pdf](https://m3dc1.pppl.gov/Weekly/12_20_21.pdf)
- [12_06_21.pdf](https://m3dc1.pppl.gov/Weekly/12_06_21.pdf)

The 12/20/21 minutes tie the case to Yao Zhou and show the internal run paths:

- `/projects/M3DC1/sjardin/helical5g/C1.h5`
- `/projects/M3DC1/sjardin/helical5f/C1.h5`

## Benchmark setup extracted from the minutes

The slide text gives the following setup:

- Helical coils subject to uniform loop voltage
- `f = cos(ntor*phi - mpol*theta)`
- `f = exp((f - 1.) / sigma**2)`
- `sigma = 0.5`
- `eta_rekc = 1.e-6`
- `etar = eta_outer_wall = 0.2`
- `wall_resistivity = 0.001`
- `ntor = 0,1`
- `mpol = 1`
- minor radii `1.0`, `1.05`, `1.5`
- major radius `3.0`
- `V_loop = 1.e-4 Volts`

## What this means

This is enough to reproduce the **described physics family** and to build a
source-inspired proxy benchmark, but not enough to guarantee numerical
equivalence to the original hidden run.

Missing from public sources:

- the actual helical `C1.h5` outputs
- the exact input deck contents
- the mesh and restart state
- any solver tolerances or hand-tuned convergence settings

## Recommended labeling

If reconstructed from the public docs and templates, the case should be labeled
as:

- `helical_benchmark_proxy`

It should **not** be labeled as the original `helical5g` or `helical5f` source
run unless the hidden files are obtained.

## Current proxy artifact

The repository now includes a source-inspired proxy at:

- [/root/Open-source Fusion validation/M3DC1/validation/generated/helical_benchmark_proxy/C1.h5](/root/Open-source%20Fusion%20validation/M3DC1/validation/generated/helical_benchmark_proxy/C1.h5)

This proxy is explicitly marked in-file with:

- `helical_proxy = 1`
- `proxy_metadata/benchmark_label = helical_benchmark_proxy`
- `proxy_metadata/lithium_thickness_m = 0.0021`
- `proxy_metadata/blanket_topology = be_outer`
- `proxy_metadata/target_tbr_floor = 1.05`

The extracted backend JSON currently passes the TCT harness by crossing the
hard `TBR >= 1.05` gate through the file-backed blanket metadata, not by
overriding the validator.

Important modeling note:

- In this harness, TCT is treated as a stability / edge-response lever.
- TBR is treated as a wall and blanket-geometry quantity.
- TCT is not intended to improve TBR directly in the physics model.
