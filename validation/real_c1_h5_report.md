# Real `C1.h5` Validation Report

This report documents the first real public M3D-C1 `C1.h5` output that was
found online and the result of running the TCT validation sweep against it.

## Source

Public file discovered in the HEAT repository:

- `/tmp/HEAT/tests/integrationTests/D3DTestCase/d3d/mesh21a_kap6_amu6_newer_n=3/C1.h5`

Repository source:

- [plasmapotential/HEAT](https://github.com/plasmapotential/HEAT)

This file was a real HDF5 output after `git lfs pull`, not a pointer stub.

## Extraction

The M3D-C1 backend extractor was run against the directory containing the file:

```bash
/tmp/c1env/bin/python \
  /root/Open-source\ Fusion\ validation/M3DC1/scripts/extract_m3dc1_backend.py \
  --input-dir /tmp/HEAT/tests/integrationTests/D3DTestCase/d3d/mesh21a_kap6_amu6_newer_n=3 \
  --output-dir /tmp/real_backend2 \
  --case-name heat_d3d_test
```

The extractor used the real file scalars documented by the M3D-C1 reader:

- `Ave_P`
- `E_P`
- `loop_voltage`
- `particle_number`
- `toroidal_current`
- `temax`
- `volume`
- `pohm`

## Extracted Backend Values

Key backend fields from `/tmp/real_backend2/heat_d3d_test.json`:

- `Pfus_MW`: `0.004986430182559823`
- `Pnet_MW`: `0.03564990426110659`
- `TBR`: `1.0208`
- `event_severity_mean`: `0.95`
- `Te_keV`: `3.7227060360483826`
- `Ti_keV`: `3.7227060360483826`
- `density_20_m3`: `0.135639801309915`
- `tau_E_s`: `0.0003682156972810265`
- `backend_source`: `m3dc1_h5_postprocess`

## Validation Sweep Result

The backend JSON was copied to the five TCT candidate names and evaluated with:

```bash
/tmp/c1env/bin/python \
  /root/Open-source\ Fusion\ validation/M3DC1/scripts/run_validation_sweep.py \
  --backend-dir /tmp/real_backend_cases \
  --output-dir /root/Open-source\ Fusion\ validation/M3DC1/validation/results
```

Outcome:

- all 5 cases failed the current hard constraints
- common failure reason: `TBR<1.05;Pnet<1.0`

Output CSV:

- `/root/Open-source Fusion validation/M3DC1/validation/results/20260601_173628/validation_results.csv`

## Interpretation

The public HEAT `C1.h5` file is useful as a real backend integration test,
but it is not reactor-relevant enough to pass the current TCT gate.

The earlier `Pnet=50` values came from the synthetic backend path, not from
this real HDF5 output.

## Current Gap

I searched for a more reactor-relevant public M3D-C1 `C1.h5` with stronger
`TBR`/`Pnet`, but did not find one in public GitHub sources during this pass.
The HEAT D3D integration test is the only real public `C1.h5` found so far.
