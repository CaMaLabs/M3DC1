#!/usr/bin/env bash
set -u
cd /root/M3DC1/unstructured || exit 99
LOG=/root/M3DC1/unstructured/build_mpich.log
{
  echo "START $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  echo "PWD $(pwd)"
  echo "CMD make -j1 OPT=1 USEPETSC=1 ARCH=localgnu"
  make -j1 OPT=1 USEPETSC=1 ARCH=localgnu
  ec=$?
  echo "EXIT:$ec"
  echo "END $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  exit $ec
} >> "$LOG" 2>&1
