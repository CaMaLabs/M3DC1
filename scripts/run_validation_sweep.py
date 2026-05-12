#!/usr/bin/env python3
"""
M3DC1 Validation Sweep Runner

This script orchestrates the full validation pipeline:
1. Load candidate configuration
2. Generate case matrix
3. For each case:
   - Run M3D-C1 backend (or use dummy output)
   - Extract physics outputs
   - Score candidate
   - Write results to CSV

Usage:
    python3 scripts/run_validation_sweep.py [--output-dir ./validation/results]
"""

import csv
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List
import argparse
from datetime import datetime

# Add validation module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "validation"))

from physics_extractor import PhysicsExtractionResult, extract_physics_for_case


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class ValidationSweep:
    """Orchestrator for validation sweep campaign."""
    
    def __init__(self, candidate_file: Path, output_base_dir: Path):
        self.candidate_file = Path(candidate_file)
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Timestamp for this sweep
        self.sweep_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.sweep_dir = self.output_base_dir / self.sweep_id
        self.sweep_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ValidationSweep initialized: {self.sweep_dir}")
        
    def load_candidate(self) -> Dict[str, Any]:
        """Load canonical candidate configuration."""
        with open(self.candidate_file, 'r') as f:
            return json.load(f)
    
    def load_case_matrix(self) -> List[Dict[str, Any]]:
        """Load generated case matrix (or generate if missing)."""
        case_matrix_file = self.candidate_file.parent / "generated" / "candidate0_case_matrix.json"
        
        if not case_matrix_file.exists():
            logger.warning(f"Case matrix not found at {case_matrix_file}")
            logger.info("Generating case matrix...")
            self._generate_case_matrix()
        
        with open(case_matrix_file, 'r') as f:
            return json.load(f)
    
    def _generate_case_matrix(self):
        """Generate case matrix from candidate."""
        candidate = self.load_candidate()
        cases = []
        
        variants = [
            ("baseline", 0.0, 0.0),
            ("weak_tct", 0.2, 0.0),
            ("moderate_tct", 0.5, 0.05),
            ("aggressive_tct", 0.8, 0.0),
            ("aggressive_tct_li_current", 0.8, 0.10),
        ]
        
        for name, tct_strength, li_current in variants:
            case = json.loads(json.dumps(candidate))
            case["case_name"] = name
            case["tct_translation"]["control_strength"] = tct_strength
            case["wall"]["lithium_current_proxy"] = li_current
            cases.append(case)
        
        outdir = self.candidate_file.parent / "generated"
        outdir.mkdir(parents=True, exist_ok=True)
        
        with open(outdir / "candidate0_case_matrix.json", 'w') as f:
            json.dump(cases, f, indent=2)
        
        logger.info(f"Generated {len(cases)} validation cases")
    
    def run_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single validation case.
        
        Returns dictionary with:
        - case_name
        - status: success, missing_outputs, extraction_failed, etc.
        - raw_physics: extracted values before constraints
        - final_physics: values after constraint application
        - score: scalar objective score
        - config_params: key configuration parameters
        """
        case_name = case.get("case_name", "unknown")
        logger.info(f"{'='*60}")
        logger.info(f"Running case: {case_name}")
        logger.info(f"{'='*60}")
        
        result = {
            "candidate_id": "Candidate-0",
            "case_name": case_name,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Create case-specific output directory
        case_output_dir = self.sweep_dir / case_name
        case_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Log config to case directory
        with open(case_output_dir / "case_config.json", 'w') as f:
            json.dump(case, f, indent=2)
        
        # 1. Run M3D-C1 (placeholder - in real use, call the binary)
        logger.info(f"[{case_name}] Running M3D-C1 backend...")
        backend_ok = self._run_backend(case, case_output_dir)
        result["backend_returncode"] = 0 if backend_ok else 1
        
        # 2. Extract physics
        logger.info(f"[{case_name}] Extracting physics...")
        physics_result = extract_physics_for_case(case_name, case_output_dir)
        
        # Dump extracted values before any constraints
        result["extraction_status"] = physics_result.extraction_status
        result["failure_reason"] = physics_result.failure_reason
        result["warnings"] = " | ".join(physics_result.warnings)
        
        # Raw physics (before constraints)
        raw_physics = physics_result.to_dict()
        result.update({
            f"raw_{k}": v for k, v in raw_physics.items()
        })
        
        # 3. Apply constraints (placeholder)
        logger.info(f"[{case_name}] Applying constraints...")
        constrained_physics = self._apply_constraints(physics_result, case)
        result.update({
            f"final_{k}": v for k, v in constrained_physics.items()
        })
        
        # 4. Compute score
        logger.info(f"[{case_name}] Computing score...")
        score = self._compute_score(physics_result, case)
        result["score"] = score
        
        # 5. Store key config parameters
        result.update(self._extract_config_params(case))
        
        logger.info(f"[{case_name}] Case complete: status={physics_result.extraction_status}, score={score}")
        
        return result
    
    def _run_backend(self, case: Dict[str, Any], output_dir: Path) -> bool:
        """
        Run M3D-C1 backend (placeholder).
        
        In real usage, this would:
        - Write case config to input file
        - Execute m3dc1 binary
        - Capture stdout/stderr
        - Return success/failure
        
        For now, returns True (success) to test the pipeline.
        """
        logger.debug(f"Backend placeholder: would run m3dc1 in {output_dir}")
        # In production: run_subprocess(["./m3dc1_2d", "-config", config_file])
        return True
    
    def _apply_constraints(self, physics: PhysicsExtractionResult, case: Dict[str, Any]) -> Dict[str, float]:
        """
        Apply physics constraints/gates.
        
        Returns filtered/constrained physics dict.
        Placeholder: returns as-is.
        """
        return physics.to_dict()
    
    def _compute_score(self, physics: PhysicsExtractionResult, case: Dict[str, Any]) -> float:
        """
        Compute objective score from physics outputs.
        
        Placeholder: returns dummy score based on Pfus_MW.
        """
        if not physics.is_valid():
            return 0.0
        
        # Example scoring: reward fusion power, penalize high severity
        pfus = physics.Pfus_MW or 0.0
        severity = physics.event_severity_mean or 0.0
        
        score = max(0.0, pfus - 5.0 * severity)
        return score
    
    def _extract_config_params(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and flatten key configuration parameters for CSV."""
        params = {}
        
        # Reactor geometry
        reactor = case.get("reactor", {})
        params["B0_T"] = reactor.get("B0_T")
        params["Ip_MA"] = reactor.get("Ip_MA")
        params["R_m"] = reactor.get("R_m")
        params["a_m"] = reactor.get("a_m")
        
        # Plasma
        plasma = case.get("plasma", {})
        params["H98"] = plasma.get("H98")
        params["greenwald_fraction"] = plasma.get("greenwald_fraction")
        params["target_betaN"] = plasma.get("target_betaN")
        
        # TCT
        tct = case.get("tct_translation", {})
        params["tct_strength"] = tct.get("control_strength")
        
        # Wall
        wall = case.get("wall", {})
        params["li_current_proxy"] = wall.get("lithium_current_proxy")
        
        return params
    
    def run_sweep(self) -> Path:
        """Execute full validation sweep."""
        logger.info(f"Starting validation sweep: {self.sweep_id}")
        
        candidate = self.load_candidate()
        case_matrix = self.load_case_matrix()
        
        logger.info(f"Candidate: {candidate.get('candidate_name')}")
        logger.info(f"Cases to run: {len(case_matrix)}")
        
        # Run all cases
        all_results = []
        for i, case in enumerate(case_matrix, 1):
            try:
                result = self.run_case(case)
                all_results.append(result)
            except Exception as e:
                logger.error(f"Case {case.get('case_name')} failed with exception: {e}", exc_info=True)
                result = {
                    "candidate_id": "Candidate-0",
                    "case_name": case.get("case_name", "unknown"),
                    "timestamp": datetime.now().isoformat(),
                    "extraction_status": "exception",
                    "failure_reason": str(e),
                }
                all_results.append(result)
        
        # Write results to CSV
        csv_path = self._write_results_csv(all_results)
        
        logger.info(f"{'='*60}")
        logger.info(f"Validation sweep complete!")
        logger.info(f"Results written to: {csv_path}")
        logger.info(f"{'='*60}")
        
        return csv_path
    
    def _write_results_csv(self, results: List[Dict[str, Any]]) -> Path:
        """Write all results to CSV with comprehensive columns."""
        csv_path = self.sweep_dir / "validation_results.csv"
        
        if not results:
            logger.warning("No results to write")
            return csv_path
        
        # Collect all unique keys across all results
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
        
        # Define column order (critical items first)
        priority_cols = [
            "candidate_id",
            "case_name",
            "timestamp",
            "extraction_status",
            "failure_reason",
            "warnings",
            "score",
            "backend_returncode",
        ]
        
        # Config columns
        config_cols = [
            "B0_T",
            "Ip_MA",
            "R_m",
            "a_m",
            "H98",
            "greenwald_fraction",
            "target_betaN",
            "tct_strength",
            "li_current_proxy",
        ]
        
        # Raw physics columns
        raw_physics_cols = [
            f"raw_{k}" for k in [
                "Pfus_MW", "Pnet_MW", "blanket_heat_MW",
                "Te_keV", "Ti_keV", "density_1e19",
                "beta", "betaN", "tau_E_s", "H98",
                "event_severity_mean", "event_severity_max",
            ]
            if f"raw_{k}" in all_keys
        ]
        
        # Final physics columns
        final_physics_cols = [
            f"final_{k}" for k in [
                "Pfus_MW", "Pnet_MW", "blanket_heat_MW",
                "event_severity_mean",
            ]
            if f"final_{k}" in all_keys
        ]
        
        # Assemble final column order
        ordered_cols = (
            priority_cols +
            config_cols +
            raw_physics_cols +
            final_physics_cols
        )
        
        # Only keep columns that exist
        fieldnames = [c for c in ordered_cols if c in all_keys]
        
        # Add any remaining columns
        remaining = sorted(all_keys - set(fieldnames))
        fieldnames.extend(remaining)
        
        # Write CSV
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        logger.info(f"Wrote {len(results)} results to {csv_path}")
        logger.info(f"Columns: {len(fieldnames)}")
        
        return csv_path


def main():
    parser = argparse.ArgumentParser(
        description="Run M3DC1 validation sweep"
    )
    parser.add_argument(
        "--candidate",
        type=Path,
        default=Path(__file__).parent.parent / "validation" / "candidate0_be_outer_killer.json",
        help="Path to candidate configuration JSON"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "validation" / "results",
        help="Base output directory for sweep results"
    )
    
    args = parser.parse_args()
    
    # Validate candidate file exists
    if not args.candidate.exists():
        logger.error(f"Candidate file not found: {args.candidate}")
        return 1
    
    # Run sweep
    sweep = ValidationSweep(args.candidate, args.output_dir)
    try:
        csv_path = sweep.run_sweep()
        logger.info(f"SUCCESS: Results at {csv_path}")
        return 0
    except Exception as e:
        logger.error(f"Sweep failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
