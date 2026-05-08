#!/usr/bin/env bash
set -euo pipefail

# Run from this case directory.
cd "$(dirname "$0")"

BIN="${M3DC1_BIN:-../../_localgnu-petsc-opt-25/m3dc1_2d}"
NPROC="${NPROC:-1}"
INPUT="${INPUT:-C1input.smoke}"
LOG="${LOG:-run.log}"
MPIEXEC="${MPIEXEC:-}"

ROOT_DIR="$(cd ../.. && pwd)"
for libdir in \
  "/root/petsc-mpich-install/lib" \
  "/root/m3dc1-scorec-mpich-install/lib" \
  "/root/scorec-mpich-install/lib" \
  "$ROOT_DIR/m3dc1_scorec/build-mpich/lib" \
  "$ROOT_DIR/m3dc1_scorec/build/lib"; do
  if [[ -d "$libdir" ]]; then
    export LD_LIBRARY_PATH="$libdir:${LD_LIBRARY_PATH:-}"
  fi
done

# Container-safe defaults for MPICH+UCX in restricted environments.
export UCX_TLS="${UCX_TLS:-self,tcp}"
export MPIR_CVAR_CH4_SHM_ENABLE="${MPIR_CVAR_CH4_SHM_ENABLE:-0}"

if [[ -z "$MPIEXEC" ]]; then
  if command -v mpiexec.mpich >/dev/null 2>&1; then
    MPIEXEC="mpiexec.mpich"
  else
    MPIEXEC="mpirun"
  fi
fi

if [[ ! -x "$BIN" ]]; then
  echo "ERROR: executable not found or not executable: $BIN" >&2
  exit 1
fi

if [[ ! -f "$INPUT" ]]; then
  echo "ERROR: input file not found: $INPUT" >&2
  exit 1
fi

echo "Launching: $MPIEXEC -np $NPROC $BIN < $INPUT"
"$MPIEXEC" -np "$NPROC" "$BIN" < "$INPUT" | tee "$LOG"
