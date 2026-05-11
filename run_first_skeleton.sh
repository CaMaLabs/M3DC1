#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASE_DIR="${ROOT_DIR}/skeleton/m3dc1_skeleton_big_spec_omp"

cd "${CASE_DIR}"

# Build objects with GNU + MPICH toolchain.
make clean
make \
  F90=mpif90.mpich \
  LD=mpif90.mpich \
  F90FLAGS='-O3 -fopenmp -fimplicit-none' \
  LDFLAGS='-fopenmp' \
  LIB='-lopenblas' || true

# Link manually so BLAS/LAPACK appear after object files.
mpif90.mpich \
  etimes.o math.o element.o mesh.o nintegrate.o field.o \
  m3dc1_data.o m3dc1_nint.o matdef.o main.o \
  -fopenmp -lopenblas -llapack -lblas \
  -o m3dc1_skeleton

# Run with shared-memory transports disabled for this proot/container environment.
OMP_NUM_THREADS=1 \
MPIR_CVAR_CH4_SHM_ENABLE=0 \
MPIR_CVAR_CH4_POSIX_SHM_ENABLE=0 \
UCX_TLS=tcp,self \
mpirun.mpich -np 1 ./m3dc1_skeleton
