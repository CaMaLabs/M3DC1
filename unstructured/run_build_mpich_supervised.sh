#!/usr/bin/env bash
set -u
cd /root/M3DC1/unstructured || exit 99
LOG=/root/M3DC1/unstructured/build_mpich.log
HB=/root/M3DC1/unstructured/build_mpich.heartbeat
PIDF=/root/M3DC1/unstructured/build_mpich.pid
OBJDIR=/root/M3DC1/unstructured/_localgnu-petsc-25

echo $$ > "$PIDF"
{
  echo "START $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  echo "HOST $(hostname)"
  echo "PWD $(pwd)"
  echo "CMD make -j1 OPT=0 USEPETSC=1 ARCH=localgnu"
} >> "$LOG"

(
  while :; do
    ts=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    echo "$ts" > "$HB"
    if [ -d "$OBJDIR" ]; then
      c=$(find "$OBJDIR" -maxdepth 1 -name '*.o' | wc -l)
      echo "PROGRESS $ts objects=$c" >> "$LOG"
    fi
    sleep 20
  done
) &
HBPID=$!

make clean ARCH=localgnu >> "$LOG" 2>&1
make -j1 OPT=0 USEPETSC=1 ARCH=localgnu >> "$LOG" 2>&1
EC=$?
kill "$HBPID" 2>/dev/null || true
wait "$HBPID" 2>/dev/null || true

echo "EXIT:$EC" >> "$LOG"
echo "END $(date -u +'%Y-%m-%dT%H:%M:%SZ')" >> "$LOG"
exit "$EC"
