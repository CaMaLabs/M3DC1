#!/usr/bin/env python3
"""M3D-C1 validation physics harness.

This is not a replacement for the compiled M3D-C1 solver.  It is the missing
validation layer around it:

1. load generated candidate cases,
2. optionally extract backend/M3D-C1 output diagnostics,
3. fall back to a deterministic, labeled proxy model when backend data is absent,
4. apply hard engineering constraints,
5. write a debug-friendly CSV that never hides NaN/empty plasma states as zeros.

The proxy model is intentionally simple and documented so it can be replaced by
real M3D-C1 output extraction as soon as the solver output files are available.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parent
DEFAULT_CASE_MATRIX = ROOT / "generated" / "candidate0_case_matrix.json"
DEFAULT_OUTPUT = ROOT / "generated" / "candidate0_physics_results.csv"

# Hard limits used to separate physically interesting proxy candidates from
# obviously invalid regimes.  Tune these only when you have stronger constraints.
MAX_BETAN = 3.5
MAX_GREENWALD_FRACTION = 0.95
MAX_NEUTRON_WALL_LOADING_MW_M2 = 4.0
MIN_TBR = 1.05
MIN_PNET_MW = 1.0

A_FW_M2_DEFAULT = 36.91232
DT_NEUTRON_FRACTION = 0.80
DT_ALPHA_FRACTION = 0.20


@dataclass
class PhysicsResult:
    candidate_id: str
    case_name: str
    status: str
    failure_reason: str
    backend_source: str
    backend_returncode: int
    passed_hard_constraints: bool

    # Config echo
    blanket_topology: str
    blanket_ordering: str
    tct_mode: str
    tct_strength: float
    li_current: float
    severity_scale: float
    lithium_thickness_m: float
    R_m: float
    a_m: float
    B0_T: float
    Ip_MA: float
    H98: float
    greenwald_fraction: float
    betaN: float

    # Extracted or proxy physics
    Te_keV: float
    Ti_keV: float
    density_20_m3: float
    tau_E_s: float
    Pfus_MW: float
    alpha_power_MW: float
    neutron_power_MW: float
    blanket_heat_MW: float
    wall_loading_MW_m2: float
    TBR: float
    Q: float
    Paux_MW: float
    Pnet_MW: float
    attenuation: float
    event_severity_mean: float
    R_less_than_1_fraction: float
    score: float


def finite_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(out) or math.isinf(out):
        return default
    return out


def deep_get(data: Dict[str, Any], path: Iterable[str], default: Any = None) -> Any:
    cur: Any = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def load_cases(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise SystemExit(
            f"Case matrix not found: {path}\n"
            "Run: python3 validation/generate_case_matrix.py"
        )
    with path.open("r") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise SystemExit(f"Expected list of cases in {path}")
    return data


def extract_backend_json(case: Dict[str, Any], backend_dir: Optional[Path]) -> Optional[Dict[str, Any]]:
    """Read a simple backend JSON if present.

    Supported locations:
      <backend_dir>/<case_name>.json
      <backend_dir>/<case_name>/diagnostics.json

    This gives us a stable contract for future M3D-C1 post-processing scripts.
    """
    if backend_dir is None:
        return None
    case_name = str(case.get("case_name", "case"))
    candidates = [
        backend_dir / f"{case_name}.json",
        backend_dir / case_name / "diagnostics.json",
    ]
    for path in candidates:
        if path.exists():
            with path.open("r") as f:
                payload = json.load(f)
            if not isinstance(payload, dict):
                raise SystemExit(f"Backend diagnostics must be a JSON object: {path}")
            payload["_backend_file"] = str(path)
            return payload
    return None


def proxy_physics(case: Dict[str, Any]) -> Dict[str, float]:
    """Deterministic first-order proxy for validation harness testing.

    This is a labeled bridge model, not a scientific proof.  It gives nonzero,
    reproducible values so the campaign machinery, scoring, and constraints can
    be tested while real M3D-C1 outputs are being wired in.
    """
    R = finite_float(deep_get(case, ["reactor", "R_m"]), 5.5) or 5.5
    a = finite_float(deep_get(case, ["reactor", "a_m"]), 1.8) or 1.8
    B0 = finite_float(deep_get(case, ["reactor", "B0_T"]), 7.2) or 7.2
    Ip = finite_float(deep_get(case, ["reactor", "Ip_MA"]), 14.0) or 14.0
    H98 = finite_float(deep_get(case, ["plasma", "H98"]), 1.0) or 1.0
    greenwald = finite_float(deep_get(case, ["plasma", "greenwald_fraction"]), 0.8) or 0.8
    betaN = finite_float(deep_get(case, ["plasma", "target_betaN"]), 2.5) or 2.5
    tct = finite_float(deep_get(case, ["tct_translation", "control_strength"]), 0.0) or 0.0
    li_current = finite_float(deep_get(case, ["wall", "lithium_current_proxy"]), 0.0) or 0.0
    li_thickness = finite_float(deep_get(case, ["wall", "lithium_thickness_m"]), 0.0014) or 0.0014

    # Basic plasma estimates.  These are intentionally conservative and monotonic.
    density_20 = max(0.05, greenwald * Ip / (math.pi * a * a))
    Ti_keV = max(4.0, 9.0 + 1.7 * (H98 - 1.0) + 0.20 * (B0 - 5.0))
    Te_keV = max(3.0, 0.92 * Ti_keV)
    tau_E = max(0.05, 0.34 * H98 * (R / 5.5) ** 1.3 * (a / 1.8) ** 0.5 * (B0 / 7.2) ** 0.15)

    # TCT/li-current suppression terms.  Lithium current helps at low/moderate
    # values but overcoupling is penalized later through severity.
    tct_suppression = min(0.60, 0.48 * tct)
    li_suppression = min(0.20, 1.20 * li_current)
    event_severity = max(0.02, 0.62 * (1.0 - tct_suppression - li_suppression))
    r_less_than_1 = max(0.0, min(1.0, 0.34 * event_severity + 0.07 * max(0.0, betaN - 2.5)))

    volume_m3 = 2.0 * math.pi * math.pi * R * a * a
    reactivity_shape = max(0.15, (Ti_keV / 10.0) ** 2.15 * math.exp(-0.30 * abs(Ti_keV - 14.0)))
    confinement_shape = max(0.2, tau_E / 0.34)
    stability_shape = max(0.25, 1.0 - 0.55 * event_severity)

    # Calibrated to give reactor-scale but not absurd values for the frozen target.
    Pfus = 185.0 * (density_20 / 1.35) ** 2 * (volume_m3 / 352.0) * reactivity_shape * confinement_shape * stability_shape
    Pfus = max(0.0, Pfus)

    neutron_power = DT_NEUTRON_FRACTION * Pfus
    alpha_power = DT_ALPHA_FRACTION * Pfus

    # Blanket attenuation improves with Li thickness and Be outer topology.
    topology = str(case.get("blanket_topology", ""))
    topology_bonus = 0.08 if "be_outer" in topology else 0.0
    attenuation = max(0.35, min(0.92, 0.58 + topology_bonus + 32.0 * li_thickness + 0.08 * tct))
    blanket_heat = neutron_power * attenuation + alpha_power * 0.15

    wall_area = A_FW_M2_DEFAULT
    wall_loading = neutron_power / wall_area if wall_area > 0 else float("nan")

    # TBR proxy rewards Li thickness and Be topology, penalizes excessive wall loading.
    TBR = 0.92 + 72.0 * li_thickness + topology_bonus + 0.05 * min(tct, 1.0) - 0.015 * max(0.0, wall_loading - 3.0)
    TBR = max(0.0, TBR)

    Paux = max(20.0, 72.0 / max(H98, 0.3) + 18.0 * event_severity + 12.0 * r_less_than_1)
    Q = Pfus / Paux if Paux > 0 else float("nan")
    Pnet = blanket_heat + alpha_power * 0.35 - Paux - 25.0 * event_severity

    return {
        "Te_keV": Te_keV,
        "Ti_keV": Ti_keV,
        "density_20_m3": density_20,
        "tau_E_s": tau_E,
        "Pfus_MW": Pfus,
        "alpha_power_MW": alpha_power,
        "neutron_power_MW": neutron_power,
        "blanket_heat_MW": blanket_heat,
        "wall_loading_MW_m2": wall_loading,
        "TBR": TBR,
        "Q": Q,
        "Paux_MW": Paux,
        "Pnet_MW": Pnet,
        "attenuation": attenuation,
        "event_severity_mean": event_severity,
        "R_less_than_1_fraction": r_less_than_1,
    }


def backend_or_proxy_physics(case: Dict[str, Any], backend_payload: Optional[Dict[str, Any]]) -> tuple[str, int, Dict[str, float]]:
    if backend_payload is None:
        return "proxy", 0, proxy_physics(case)

    backend_code = int(finite_float(backend_payload.get("backend_returncode"), 0) or 0)
    fields = proxy_physics(case)
    used_real = False
    for key in list(fields):
        val = finite_float(backend_payload.get(key), None)
        if val is not None:
            fields[key] = val
            used_real = True

    source = "backend_json" if used_real else "backend_json_no_physics"
    return source, backend_code, fields


def evaluate_constraints(fields: Dict[str, float], betaN: float, greenwald: float) -> tuple[bool, List[str]]:
    reasons: List[str] = []
    if betaN > MAX_BETAN:
        reasons.append(f"betaN>{MAX_BETAN}")
    if greenwald > MAX_GREENWALD_FRACTION:
        reasons.append(f"greenwald_fraction>{MAX_GREENWALD_FRACTION}")
    if fields["wall_loading_MW_m2"] > MAX_NEUTRON_WALL_LOADING_MW_M2:
        reasons.append(f"wall_loading>{MAX_NEUTRON_WALL_LOADING_MW_M2}")
    if fields["TBR"] < MIN_TBR:
        reasons.append(f"TBR<{MIN_TBR}")
    if fields["Pnet_MW"] < MIN_PNET_MW:
        reasons.append(f"Pnet<{MIN_PNET_MW}")
    if fields["Pfus_MW"] <= 0:
        reasons.append("Pfus<=0")
    return not reasons, reasons


def score(fields: Dict[str, float], passed: bool) -> float:
    if not passed:
        return 0.0
    return max(
        0.0,
        fields["Pnet_MW"] / 1000.0
        + 0.35 * max(0.0, fields["TBR"] - 1.0)
        - 0.22 * fields["event_severity_mean"]
        - 0.18 * fields["R_less_than_1_fraction"]
        - 0.06 * max(0.0, fields["wall_loading_MW_m2"] - 2.5),
    )


def evaluate_case(case: Dict[str, Any], backend_dir: Optional[Path]) -> PhysicsResult:
    case_name = str(case.get("case_name", case.get("candidate_name", "case")))
    candidate_id = str(case.get("candidate_name", "candidate0"))

    backend_payload = extract_backend_json(case, backend_dir)
    backend_source, backend_returncode, fields = backend_or_proxy_physics(case, backend_payload)

    topology = str(case.get("blanket_topology", "unknown"))
    ordering = "/".join(case.get("blanket_ordering", [])) if isinstance(case.get("blanket_ordering"), list) else str(case.get("blanket_ordering", "unspecified"))
    tct_mode = str(deep_get(case, ["tct_translation", "mode"], "unknown"))
    tct_strength = finite_float(deep_get(case, ["tct_translation", "control_strength"]), 0.0) or 0.0
    li_current = finite_float(deep_get(case, ["wall", "lithium_current_proxy"]), 0.0) or 0.0
    severity_scale = finite_float(case.get("severity_scale"), 0.6) or 0.6
    lithium_thickness = finite_float(deep_get(case, ["wall", "lithium_thickness_m"]), 0.0) or 0.0
    R = finite_float(deep_get(case, ["reactor", "R_m"]), 0.0) or 0.0
    a = finite_float(deep_get(case, ["reactor", "a_m"]), 0.0) or 0.0
    B0 = finite_float(deep_get(case, ["reactor", "B0_T"]), 0.0) or 0.0
    Ip = finite_float(deep_get(case, ["reactor", "Ip_MA"]), 0.0) or 0.0
    H98 = finite_float(deep_get(case, ["plasma", "H98"]), 0.0) or 0.0
    greenwald = finite_float(deep_get(case, ["plasma", "greenwald_fraction"]), 0.0) or 0.0
    betaN = finite_float(deep_get(case, ["plasma", "target_betaN"]), 0.0) or 0.0

    if backend_returncode != 0:
        passed = False
        status = "backend_failed"
        failure_reason = f"backend_returncode={backend_returncode}"
    elif backend_source == "backend_json_no_physics":
        passed = False
        status = "empty_plasma_state"
        failure_reason = "backend diagnostics existed but contained no recognized physics fields"
    else:
        passed, reasons = evaluate_constraints(fields, betaN, greenwald)
        status = "ok" if passed else "constraints_failed"
        failure_reason = ";".join(reasons)

    result_score = score(fields, passed)
    return PhysicsResult(
        candidate_id=candidate_id,
        case_name=case_name,
        status=status,
        failure_reason=failure_reason,
        backend_source=backend_source,
        backend_returncode=backend_returncode,
        passed_hard_constraints=passed,
        blanket_topology=topology,
        blanket_ordering=ordering,
        tct_mode=tct_mode,
        tct_strength=tct_strength,
        li_current=li_current,
        severity_scale=severity_scale,
        lithium_thickness_m=lithium_thickness,
        R_m=R,
        a_m=a,
        B0_T=B0,
        Ip_MA=Ip,
        H98=H98,
        greenwald_fraction=greenwald,
        betaN=betaN,
        Te_keV=fields["Te_keV"],
        Ti_keV=fields["Ti_keV"],
        density_20_m3=fields["density_20_m3"],
        tau_E_s=fields["tau_E_s"],
        Pfus_MW=fields["Pfus_MW"],
        alpha_power_MW=fields["alpha_power_MW"],
        neutron_power_MW=fields["neutron_power_MW"],
        blanket_heat_MW=fields["blanket_heat_MW"],
        wall_loading_MW_m2=fields["wall_loading_MW_m2"],
        TBR=fields["TBR"],
        Q=fields["Q"],
        Paux_MW=fields["Paux_MW"],
        Pnet_MW=fields["Pnet_MW"],
        attenuation=fields["attenuation"],
        event_severity_mean=fields["event_severity_mean"],
        R_less_than_1_fraction=fields["R_less_than_1_fraction"],
        score=result_score,
    )


def write_results(results: List[PhysicsResult], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [asdict(r) for r in results]
    with output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the M3D-C1 validation physics harness.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASE_MATRIX)
    parser.add_argument("--backend-dir", type=Path, default=None, help="Optional directory containing backend diagnostics JSON files")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    cases = load_cases(args.cases)
    results = [evaluate_case(case, args.backend_dir) for case in cases]
    write_results(results, args.out)

    print(f"Evaluated {len(results)} cases")
    print(f"Wrote {args.out}")
    for r in sorted(results, key=lambda x: x.score, reverse=True):
        print(
            f"{r.case_name:28s} status={r.status:18s} "
            f"score={r.score:.4f} Pfus={r.Pfus_MW:.1f}MW "
            f"Pnet={r.Pnet_MW:.1f}MW TBR={r.TBR:.3f} "
            f"severity={r.event_severity_mean:.3f} source={r.backend_source}"
        )


if __name__ == "__main__":
    main()
