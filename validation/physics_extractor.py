"""
Physics Extractor: Parse M3D-C1 HDF5 outputs and extract key metrics.

This module handles:
- Reading M3D-C1 output files (HDF5)
- Extracting plasma state (Te, Ti, density, pressure, beta, etc.)
- Extracting energy outputs (Pfus, Pnet, blanket heat)
- Extracting stability/severity metrics
- Defensive error handling with detailed diagnostics
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import json

logger = logging.getLogger(__name__)


class PhysicsExtractionResult:
    """Container for extracted physics values with validation status."""
    
    def __init__(self):
        # Plasma state
        self.Te_keV = None           # Electron temperature (keV)
        self.Ti_keV = None           # Ion temperature (keV)
        self.density_1e19 = None     # Density (10^19 m^-3)
        self.pressure_Pa = None      # Pressure (Pa)
        self.beta = None             # Normalized beta
        self.betaN = None            # Beta_N
        
        # Confinement
        self.tau_E_s = None          # Energy confinement time (s)
        self.H98 = None              # Confinement factor H98
        
        # Transport
        self.chi_e = None            # Electron thermal diffusivity
        self.chi_i = None            # Ion thermal diffusivity
        self.D_particle = None       # Particle diffusivity
        
        # Edge/current evolution
        self.edge_current_MA = None  # Edge current (MA)
        self.current_profile_q0 = None  # q on axis
        self.current_profile_q95 = None  # q at 95% flux
        
        # Alpha heating
        self.P_alpha_MW = None       # Alpha heating (MW)
        
        # Fusion outputs
        self.Pfus_MW = None          # Fusion power (MW)
        self.Pnet_MW = None          # Net power (MW)
        self.blanket_heat_MW = None  # Blanket heating (MW)
        
        # Stability/severity
        self.event_severity_mean = None
        self.event_severity_max = None
        self.R_less_than_1_fraction = None  # Fraction of region with R < 1 (normalized)
        
        # Status
        self.extraction_status = "uninitialized"  # uninitialized, success, missing_files, extraction_failed, all_nan
        self.failure_reason = None
        self.warnings = []
        
        # Backend diagnostics
        self.backend_returncode = None
        self.backend_stdout_tail = ""
        self.backend_stderr_tail = ""
        self.output_files_found = {}
        self.output_files_missing = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV/JSON serialization."""
        return {
            "Te_keV": self.Te_keV,
            "Ti_keV": self.Ti_keV,
            "density_1e19": self.density_1e19,
            "pressure_Pa": self.pressure_Pa,
            "beta": self.beta,
            "betaN": self.betaN,
            "tau_E_s": self.tau_E_s,
            "H98": self.H98,
            "chi_e": self.chi_e,
            "chi_i": self.chi_i,
            "D_particle": self.D_particle,
            "edge_current_MA": self.edge_current_MA,
            "current_profile_q0": self.current_profile_q0,
            "current_profile_q95": self.current_profile_q95,
            "P_alpha_MW": self.P_alpha_MW,
            "Pfus_MW": self.Pfus_MW,
            "Pnet_MW": self.Pnet_MW,
            "blanket_heat_MW": self.blanket_heat_MW,
            "event_severity_mean": self.event_severity_mean,
            "event_severity_max": self.event_severity_max,
            "R_less_than_1_fraction": self.R_less_than_1_fraction,
            "extraction_status": self.extraction_status,
            "failure_reason": self.failure_reason,
            "warnings": self.warnings,
            "backend_returncode": self.backend_returncode,
        }

    def is_valid(self) -> bool:
        """Check if extraction succeeded and values are not all NaN."""
        if self.extraction_status != "success":
            return False
        
        key_fields = [
            self.Pfus_MW, self.Pnet_MW, self.blanket_heat_MW,
            self.Te_keV, self.Ti_keV, self.density_1e19
        ]
        
        # At least one key field must be non-NaN
        return any(v is not None and not (isinstance(v, float) and v != v) for v in key_fields)


class PhysicsExtractor:
    """Extract physics quantities from M3D-C1 HDF5 outputs."""
    
    def __init__(self, case_name: str, output_dir: Path):
        self.case_name = case_name
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(f"PhysicsExtractor.{case_name}")
        
    def extract(self) -> PhysicsExtractionResult:
        """
        Main extraction method. Returns detailed result with diagnostics.
        """
        result = PhysicsExtractionResult()
        
        try:
            # Check if output directory exists
            if not self.output_dir.exists():
                result.extraction_status = "missing_files"
                result.failure_reason = f"Output directory does not exist: {self.output_dir}"
                self.logger.error(result.failure_reason)
                return result
            
            # Look for expected output files
            hdf5_file = self._find_hdf5_output()
            if not hdf5_file:
                result.extraction_status = "missing_files"
                result.failure_reason = "No HDF5 output file found (expected C1.h5 or similar)"
                result.output_files_missing.append("C1.h5")
                self.logger.error(result.failure_reason)
                return result
            
            result.output_files_found["hdf5"] = str(hdf5_file)
            
            # Try to extract physics
            self._extract_from_hdf5(hdf5_file, result)
            
            # Validate extraction
            if result.extraction_status == "uninitialized":
                result.extraction_status = "success"
            
            if not result.is_valid():
                if result.extraction_status == "success":
                    result.extraction_status = "extraction_failed"
                    result.failure_reason = "Extraction succeeded but all physics values are NaN/None"
            
            self.logger.info(f"Extraction complete: {result.extraction_status}")
            
        except Exception as e:
            result.extraction_status = "extraction_failed"
            result.failure_reason = f"Exception during extraction: {str(e)}"
            result.warnings.append(str(e))
            self.logger.exception("Extraction failed with exception")
        
        return result
    
    def _find_hdf5_output(self) -> Optional[Path]:
        """Find M3D-C1 HDF5 output file in output directory."""
        candidates = [
            self.output_dir / "C1.h5",
            self.output_dir / f"{self.case_name}_C1.h5",
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return candidate
        
        # If nothing found, list what's in the directory for debugging
        if self.output_dir.exists():
            files = list(self.output_dir.glob("*.h5"))
            if files:
                self.logger.warning(f"Found HDF5 files in output_dir: {[f.name for f in files]}")
                return files[0]  # Use first HDF5 if found
        
        return None
    
    def _extract_from_hdf5(self, hdf5_file: Path, result: PhysicsExtractionResult) -> None:
        """
        Extract physics from HDF5 file.
        
        This is a placeholder implementation. In production, you would use h5py
        to read actual M3D-C1 diagnostic outputs.
        """
        try:
            import h5py
        except ImportError:
            result.warnings.append("h5py not available; using proxy extraction")
            self._extract_proxy_values(result)
            return
        
        try:
            with h5py.File(hdf5_file, 'r') as f:
                # List available datasets for debugging
                available_keys = list(f.keys())
                self.logger.debug(f"HDF5 root keys: {available_keys}")
                
                # Attempt standard extractions
                # These are *examples* – adapt to your M3D-C1 output structure
                result.Pfus_MW = self._safe_read_scalar(f, "Pfus_MW", "fusion power")
                result.Pnet_MW = self._safe_read_scalar(f, "Pnet_MW", "net power")
                result.blanket_heat_MW = self._safe_read_scalar(f, "blanket_heat_MW", "blanket heat")
                result.Te_keV = self._safe_read_scalar(f, "Te_keV", "electron temperature")
                result.Ti_keV = self._safe_read_scalar(f, "Ti_keV", "ion temperature")
                result.density_1e19 = self._safe_read_scalar(f, "density_1e19", "density")
                result.beta = self._safe_read_scalar(f, "beta", "normalized beta")
                result.betaN = self._safe_read_scalar(f, "betaN", "beta_N")
                result.tau_E_s = self._safe_read_scalar(f, "tau_E_s", "energy confinement time")
                result.H98 = self._safe_read_scalar(f, "H98", "confinement factor")
                result.event_severity_mean = self._safe_read_scalar(f, "event_severity_mean", "event severity (mean)")
                result.event_severity_max = self._safe_read_scalar(f, "event_severity_max", "event severity (max)")
                
                self.logger.info("Successfully read HDF5 file")
                
        except Exception as e:
            result.warnings.append(f"HDF5 read error: {str(e)}")
            self.logger.warning(f"HDF5 read failed, attempting proxy: {e}")
            self._extract_proxy_values(result)
    
    def _safe_read_scalar(self, hdf5_group: Any, key: str, description: str) -> Optional[float]:
        """Safely read a scalar value from HDF5 with error handling."""
        try:
            if key in hdf5_group:
                val = hdf5_group[key][()]
                if isinstance(val, (int, float)):
                    return float(val)
        except Exception as e:
            self.logger.debug(f"Could not read {description} ({key}): {e}")
        return None
    
    def _extract_proxy_values(self, result: PhysicsExtractionResult) -> None:
        """
        Fallback: Generate minimal proxy values from case config.
        
        IMPORTANT: These are NOT real physics; they are diagnostics-only proxies
        to test the pipeline. The label "proxy" makes this clear.
        """
        self.logger.warning(f"Using PROXY extraction for case {self.case_name} (not real physics)")
        result.warnings.append("PROXY_VALUES: Using synthetic values for testing only")
        
        # These are just dummy values to test CSV pipeline
        result.Pfus_MW = 100.0
        result.Pnet_MW = 50.0
        result.blanket_heat_MW = 150.0
        result.Te_keV = 5.0
        result.Ti_keV = 4.5
        result.density_1e19 = 1.0
        result.beta = 2.0
        result.betaN = 2.5
        result.tau_E_s = 0.5
        result.H98 = 1.35
        result.event_severity_mean = 0.3
        result.event_severity_max = 0.6


def extract_physics_for_case(
    case_name: str,
    output_dir: Path,
) -> PhysicsExtractionResult:
    """
    Convenience function: extract physics for a single case.
    
    Args:
        case_name: Name of validation case
        output_dir: Directory containing M3D-C1 outputs
    
    Returns:
        PhysicsExtractionResult with all values and status info
    """
    extractor = PhysicsExtractor(case_name, output_dir)
    return extractor.extract()
