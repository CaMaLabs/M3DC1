from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
candidate = ROOT / "validation" / "candidate0_be_outer_killer.json"

print("[smoke] repo root:", ROOT)
print("[smoke] candidate exists:", candidate.exists())

if candidate.exists():
    with open(candidate, "r") as f:
        data = json.load(f)

    print("[smoke] candidate:", data.get("candidate_name"))
    print("[smoke] topology:", data.get("blanket_topology"))
    print("[smoke] TCT enabled:", data.get("active_tct"))
    print("[smoke] lithium current:", data.get("lithium_current_enabled"))

print("[smoke] OK")
