#!/usr/bin/env python3
"""Run the open-source FreeGSNKE verifier against the installed checkout.

This is a lightweight equilibrium verification step used as the OSS complement
to the M3D-C1 smoke harness. It runs a curated subset of the FreeGSNKE pytest
suite from the repository root so the machine_config fixtures resolve correctly.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FREEGSNKE_REPO = Path(os.environ.get("FREEGSNKE_REPO", "/root/work/freegsnke"))
DEFAULT_FREEGSNKE_PYTHON = Path(
    os.environ.get("FREEGSNKE_PYTHON", "/root/work/.venv/bin/python")
)
DEFAULT_RESULTS_DIR = REPO_ROOT / "validation" / "results"
DEFAULT_SUMMARY = DEFAULT_RESULTS_DIR / "freegsnke_verifier_summary.json"

DEFAULT_TESTS = [
    "freegsnke/tests/test_inverse_static_solver.py",
    "freegsnke/tests/test_implicit_euler.py",
    "freegsnke/tests/test_static_solver.py",
]


def run_verifier(freegsnke_repo: Path, python_exe: Path, tests: list[str]) -> dict[str, object]:
    if not freegsnke_repo.exists():
        raise SystemExit(f"[freegsnke] repository not found: {freegsnke_repo}")
    if not python_exe.exists():
        raise SystemExit(f"[freegsnke] python executable not found: {python_exe}")

    cmd = [str(python_exe), "-m", "pytest", "-q", *tests]
    env = os.environ.copy()
    env["NUMBA_DISABLE_JIT"] = "1"

    proc = subprocess.run(
        cmd,
        cwd=freegsnke_repo,
        env=env,
        text=True,
        capture_output=True,
    )

    summary = {
        "repo": str(freegsnke_repo),
        "python": str(python_exe),
        "cwd": str(freegsnke_repo),
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "tests": tests,
        "numba_disable_jit": True,
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the FreeGSNKE OSS verifier.")
    parser.add_argument("--freegsnke-repo", type=Path, default=DEFAULT_FREEGSNKE_REPO)
    parser.add_argument("--python", type=Path, default=DEFAULT_FREEGSNKE_PYTHON)
    parser.add_argument("--out", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument(
        "--test",
        action="append",
        dest="tests",
        help="Specific pytest node or file to run. May be repeated.",
    )
    args = parser.parse_args()

    tests = args.tests or DEFAULT_TESTS
    summary = run_verifier(args.freegsnke_repo, args.python, tests)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as f:
        json.dump(summary, f, indent=2)

    print("[freegsnke] repo:", summary["repo"])
    print("[freegsnke] python:", summary["python"])
    print("[freegsnke] tests:")
    for item in tests:
        print(f"[freegsnke]   - {item}")
    print(f"[freegsnke] summary written to {args.out}")
    sys.stdout.write(summary["stdout"])
    sys.stderr.write(summary["stderr"])
    raise SystemExit(summary["returncode"])


if __name__ == "__main__":
    main()
