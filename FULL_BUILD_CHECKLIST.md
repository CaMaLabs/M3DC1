# M3D-C1 Full `unstructured` Build Checklist (Local Host)

This checklist captures what was done on this host and what still blocks a full executable run.

## 1) Clone

```bash
git clone https://github.com/PrincetonUniversity/M3DC1.git /root/M3DC1
cd /root/M3DC1
```

## 2) Install base toolchain

```bash
apt-get update
apt-get install -y gfortran openmpi-bin libopenmpi-dev libopenblas-dev mpich libmpich-dev
```

## 3) Install `unstructured` dependencies

```bash
apt-get install -y pkg-config \
  libpetsc-real-dev \
  libhdf5-openmpi-dev \
  libnetcdf-dev libnetcdff-dev \
  libfftw3-dev libfftw3-mpi-dev \
  libgsl-dev \
  libtrilinos-zoltan-dev
```

If interrupted:

```bash
dpkg --configure -a
apt-get -f install -y
```

## 4) Local ARCH file for GNU/MPI

Created: `unstructured/localgnu.mk`

This wires PETSc/HDF5/netCDF/FFTW/GSL from distro packages and builds with `mpif90`.

## 5) PETSc Fortran compatibility shim

Debian PETSc package does not provide `finclude/petscis.h90`, but this M3D-C1 tree includes it.

Created:

- `unstructured/finclude/petscis.h90`

Contents:

```fortran
#include "petscis.h"
```

## 6) Build attempt command

```bash
cd /root/M3DC1/unstructured
make clean ARCH=localgnu
make OPT=1 USEPETSC=1 ARCH=localgnu
```

## 7) Current status on this host

- Build now progresses through many Fortran/C/C++ objects.
- A large set of objects compile (for example in `_localgnu-petsc-opt-25/`):
  `control.o`, `fftw_fortran.o`, `gsl_wrapper.o`, `interpolate.o`, `math.o`, `read_ascii.o`, `read_namelist.o`, `region.o`, `signal_handler.o`, `spline.o`.
- Frequent OpenMPI warning:
  `opal_ifinit: ioctl(SIOCGIFHWADDR) failed with errno=13`
  (warning only; compile still proceeds).

## 8) Remaining blockers to resolve for full executable + regtest run

1. PETSc Fortran-header expectations in this source vs distro PETSc layout/macros are fragile.
2. Runtime MPI in this proot/container environment has transport/shared-memory constraints (already observed in skeleton runs), so `regtest` batch flows are unlikely to run unchanged.
3. Even with `USEPETSC=1`, this code path is not a maintained distro-default path; full success generally expects project-provided module stacks (PPPL/NERSC/etc.).

## 9) Practical next step options

1. Use a supported HPC environment from upstream docs (`module load m3dc1/...`) and run official regtests there.
2. Build a container with upstream-compatible PETSc + SCOREC/PUMI stack (closest to module environments).
3. Keep iterating local GNU path and patch compatibility includes/macros until `m3dc1_2d` links, then run a single minimal case before full regtests.
