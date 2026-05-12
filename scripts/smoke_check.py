#!/usr/bin/env python3
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
subprocess.run([sys.executable, str(physics_engine)], check=True)
if not physics_csv.exists():
    raise SystemExit("[smoke] physics result CSV was not generated")

with open(physics_csv, "r", newline="") as f:
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
else:
    print("[smoke] proxy physics mode active; wire --backend-dir for real M3D-C1 diagnostics")

print(f"[smoke] OK: {len(rows)} physics rows written to {physics_csv}")
