#!/usr/bin/env python3
"""
Fusion candidate sweep runner.

Two backends are supported:
  - `m3dc1`: run the local M3DC1 case directory and scrape real diagnostics
  - `external`: invoke an arbitrary backend command template that emits JSON

The M3DC1 adapter only applies controls that actually exist in this repo:
  - `li_current` -> `current.dat` scale
  - `tct_alpha`/`tct_mode` -> GS feedback gain scale
  - `severity_scale` -> `eps`
  - `lithium_thickness_m` -> `pedge`

Blanket ordering/topology are retained in the candidate metadata, but they are
not active M3DC1 inputs, so they are dropped from the sweep dimensions.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import math
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
M3DC1_TEMPLATE_DIR = ROOT / "unstructured" / "runs" / "first_linear"
M3DC1_BIN = ROOT / "unstructured" / "_localgnu-petsc-opt-25" / "m3dc1_2d"


def finite_or_none(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    if math.isfinite(x):
        return x
    return None


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if math.isfinite(value):
            return f"{value:.8g}"
        return ""
    return str(value)


def sort_value(value: Optional[float], *, default: float) -> float:
    if value is None:
        return default
    return value


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "item"


@dataclasses.dataclass(frozen=True)
class Candidate:
    candidate_id: str
    family: str
    li_current: float = 0.10
    tct_mode: str = "aggressive"
    tct_alpha: float = 10.0
    severity_scale: float = 0.6
    lithium_thickness_m: float = 0.003
    blanket_topology: str = "be_outer_kill"
    blanket_ordering: str = "Be/Li2O/Li2O/W_Ti_B4C_60_30_10_wt/Be"
    blanket_split: str = "0.15/0.20/0.40/0.15/0.10"
    blanket_thickness_m: float = 1.25
    R_m: float = 0.55
    a_m: float = 0.55
    severity_supervisor: str = "aggressive"

    def to_payload(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class EvaluationResult:
    candidate_id: str
    family: str
    params: Dict[str, Any]
    metrics: Dict[str, Optional[float]]
    failure_reason: str = ""
    raw_backend_stdout: str = ""
    raw_backend_stderr: str = ""
    backend_returncode: Optional[int] = None

    @property
    def passed_hard_constraints(self) -> bool:
        beta_n = self.metrics.get("betaN")
        neutron = self.metrics.get("neutron_wall_load_MW_m2")
        pnet = self.metrics.get("Pnet_MW")
        tbr = self.metrics.get("TBR")
        if beta_n is not None and beta_n > 2.5:
            return False
        if neutron is not None and neutron > 4.0:
            return False
        if pnet is not None and pnet <= 0.0:
            return False
        if tbr is not None and tbr < 1.05:
            return False
        return self.failure_reason == ""

    @property
    def score(self) -> Optional[float]:
        if self.failure_reason:
            return None
        pnet = self.metrics.get("Pnet_MW")
        if pnet is None:
            return None
        tbr = self.metrics.get("TBR")
        tbr_proxy = self.metrics.get("TBR_proxy")
        severity_mean = self.metrics.get("event_severity_mean")
        severity_max = self.metrics.get("event_severity_max")
        neutron = self.metrics.get("neutron_wall_load_MW_m2")
        tct = self.metrics.get("TCT_duty_fraction")
        q = self.metrics.get("Q")
        blanket_heat = self.metrics.get("blanket_heat_MW")

        tbr_term = tbr if tbr is not None else tbr_proxy
        severity_term = severity_mean if severity_mean is not None else severity_max
        score = 0.0
        score += 2.0 * pnet
        if tbr_term is not None:
            score += 500.0 * (tbr_term - 1.0)
        if severity_term is not None:
            score -= 200.0 * severity_term
        if neutron is not None:
            score -= 25.0 * neutron
        if tct is not None:
            score -= 100.0 * tct
        if q is not None and q >= 2.0:
            score += 50.0
        if blanket_heat is not None:
            score += 0.05 * blanket_heat
        return score

    def row(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "candidate_id": self.candidate_id,
            "family": self.family,
            **self.params,
            **self.metrics,
            "failure_reason": self.failure_reason,
            "candidate_score": self.score,
            "passed_hard_constraints": self.passed_hard_constraints,
            "backend_returncode": self.backend_returncode,
        }
        return out


def frozen_candidate() -> Candidate:
    return Candidate(
        candidate_id="frozen_candidate",
        family="baseline",
    )


def _scale_feedback_line(line: str, scale: float) -> str:
    if "=" not in line:
        return line
    lhs, rhs = line.split("=", 1)
    key = lhs.strip()
    if not key.startswith(
        (
            "gs_vertical_feedback",
            "gs_vertical_feedback_i",
            "gs_radial_feedback",
            "gs_radial_feedback_i",
        )
    ):
        return line
    try:
        value = float(rhs.split("!", 1)[0].strip())
    except ValueError:
        return line
    comment = ""
    if "!" in rhs:
        comment = "!" + rhs.split("!", 1)[1]
    return f"{lhs} = {value * scale:.12g} {comment}".rstrip()


def _replace_assignment(lines: Sequence[str], key: str, value: str, comment: str) -> List[str]:
    out: List[str] = []
    matched = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key} ="):
            out.append(f"\t{key} = {value}\t! {comment}")
            matched = True
        else:
            out.append(line)
    if not matched:
        out.append(f"\t{key} = {value}\t! {comment}")
    return out


def apply_m3dc1_mapping(candidate: Candidate, case_dir: Path, quick_init: bool) -> Dict[str, Any]:
    """Apply the candidate knobs to a copied first_linear case."""
    input_path = case_dir / "C1input.smoke"
    lines = input_path.read_text(encoding="utf-8").splitlines()

    li_scale = 1.0 + (candidate.li_current - 0.10)
    mode_scale = {"disabled": 0.0, "mild": 0.5, "aggressive": 1.0}.get(candidate.tct_mode, 1.0)
    feedback_scale = mode_scale * (candidate.tct_alpha / 10.0)
    eps_value = 0.0 if quick_init else 1e-8 * (candidate.severity_scale / 0.6)
    pedge_value = 2e-4 * (candidate.lithium_thickness_m / 0.003)

    updated: List[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("linear ="):
            updated.append("\tlinear = 0\t! run the nonlinear path for meaningful native diagnostics")
            continue
        if stripped.startswith("eqsubtract ="):
            updated.append("\teqsubtract = 0\t! keep equilibrium terms in the nonlinear run")
            continue
        if stripped.startswith("eps ="):
            updated.append(f"\teps = {eps_value:.12g}\t! amplitude of initial random perturbations")
            continue
        if stripped.startswith("icalc_scalars ="):
            updated.append("\ticalc_scalars = 1\t! keep scalar diagnostics enabled for sweep runs")
            continue
        if stripped.startswith("pedge ="):
            updated.append(f"\tpedge = {pedge_value:.12g}\t! mapped from lithium_thickness_m")
            continue
        if stripped.startswith("gs_vertical_feedback(") or stripped.startswith("gs_vertical_feedback_i(") or stripped.startswith("gs_radial_feedback(") or stripped.startswith("gs_radial_feedback_i("):
            updated.append(_scale_feedback_line(line, feedback_scale))
            continue
        updated.append(line)
    input_path.write_text("\n".join(updated) + "\n", encoding="utf-8")

    current_path = case_dir / "current.dat"
    current_lines: List[str] = []
    for raw in current_path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped:
            current_lines.append(raw)
            continue
        try:
            value = float(stripped.split()[0])
        except ValueError:
            current_lines.append(raw)
            continue
        current_lines.append(f"{value * li_scale:12.6f}")
    current_path.write_text("\n".join(current_lines) + "\n", encoding="utf-8")

    return {
        "m3dc1_applied": True,
        "li_scale": li_scale,
        "feedback_scale": feedback_scale,
        "eps": eps_value,
        "pedge": pedge_value,
        "blanket_ordering_applied": False,
        "blanket_topology_applied": False,
    }


def parse_m3dc1_log(log_text: str) -> Dict[str, Optional[float]]:
    metrics: Dict[str, Optional[float]] = {
        "total_energy": None,
        "total_energy_lost": None,
        "toroidal_current": None,
        "toroidal_flux": None,
        "area": None,
        "volume": None,
        "total_particles": None,
        "total_radiation": None,
        "line_radiation": None,
        "bremsstrahlung_radiation": None,
        "ionization_loss": None,
        "recombination_radiation_kinetic": None,
        "recombination_radiation_potential": None,
        "psi0": None,
        "te_max": None,
    }
    for line in log_text.splitlines():
        if "Total energy =" in line:
            vals = [finite_or_none(x) for x in re.findall(r"[-+]?\d+\.\d+(?:[Ee][-+]?\d+)?", line)]
            if vals:
                metrics["total_energy"] = vals[0]
        elif "Total energy lost =" in line:
            vals = [finite_or_none(x) for x in re.findall(r"[-+]?\d+\.\d+(?:[Ee][-+]?\d+)?", line)]
            if vals:
                metrics["total_energy_lost"] = vals[0]
        elif "Toroidal current =" in line:
            vals = [finite_or_none(x) for x in re.findall(r"[-+]?\d+\.\d+(?:[Ee][-+]?\d+)?", line)]
            if vals:
                metrics["toroidal_current"] = vals[0]
        elif "Toroidal flux =" in line:
            vals = [finite_or_none(x) for x in re.findall(r"[-+]?\d+\.\d+(?:[Ee][-+]?\d+)?", line)]
            if vals:
                metrics["toroidal_flux"] = vals[0]
        elif "Total particles =" in line:
            vals = [finite_or_none(x) for x in re.findall(r"[-+]?\d+\.\d+(?:[Ee][-+]?\d+)?", line)]
            if vals:
                metrics["total_particles"] = vals[0]
        elif "Total radiation =" in line:
            vals = [finite_or_none(x) for x in re.findall(r"[-+]?\d+\.\d+(?:[Ee][-+]?\d+)?", line)]
            if vals:
                metrics["total_radiation"] = vals[0]
        elif "Line radiation =" in line:
            vals = [finite_or_none(x) for x in re.findall(r"[-+]?\d+\.\d+(?:[Ee][-+]?\d+)?", line)]
            if vals:
                metrics["line_radiation"] = vals[0]
        elif "Bremsstrahlung radiation =" in line:
            vals = [finite_or_none(x) for x in re.findall(r"[-+]?\d+\.\d+(?:[Ee][-+]?\d+)?", line)]
            if vals:
                metrics["bremsstrahlung_radiation"] = vals[0]
        elif "Ionization loss =" in line:
            vals = [finite_or_none(x) for x in re.findall(r"[-+]?\d+\.\d+(?:[Ee][-+]?\d+)?", line)]
            if vals:
                metrics["ionization_loss"] = vals[0]
        elif "Recombination radiation (kinetic) =" in line:
            vals = [finite_or_none(x) for x in re.findall(r"[-+]?\d+\.\d+(?:[Ee][-+]?\d+)?", line)]
            if vals:
                metrics["recombination_radiation_kinetic"] = vals[0]
        elif "Recombination radiation (potential) =" in line:
            vals = [finite_or_none(x) for x in re.findall(r"[-+]?\d+\.\d+(?:[Ee][-+]?\d+)?", line)]
            if vals:
                metrics["recombination_radiation_potential"] = vals[0]
        elif "max te" in line:
            vals = [finite_or_none(x) for x in re.findall(r"[-+]?\d+\.\d+(?:[Ee][-+]?\d+)?", line)]
            if vals:
                metrics["te_max"] = vals[0]
        elif "psi0" in line.lower():
            vals = [finite_or_none(x) for x in re.findall(r"[-+]?\d+\.\d+(?:[Ee][-+]?\d+)?", line)]
            if vals:
                metrics["psi0"] = vals[0]
    return metrics


def run_m3dc1_local(candidate: Candidate, results_dir: Path, keep_logs: bool, quick_init: bool) -> EvaluationResult:
    import shutil

    run_root = results_dir / "runs"
    run_root.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix=f"{candidate.candidate_id}_", dir=str(run_root)))
    shutil.copytree(M3DC1_TEMPLATE_DIR, run_dir, dirs_exist_ok=True)
    applied = apply_m3dc1_mapping(candidate, run_dir, quick_init=quick_init)
    log_path = run_dir / "run.log"
    proc = subprocess.run(
        ["/bin/bash", "./run.sh"],
        cwd=str(run_dir),
        env={
            **os.environ,
            "M3DC1_BIN": str(M3DC1_BIN),
            "INPUT": "C1input.smoke",
            "LOG": "run.log",
            "NPROC": "1",
        },
        capture_output=True,
        text=True,
    )
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    log_text = ""
    if log_path.exists():
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
    metrics = parse_m3dc1_log(log_text)
    failure_reason = ""
    if proc.returncode != 0:
        failure_reason = f"m3dc1 exited {proc.returncode}"
    result = EvaluationResult(
        candidate_id=candidate.candidate_id,
        family=candidate.family,
        params={**candidate.to_payload(), **applied},
        metrics=metrics,
        failure_reason=failure_reason,
        raw_backend_stdout=stdout,
        raw_backend_stderr=stderr,
        backend_returncode=proc.returncode,
    )
    if not keep_logs:
        shutil.rmtree(run_dir, ignore_errors=True)
    return result


def build_grid(mode: str) -> List[Candidate]:
    base = frozen_candidate()
    rows: List[Candidate] = [base]

    if mode == "smoke":
        rows.append(dataclasses.replace(base, candidate_id="li_current_0p05", family="li_current", li_current=0.05))
        return rows

    li_values = [0.00, 0.05, 0.08, 0.10, 0.12, 0.15, 0.20]
    for value in li_values:
        rows.append(
            dataclasses.replace(
                base,
                candidate_id=f"li_current_{str(value).replace('.', 'p')}",
                family="li_current",
                li_current=value,
            )
        )

    tct_modes = ["disabled", "mild", "aggressive"]
    tct_alphas = [8, 9, 10, 11, 12]
    for mode_name in tct_modes:
        for alpha in tct_alphas:
            rows.append(
                dataclasses.replace(
                    base,
                    candidate_id=f"tct_{slugify(mode_name)}_{alpha}",
                    family="tct",
                    tct_mode=mode_name,
                    tct_alpha=float(alpha),
                    severity_supervisor=mode_name,
                )
            )

    severity_values = [0.4, 0.5, 0.6, 0.7, 0.8]
    for value in severity_values:
        rows.append(
            dataclasses.replace(
                base,
                candidate_id=f"severity_{str(value).replace('.', 'p')}",
                family="severity_scale",
                severity_scale=value,
            )
        )

    lithium_values = [0.001, 0.002, 0.003, 0.005, 0.010]
    for value in lithium_values:
        rows.append(
            dataclasses.replace(
                base,
                candidate_id=f"lithium_{str(value).replace('.', 'p')}",
                family="lithium_thickness",
                lithium_thickness_m=value,
            )
        )

    return rows


def backend_template_values(workdir: Path, run_dir: Path, candidate: Candidate, candidate_json: Path, result_json: Path) -> Dict[str, str]:
    return {
        "workdir": str(workdir),
        "run_dir": str(run_dir),
        "candidate_json": str(candidate_json),
        "result_json": str(result_json),
        "candidate_id": candidate.candidate_id,
    }


def run_backend(
    backend_cmd: str,
    workdir: Path,
    run_dir: Path,
    candidate: Candidate,
    keep_logs: bool,
) -> EvaluationResult:
    run_dir.mkdir(parents=True, exist_ok=True)
    candidate_json = run_dir / "candidate.json"
    result_json = run_dir / "result.json"
    candidate_json.write_text(json.dumps(candidate.to_payload(), indent=2) + "\n", encoding="utf-8")

    fmt = backend_template_values(workdir, run_dir, candidate, candidate_json, result_json)
    command = backend_cmd.format(**fmt)
    argv = shlex.split(command)

    proc = subprocess.run(
        argv,
        cwd=str(workdir),
        capture_output=True,
        text=True,
    )

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""

    result_payload: Dict[str, Any] = {}
    if result_json.exists():
        try:
            result_payload = json.loads(result_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            result_payload = {}
    elif stdout.strip():
        try:
            result_payload = json.loads(stdout)
        except json.JSONDecodeError:
            result_payload = {}

    metrics: Dict[str, Optional[float]] = {}
    aliases = {
        "Pfus_MW": ["Pfus_MW", "Pfus", "pfus_mw"],
        "Pnet_MW": ["Pnet_MW", "Pnet", "pnet_mw"],
        "Ploss_MW": ["Ploss_MW", "Ploss", "ploss_mw"],
        "Q": ["Q", "q"],
        "betaN": ["betaN", "beta_n", "betan"],
        "neutron_wall_load_MW_m2": ["neutron_wall_load_MW_m2", "neutron_wall_load", "wall_load"],
        "TBR": ["TBR", "tbr"],
        "TBR_proxy": ["TBR_proxy", "tbr_proxy"],
        "front_flux": ["front_flux"],
        "blanket_heat_MW": ["blanket_heat_MW", "blanket_heat"],
        "attenuation": ["attenuation"],
        "event_severity_mean": ["event_severity_mean"],
        "event_severity_max": ["event_severity_max"],
        "R_less_than_1_fraction": ["R_less_than_1_fraction"],
        "TCT_duty_fraction": ["TCT_duty_fraction", "tct_duty_fraction"],
    }
    for canonical, keys in aliases.items():
        value = None
        for key in keys:
            if key in result_payload:
                value = finite_or_none(result_payload.get(key))
                break
        metrics[canonical] = value

    failure_reason = ""
    if proc.returncode != 0:
        failure_reason = str(result_payload.get("failure_reason") or result_payload.get("error") or f"backend exited {proc.returncode}")
    elif result_payload.get("failure_reason"):
        failure_reason = str(result_payload["failure_reason"])

    if not keep_logs:
        for path in (candidate_json, result_json):
            if path.exists():
                path.unlink()

    return EvaluationResult(
        candidate_id=candidate.candidate_id,
        family=candidate.family,
        params=candidate.to_payload(),
        metrics=metrics,
        failure_reason=failure_reason,
        raw_backend_stdout=stdout,
        raw_backend_stderr=stderr,
        backend_returncode=proc.returncode,
    )


def rank_results(results: Sequence[EvaluationResult]) -> List[EvaluationResult]:
    return sorted(
        results,
        key=lambda r: (
            not r.passed_hard_constraints,
            -sort_value(r.score, default=float("-inf")),
            -sort_value(r.metrics.get("Pnet_MW"), default=float("-inf")),
            -sort_value(
                r.metrics.get("TBR") if r.metrics.get("TBR") is not None else r.metrics.get("TBR_proxy"),
                default=float("-inf"),
            ),
            sort_value(r.metrics.get("neutron_wall_load_MW_m2"), default=float("inf")),
            sort_value(r.metrics.get("event_severity_mean"), default=float("inf")),
            sort_value(r.metrics.get("TCT_duty_fraction"), default=float("inf")),
        ),
    )


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: List[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: csv_value(row.get(k)) for k in fieldnames})


def maybe_make_plots(results: Sequence[EvaluationResult], out_dir: Path) -> List[Path]:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return []

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []

    def savefig(name: str) -> Path:
        path = out_dir / name
        plt.tight_layout()
        plt.savefig(path, dpi=160)
        plt.close()
        paths.append(path)
        return path

    li_points = [
        (r.params.get("li_current"), r.metrics.get("Pnet_MW"))
        for r in results
        if r.family == "li_current" and r.params.get("li_current") is not None and r.metrics.get("Pnet_MW") is not None
    ]
    if li_points:
        xs, ys = zip(*sorted(li_points, key=lambda x: x[0]))
        plt.figure(figsize=(7, 4))
        plt.plot(xs, ys, marker="o")
        plt.xlabel("li_current")
        plt.ylabel("Pnet_MW")
        plt.title("Pnet vs li_current")
        savefig("pnet_vs_li_current.png")

    thickness_points = [
        (r.params.get("lithium_thickness_m"), r.metrics.get("TBR") or r.metrics.get("TBR_proxy"))
        for r in results
        if r.family == "lithium_thickness"
        and r.params.get("lithium_thickness_m") is not None
        and (r.metrics.get("TBR") is not None or r.metrics.get("TBR_proxy") is not None)
    ]
    if thickness_points:
        xs, ys = zip(*sorted(thickness_points, key=lambda x: x[0]))
        plt.figure(figsize=(7, 4))
        plt.plot(xs, ys, marker="o")
        plt.xlabel("lithium_thickness_m")
        plt.ylabel("TBR / TBR_proxy")
        plt.title("TBR vs lithium thickness")
        savefig("tbr_vs_lithium_thickness.png")

    tct_points = [
        (r.params.get("tct_alpha"), r.metrics.get("event_severity_mean"))
        for r in results
        if r.family == "tct" and r.params.get("tct_alpha") is not None and r.metrics.get("event_severity_mean") is not None
    ]
    if tct_points:
        xs, ys = zip(*sorted(tct_points, key=lambda x: x[0]))
        plt.figure(figsize=(7, 4))
        plt.plot(xs, ys, marker="o")
        plt.xlabel("TCT alpha")
        plt.ylabel("event_severity_mean")
        plt.title("Event severity vs TCT alpha")
        savefig("severity_vs_tct_alpha.png")

    ranked = rank_results(results)[:20]
    ranked = [r for r in ranked if r.score is not None]
    if ranked:
        labels = [r.candidate_id for r in ranked]
        values = [r.score for r in ranked if r.score is not None]
        plt.figure(figsize=(10, 5))
        plt.bar(range(len(values)), values)
        plt.xticks(range(len(values)), labels, rotation=60, ha="right", fontsize=8)
        plt.ylabel("candidate_score")
        plt.title("Top 20 candidates")
        savefig("candidate_score_top20.png")

    return paths


def summarize(results: Sequence[EvaluationResult]) -> Tuple[str, List[str]]:
    ranked = rank_results(results)
    viable = [r for r in ranked if r.passed_hard_constraints and r.score is not None]
    frozen = next((r for r in results if r.candidate_id == "frozen_candidate"), None)
    lines: List[str] = []
    if viable:
        best = viable[0]
        lines.append(f"Best viable candidate: `{best.candidate_id}`")
        lines.append(f"- family: `{best.family}`")
        lines.append(f"- score: `{best.score:.4g}`")
        for key in ["Pnet_MW", "TBR", "TBR_proxy", "betaN", "neutron_wall_load_MW_m2", "event_severity_mean", "event_severity_max", "TCT_duty_fraction"]:
            val = best.metrics.get(key)
            if val is not None:
                lines.append(f"- {key}: `{val:.6g}`")
    else:
        lines.append("No viable candidate satisfied the available hard constraints.")

    if frozen and frozen.score is not None:
        lines.append("")
        lines.append("Frozen candidate:")
        lines.append(f"- score: `{frozen.score:.4g}`")
        if viable and viable[0].score is not None:
            delta = viable[0].score - frozen.score
            lines.append(f"- score delta vs best: `{delta:.4g}`")
        for key in ["Pnet_MW", "TBR", "TBR_proxy", "betaN", "neutron_wall_load_MW_m2", "event_severity_mean", "event_severity_max"]:
            val = frozen.metrics.get(key)
            if val is not None:
                lines.append(f"- {key}: `{val:.6g}`")
    elif frozen:
        lines.append("")
        lines.append("Frozen candidate has no score because backend metrics were incomplete.")
    return ("\n".join(lines), lines)


def write_report(path: Path, results: Sequence[EvaluationResult], plot_paths: Sequence[Path], mode: str, backend_cmd: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary_text, summary_lines = summarize(results)
    total = len(results)
    succeeded = sum(1 for r in results if not r.failure_reason and r.backend_returncode == 0)
    viable = sum(1 for r in results if r.passed_hard_constraints and r.score is not None)
    failed = total - succeeded
    families = sorted({r.family for r in results})
    failed_reasons: Dict[str, int] = {}
    for r in results:
        if r.failure_reason:
            failed_reasons[r.failure_reason] = failed_reasons.get(r.failure_reason, 0) + 1

    lines = [
        "# mc3-d1 fusion sweep report",
        "",
        f"- mode: `{mode}`",
        f"- backend_cmd: `{backend_cmd}`",
        f"- candidates: `{total}`",
        f"- backend success count: `{succeeded}`",
        f"- viable count: `{viable}`",
        f"- failed count: `{failed}`",
        f"- families: `{', '.join(families)}`",
        "",
        "## Summary",
        summary_text,
        "",
        "## Failure Modes",
    ]
    if failed_reasons:
        for reason, count in sorted(failed_reasons.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Plots",
        ]
    )
    if plot_paths:
        for p in plot_paths:
            lines.append(f"- [{p.name}]({p.name})")
    else:
        lines.append("- none generated")
    lines.extend(
        [
            "",
            "## Notes",
            "- Missing backend metrics are left blank in CSV output.",
            "- Hard constraints are evaluated only when the corresponding metric is available.",
            "- If the backend does not expose a real TBR, the script preserves the `TBR_proxy` column when provided.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run a fusion candidate sweep through M3DC1 or an external backend.")
    parser.add_argument("--mode", choices=["smoke", "full"], default="smoke", help="Quick smoke run or full sweep.")
    parser.add_argument("--engine", choices=["m3dc1", "external"], default="m3dc1", help="Use the local M3DC1 adapter or an external JSON backend.")
    parser.add_argument("--backend-cmd", default=os.environ.get("MC3D1_BACKEND_CMD", ""), help="Backend command template. Use {candidate_json}, {result_json}, {run_dir}, {workdir}, {candidate_id}.")
    parser.add_argument("--results-dir", default=str(RESULTS_DIR), help="Directory for CSVs, report, and plots.")
    parser.add_argument("--keep-run-artifacts", action="store_true", help="Keep per-candidate JSON payloads and backend outputs.")
    parser.add_argument("--no-plots", action="store_true", help="Disable plot generation.")
    parser.add_argument("--max-candidates", type=int, default=0, help="Limit the sweep to the first N candidates after grid construction.")
    parser.add_argument("--validate-only", action="store_true", help="Only validate the planned sweep and exit without running the backend.")
    args = parser.parse_args(argv)

    results_dir = Path(args.results_dir).expanduser().resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    candidates = build_grid(args.mode)
    if args.max_candidates and args.max_candidates > 0:
        candidates = candidates[: args.max_candidates]
    if args.validate_only:
        print(f"mode={args.mode}")
        print(f"candidates={len(candidates)}")
        print(f"results_dir={results_dir}")
        for c in candidates:
            print(json.dumps(c.to_payload(), sort_keys=True))
        return 0

    if args.engine == "external" and not args.backend_cmd:
        print(
            "Error: no backend command was supplied. Set MC3D1_BACKEND_CMD or pass --backend-cmd.\n"
            "This repository currently does not contain a callable external fusion evaluator.",
            file=sys.stderr,
        )
        return 2

    results: List[EvaluationResult] = []
    for candidate in candidates:
        if args.engine == "m3dc1":
            result = run_m3dc1_local(candidate, results_dir, args.keep_run_artifacts, quick_init=(args.mode == "smoke"))
        else:
            run_root = results_dir / "runs"
            run_root.mkdir(parents=True, exist_ok=True)
            run_dir = run_root / candidate.candidate_id
            result = run_backend(
                backend_cmd=args.backend_cmd,
                workdir=ROOT,
                run_dir=run_dir,
                candidate=candidate,
                keep_logs=args.keep_run_artifacts,
            )
        results.append(result)
        print(
            f"[{candidate.candidate_id}] "
            f"score={csv_value(result.score)} "
            f"Pnet={csv_value(result.metrics.get('Pnet_MW'))} "
            f"TBR={csv_value(result.metrics.get('TBR') if result.metrics.get('TBR') is not None else result.metrics.get('TBR_proxy'))} "
            f"status={'ok' if not result.failure_reason else result.failure_reason}",
            flush=True,
        )

    raw_rows = [r.row() for r in results]
    write_csv(results_dir / "mc3d1_fusion_sweep_raw.csv", raw_rows)
    ranked_rows = [r.row() for r in rank_results(results) if r.passed_hard_constraints and r.score is not None]
    write_csv(results_dir / "mc3d1_fusion_sweep_ranked.csv", ranked_rows)

    plot_paths: List[Path] = []
    if not args.no_plots:
        plot_paths = maybe_make_plots(results, results_dir / "plots")

    write_report(
        results_dir / "mc3d1_fusion_sweep_report.md",
        results=results,
        plot_paths=plot_paths,
        mode=args.mode,
        backend_cmd=args.engine if args.engine == "m3dc1" else args.backend_cmd,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
