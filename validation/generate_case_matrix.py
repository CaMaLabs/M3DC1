import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CANDIDATE = ROOT / "candidate0_be_outer_killer.json"
OUTDIR = ROOT / "generated"
OUTDIR.mkdir(parents=True, exist_ok=True)

with open(CANDIDATE, "r") as f:
    base = json.load(f)

cases = []

variants = [
    ("baseline", 0.0, 0.0),
    ("weak_tct", 0.2, 0.0),
    ("moderate_tct", 0.5, 0.05),
    ("aggressive_tct", 0.8, 0.0),
    ("aggressive_tct_li_current", 0.8, 0.10),
]

for name, tct_strength, li_current in variants:
    case = json.loads(json.dumps(base))
    case["case_name"] = name
    case["tct_translation"]["control_strength"] = tct_strength
    case["wall"]["lithium_current_proxy"] = li_current
    cases.append(case)

json_out = OUTDIR / "candidate0_case_matrix.json"
with open(json_out, "w") as f:
    json.dump(cases, f, indent=2)

csv_out = OUTDIR / "candidate0_cases.csv"
with open(csv_out, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "case_name",
        "tct_strength",
        "li_current",
        "B0_T",
        "Ip_MA",
        "H98",
        "greenwald_fraction",
    ])

    for case in cases:
        writer.writerow([
            case["case_name"],
            case["tct_translation"]["control_strength"],
            case["wall"]["lithium_current_proxy"],
            case["reactor"]["B0_T"],
            case["reactor"]["Ip_MA"],
            case["plasma"]["H98"],
            case["plasma"]["greenwald_fraction"],
        ])

print(f"Generated {len(cases)} validation cases")
print(json_out)
print(csv_out)
