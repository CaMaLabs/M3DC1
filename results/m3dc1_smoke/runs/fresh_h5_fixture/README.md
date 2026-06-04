# Fresh HDF5 Fixture

This directory captures a single run of M3D-C1 that produced a fresh HDF5
output set for regression use.

Source run:
- Input: `C1input`
- Mesh: `/root/M3DC1/unstructured/runs/first_linear/diii-d_rw1-9K.smb`
- Mesh model: `/root/M3DC1/unstructured/runs/first_linear/diii-d_rw1.txt`
- Executable: `/root/M3DC1/unstructured/build-mpich325/m3dc1_2d`
- Run directory during generation: `/tmp/m3dc1-h5test`

Generated files:
- `C1.h5`
- `equilibrium.h5`
- `time_000.h5`
- `normcurv`
- `run_mpich_ucx.log`

Mesh inputs bundled with the fixture:
- `mesh/diii-d_rw1-9K0.smb`
- `mesh/diii-d_rw1-9K.smb` (symlink to `diii-d_rw1-9K0.smb`)
- `mesh/diii-d_rw1.txt`

Notes:
- `C1.h5` is the HDF5 container file with external links to the slice files.
- `equilibrium.h5` and `time_000.h5` contain the actual mesh and field data.
- The run exited nonzero after the files were written, but the HDF5 output is
  present and valid for inspection and regression comparisons.
