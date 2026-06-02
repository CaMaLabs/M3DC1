#!/usr/bin/env python3
import argparse
from pathlib import Path
import csv
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
candidate = ROOT / "validation" / "candidate0_be_outer_killer.json"
case_matrix = ROOT / "validation" / "generated" / "candidate0_case_matrix.json"
physics_csv = ROOT / "validation" / "generated" / "candidate0_physics_results.csv"
physics_engine = ROOT / "validation" / "physics_engine.py"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the M3D-C1 smoke harness.")
    parser.add_argument(
        "--backend-dir",
        type=Path,
        default=None,
        help="Optional backend diagnostics directory containing per-case JSON files",
    )
    parser.add_argument(
        "--physics-out",
        type=Path,
        default=physics_csv,
        help="CSV output path for physics results",
    )
    args = parser.parse_args()

    print("[smoke] repo root:", ROOT)
    print("[smoke] candidate exists:", candidate.exists())

    if not candidate.exists():
        raise SystemExit("[smoke] missing validation/candidate0_be_outer_killer.json")

    with open(candidate, "r") as f:
        data = json.load(f)

    print("[smoke] candidate:", data.get("candidate_name"))
    print("[smoke] topology:", data.get("blanket_topology"))
    print("[smoke] TCT enabled:", data.get("active_tct"))
    print("[smoke] lithium current:", data.get("lithium_current_enabled"))

    required_top = ["reactor", "plasma", "wall", "tct_translation"]
    missing = [key for key in required_top if key not in data]
    if missing:
        raise SystemExit(f"[smoke] candidate missing required sections: {missing}")

    print("[smoke] generating case matrix")
    subprocess.run([sys.executable, str(ROOT / "validation" / "generate_case_matrix.py")], check=True)
    if not case_matrix.exists():
        raise SystemExit("[smoke] case matrix was not generated")

    print("[smoke] running physics harness")
    physics_cmd = [sys.executable, str(physics_engine), "--out", str(args.physics_out)]
    if args.backend_dir is not None:
        physics_cmd.extend(["--backend-dir", str(args.backend_dir)])
        print(f"[smoke] backend diagnostics dir: {args.backend_dir}")
    subprocess.run(physics_cmd, check=True)
    if not args.physics_out.exists():
        raise SystemExit("[smoke] physics result CSV was not generated")

    with open(args.physics_out, "r", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise SystemExit("[smoke] physics result CSV is empty")

    required_result_cols = [
        "case_name",
        "status",
        "backend_source",
        "Pfus_MW",
        "Pnet_MW",
        "TBR",
        "event_severity_mean",
        "score",
    ]
    missing_cols = [col for col in required_result_cols if col not in rows[0]]
    if missing_cols:
        raise SystemExit(f"[smoke] physics CSV missing columns: {missing_cols}")

    if all(row.get("backend_source") != "proxy" for row in rows):
        print("[smoke] backend diagnostics were used")
    elif args.backend_dir is not None:
        print("[smoke] backend diagnostics directory supplied, but no diagnostics JSON was found")
    else:
        print("[smoke] proxy physics mode active; wire --backend-dir for real M3D-C1 diagnostics")

    print(f"[smoke] OK: {len(rows)} physics rows written to {args.physics_out}")


if __name__ == "__main__":
    main()
