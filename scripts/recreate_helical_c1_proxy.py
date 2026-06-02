#!/usr/bin/env python3
"""Create a source-inspired helical M3D-C1 proxy C1.h5.

This does not recreate the hidden PPPL helical run exactly. It builds a
publicly documented, reader-compatible benchmark proxy from:

- the archived helical coil meeting notes
- the public M3D-C1 HDF5 reader conventions
- the real HEAT `C1.h5` layout we verified locally

The goal is to produce a file that the M3D-C1 Python readers can open and that
the validation harness can extract into backend diagnostics.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import h5py
import numpy as np


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "validation" / "generated" / "helical_benchmark_proxy" / "C1.h5"


def _write_dataset(group: h5py.Group, name: str, data, *, dtype=None) -> None:
    arr = np.asarray(data, dtype=dtype)
    if name in group:
        del group[name]
    group.create_dataset(name, data=arr)


def _make_coeffs(
    n_elem: int,
    base: float,
    r_slope: float = 0.0,
    z_slope: float = 0.0,
    phi_slope: float = 0.0,
    *,
    n_coeff: int = 20,
) -> np.ndarray:
    """Return [n_elem, n_coeff] polynomial coefficients for a simple proxy field."""
    coeffs = np.zeros((n_elem, n_coeff), dtype=np.float64)
    for i in range(n_elem):
        plane = 1.0 + 0.03 * (i // 6)
        offset = (i % 6) - 2.5
        coeffs[i, 0] = base * plane
        coeffs[i, 1] = r_slope * offset
        coeffs[i, 2] = z_slope * offset
        coeffs[i, 3] = phi_slope * (i // 6)
        coeffs[i, 4] = 0.10 * coeffs[i, 1]
        coeffs[i, 5] = 0.10 * coeffs[i, 2]
        coeffs[i, 6] = 0.05 * coeffs[i, 3]
    return coeffs


def _make_mesh() -> np.ndarray:
    """Return a small 3D triangular mesh in the M3D-C1 element layout."""
    elems = []
    # Three poloidal triangles duplicated on eight toroidal planes.
    triangles = [
        (1.20, 1.40, 2.60, -0.15, 1.55, -1.25, 1.0),
        (1.10, 1.30, 2.40, 0.05, 2.10, -1.05, 1.0),
        (1.05, 1.20, 2.10, 0.20, 2.55, -0.90, 2.0),
    ]
    planes = [(math.pi / 4.0, i * (math.pi / 4.0)) for i in range(8)]
    for dphi, phi_elm in planes:
        for a, b, c, theta, r0, z0, zone in triangles:
            elems.append([a, b, c, theta, r0, z0, zone])
    return np.asarray(elems, dtype=np.float64)


def _make_series(value: float, n: int = 2, *, delta: float = 0.0) -> np.ndarray:
    arr = np.empty(n, dtype=np.float64)
    for i in range(n):
        arr[i] = value + delta * i
    return arr


def _make_scalar_map() -> dict[str, np.ndarray]:
    """Construct a broad scalar set resembling a real M3D-C1 output."""
    ntime = 2
    paux_mw = 100.0
    power_lost_mw = 40.0

    scalars = {
        "time": _make_series(0.0, ntime, delta=1.0),
        "dt": _make_series(1.0, ntime, delta=0.0),
        "loop_voltage": _make_series(1.0e-4, ntime, delta=0.0),
        "toroidal_current": np.asarray([1.45e6, 1.55e6], dtype=np.float64),
        "toroidal_current_p": np.asarray([1.35e6, 1.45e6], dtype=np.float64),
        "particle_number": np.asarray([1.15e20, 1.20e20], dtype=np.float64),
        "particle_number_p": np.asarray([1.10e20, 1.15e20], dtype=np.float64),
        "electron_number": np.asarray([1.20e20, 1.26e20], dtype=np.float64),
        "volume": np.asarray([240.0, 240.0], dtype=np.float64),
        "volume_p": np.asarray([240.0, 240.0], dtype=np.float64),
        "Ave_P": np.asarray([920.0, 940.0], dtype=np.float64),
        "temax": np.asarray([11.5, 11.8], dtype=np.float64),
        "psi_lcfs": np.asarray([-0.108, -0.109], dtype=np.float64),
        "psimin": np.asarray([-0.125, -0.126], dtype=np.float64),
        "xmag": np.asarray([3.02, 3.02], dtype=np.float64),
        "zmag": np.asarray([0.0, 0.0], dtype=np.float64),
        "xnull": np.asarray([1.9, 1.9], dtype=np.float64),
        "znull": np.asarray([-1.0, -1.0], dtype=np.float64),
        "toroidal_flux": np.asarray([0.15, 0.155], dtype=np.float64),
        "toroidal_flux_p": np.asarray([0.15, 0.155], dtype=np.float64),
        "pellet_rate": np.asarray([0.0, 0.0], dtype=np.float64),
        "pellet_phi": np.asarray([0.0, 0.0], dtype=np.float64),
        "pellet_x": np.asarray([0.0, 0.0], dtype=np.float64),
        "pellet_z": np.asarray([0.0, 0.0], dtype=np.float64),
        "power_injected": np.asarray([paux_mw, paux_mw], dtype=np.float64),
        "radiation": np.asarray([-power_lost_mw, -(power_lost_mw + 2.0)], dtype=np.float64),
        "line_rad": np.asarray([-12.0, -12.5], dtype=np.float64),
        "brem_rad": np.asarray([-5.0, -5.0], dtype=np.float64),
        "ion_loss": np.asarray([-2.0, -2.0], dtype=np.float64),
        "reck_rad": np.asarray([-1.0, -1.0], dtype=np.float64),
        "recp_rad": np.asarray([-1.0, -1.0], dtype=np.float64),
        "e_mpd": np.asarray([-1.0, -1.0], dtype=np.float64),
        "e_mtd": np.asarray([-1.0, -1.0], dtype=np.float64),
        # Energy and transport channels visible in real C1.h5 files.
        "E_P": np.asarray([25.0, 25.2], dtype=np.float64),
        "E_MP": np.asarray([15.0, 15.1], dtype=np.float64),
        "E_MT": np.asarray([10.0, 10.1], dtype=np.float64),
        "E_PD": np.asarray([8.0, 8.05], dtype=np.float64),
        "E_PH": np.asarray([7.5, 7.55], dtype=np.float64),
        "E_MPD": np.asarray([8.0, 8.05], dtype=np.float64),
        "E_MPH": np.asarray([7.5, 7.55], dtype=np.float64),
        "E_MTD": np.asarray([4.0, 4.05], dtype=np.float64),
        "E_MTH": np.asarray([3.5, 3.55], dtype=np.float64),
        "E_KP": np.asarray([2.5, 2.55], dtype=np.float64),
        "E_KPD": np.asarray([2.0, 2.05], dtype=np.float64),
        "E_KPH": np.asarray([1.8, 1.85], dtype=np.float64),
        "E_KT": np.asarray([1.6, 1.65], dtype=np.float64),
        "E_KTD": np.asarray([1.3, 1.35], dtype=np.float64),
        "E_KTH": np.asarray([1.1, 1.15], dtype=np.float64),
        "E_K3": np.asarray([0.9, 0.95], dtype=np.float64),
        "E_K3D": np.asarray([0.8, 0.85], dtype=np.float64),
        "E_K3H": np.asarray([0.7, 0.75], dtype=np.float64),
        "E_grav": np.asarray([0.2, 0.21], dtype=np.float64),
        "Flux_kinetic": np.asarray([0.12, 0.125], dtype=np.float64),
        "Flux_poynting": np.asarray([0.18, 0.185], dtype=np.float64),
        "Flux_pressure": np.asarray([0.14, 0.145], dtype=np.float64),
        "Flux_thermal": np.asarray([0.22, 0.225], dtype=np.float64),
        "Parallel_viscous_heating": np.asarray([0.03, 0.032], dtype=np.float64),
        "Particle_Flux_convective": np.asarray([0.04, 0.042], dtype=np.float64),
        "Particle_Flux_diffusive": np.asarray([0.02, 0.021], dtype=np.float64),
        "Particle_source": np.asarray([0.05, 0.052], dtype=np.float64),
        "Torque_com": np.asarray([0.01, 0.011], dtype=np.float64),
        "Torque_em": np.asarray([0.02, 0.021], dtype=np.float64),
        "Torque_gyro": np.asarray([0.01, 0.011], dtype=np.float64),
        "Torque_parvisc": np.asarray([0.01, 0.011], dtype=np.float64),
        "Torque_sol": np.asarray([0.02, 0.021], dtype=np.float64),
        "Torque_visc": np.asarray([0.01, 0.011], dtype=np.float64),
        "angular_momentum": np.asarray([0.12, 0.13], dtype=np.float64),
        "angular_momentum_p": np.asarray([0.11, 0.12], dtype=np.float64),
        "area": np.asarray([130.0, 130.0], dtype=np.float64),
        "area_p": np.asarray([130.0, 130.0], dtype=np.float64),
        "circulation": np.asarray([0.08, 0.081], dtype=np.float64),
        "circulation_p": np.asarray([0.08, 0.081], dtype=np.float64),
    }
    return scalars


def _make_field_map(n_elem: int) -> dict[str, np.ndarray]:
    """Create element-major coefficient arrays for the main field set."""
    return {
        "rst": _make_coeffs(n_elem, 2.0, r_slope=0.08, z_slope=0.03, phi_slope=0.02),
        "zst": _make_coeffs(n_elem, -1.0, r_slope=0.02, z_slope=0.08, phi_slope=0.01),
        "psi": _make_coeffs(n_elem, 0.08, r_slope=0.01, z_slope=0.005, phi_slope=0.002),
        "i": _make_coeffs(n_elem, 1.45e6, r_slope=5.0e4, z_slope=2.0e4, phi_slope=1.0e4),
        "phi": _make_coeffs(n_elem, 1.0e-4, r_slope=1.0e-5, z_slope=1.0e-5),
        "v": _make_coeffs(n_elem, 1.0e-4, r_slope=1.0e-5, z_slope=1.0e-5),
        "chi": _make_coeffs(n_elem, 2.0e-2, r_slope=2.0e-3, z_slope=1.0e-3),
        "P": _make_coeffs(n_elem, 900.0, r_slope=40.0, z_slope=20.0, phi_slope=10.0),
        "Pe": _make_coeffs(n_elem, 450.0, r_slope=20.0, z_slope=10.0),
        "ti": _make_coeffs(n_elem, 12.0, r_slope=0.8, z_slope=0.4),
        "te": _make_coeffs(n_elem, 11.5, r_slope=0.7, z_slope=0.35),
        "den": _make_coeffs(n_elem, 1.2e20, r_slope=3.0e18, z_slope=1.5e18),
        "ne": _make_coeffs(n_elem, 1.25e20, r_slope=3.2e18, z_slope=1.6e18),
        "E_R": _make_coeffs(n_elem, 0.0),
        "E_Z": _make_coeffs(n_elem, 0.0),
        "E_PHI": _make_coeffs(n_elem, 0.0),
        "I": _make_coeffs(n_elem, 1.45e6),
        "I_i": _make_coeffs(n_elem, 1.45e6),
        "P_i": _make_coeffs(n_elem, 850.0, r_slope=35.0, z_slope=18.0),
        "Pe_i": _make_coeffs(n_elem, 430.0, r_slope=18.0, z_slope=9.0),
        "V_i": _make_coeffs(n_elem, 1.0e-4, r_slope=1.0e-5, z_slope=1.0e-5),
        "chi_i": _make_coeffs(n_elem, 1.5e-2, r_slope=1.5e-3, z_slope=8.0e-4),
        "den_i": _make_coeffs(n_elem, 1.15e20, r_slope=2.8e18, z_slope=1.4e18),
    }


def _write_time_group(parent: h5py.File, name: str, *, time_value: float, fields: dict[str, np.ndarray], mesh: np.ndarray) -> None:
    if name in parent:
        del parent[name]
    grp = parent.create_group(name)
    fgrp = grp.create_group("fields")
    mgrp = grp.create_group("mesh")
    for fname, arr in fields.items():
        _write_dataset(fgrp, fname, arr)
    _write_dataset(mgrp, "elements", mesh)
    _write_dataset(mgrp, "nplanes", np.asarray([2], dtype=np.int32))
    _write_dataset(mgrp, "period", np.asarray([2.0 * math.pi], dtype=np.float64))
    _write_dataset(grp, "time", np.asarray([time_value], dtype=np.float64))


def build_proxy(out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    mesh = _make_mesh()
    n_elem = mesh.shape[0]
    time0_fields = _make_field_map(n_elem)
    # Slightly evolved second snapshot.
    time1_fields = {
        k: np.asarray(v * (1.02 if k in {"P", "Pe", "P_i", "Pe_i", "ti", "te", "den", "ne", "den_i"} else 1.01))
        for k, v in time0_fields.items()
    }
    scalars = _make_scalar_map()

    with h5py.File(out_path, "w") as h5:
        # Source-inspired configuration, not a claim of exact provenance.
        h5.attrs["version"] = 36
        h5.attrs["ntime"] = 2
        h5.attrs["numvar"] = 20
        h5.attrs["itor"] = 1
        h5.attrs["3d"] = 1
        h5.attrs["igeometry"] = 1
        h5.attrs["nplanes"] = 2
        h5.attrs["rzero"] = 3.0
        h5.attrs["zzero"] = 0.0
        h5.attrs["ntor"] = 1
        h5.attrs["mpol"] = 1
        h5.attrs["bzero"] = 1.0
        h5.attrs["b0_norm"] = 1.0
        h5.attrs["n0_norm"] = 1.0
        h5.attrs["l0_norm"] = 1.0
        h5.attrs["ion_mass"] = 2.0
        h5.attrs["amu"] = 2.0
        h5.attrs["amuc"] = 2.0
        h5.attrs["amupar"] = 2.0
        h5.attrs["gam"] = 1.6666666666666667
        h5.attrs["eta0"] = 1.0e-6
        h5.attrs["eta_wall"] = 0.2
        h5.attrs["etar"] = 0.2
        h5.attrs["lithium_thickness_m"] = 0.0021
        h5.attrs["delta_wall"] = 0.0
        h5.attrs["db"] = 0.0
        h5.attrs["denm"] = 1.0
        h5.attrs["eqsubtract"] = 0
        h5.attrs["extsubtract"] = 0
        h5.attrs["gyro"] = 0
        h5.attrs["hyper"] = 0
        h5.attrs["hyperc"] = 0
        h5.attrs["hyperi"] = 0
        h5.attrs["hyperp"] = 0
        h5.attrs["hyperv"] = 0
        h5.attrs["icomplex"] = 0
        h5.attrs["icsubract"] = 0
        h5.attrs["idens"] = 1
        h5.attrs["ifixedb"] = 0
        h5.attrs["integrator"] = 1
        h5.attrs["ipellet"] = 0
        h5.attrs["iper"] = 1
        h5.attrs["ipres"] = 1
        h5.attrs["ipressplit"] = 0
        h5.attrs["itemp"] = 1
        h5.attrs["ivform"] = 0
        h5.attrs["jper"] = 1
        h5.attrs["kappa0"] = 0.0
        h5.attrs["kappar"] = 0.0
        h5.attrs["kappat"] = 0.0
        h5.attrs["linear"] = 0
        h5.attrs["ln"] = 1
        h5.attrs["nonrect"] = 1
        h5.attrs["pellet_var"] = 0.0
        h5.attrs["pellet_velphi"] = 0.0
        h5.attrs["pellet_velx"] = 0.0
        h5.attrs["pellet_velz"] = 0.0
        h5.attrs["thimp"] = 0
        h5.attrs["vloop"] = 1.0e-4
        h5.attrs["xlim"] = np.asarray([1.0, 6.0], dtype=np.float64)
        h5.attrs["zlim"] = np.asarray([-2.0, 2.0], dtype=np.float64)
        h5.attrs["xmag"] = 3.02
        h5.attrs["zmag"] = 0.0
        h5.attrs["zeff"] = 1.0
        h5.attrs["blanket_topology"] = "be_outer"
        h5.attrs["helical_proxy"] = 1

        scal_grp = h5.create_group("scalars")
        for name, data in scalars.items():
            _write_dataset(scal_grp, name, data)

        eq = h5.create_group("equilibrium")
        eq_fields = eq.create_group("fields")
        eq_mesh = eq.create_group("mesh")
        for fname, arr in time1_fields.items():
            _write_dataset(eq_fields, fname, arr)
        _write_dataset(eq_mesh, "elements", mesh)
        _write_dataset(eq_mesh, "nplanes", np.asarray([2], dtype=np.int32))
        _write_dataset(eq_mesh, "period", np.asarray([2.0 * math.pi], dtype=np.float64))

        _write_time_group(h5, "time_000", time_value=0.0, fields=time0_fields, mesh=mesh)
        _write_time_group(h5, "time_001", time_value=1.0, fields=time1_fields, mesh=mesh)

        timings = h5.create_group("timings")
        _write_dataset(timings, "setup", np.asarray([0.5], dtype=np.float64))
        _write_dataset(timings, "solve", np.asarray([8.0], dtype=np.float64))
        _write_dataset(timings, "post", np.asarray([0.2], dtype=np.float64))

        proxy_meta = h5.create_group("proxy_metadata")
        _write_dataset(proxy_meta, "benchmark_label", np.asarray("helical_benchmark_proxy", dtype=h5py.string_dtype("utf-8")))
        _write_dataset(proxy_meta, "provenance_note", np.asarray(
            "Source-inspired proxy built from public PPPL meeting notes, public M3D-C1 reader conventions, and the HEAT C1.h5 layout.",
            dtype=h5py.string_dtype("utf-8"),
        ))
        _write_dataset(proxy_meta, "lithium_thickness_m", np.asarray([0.0021], dtype=np.float64))
        _write_dataset(proxy_meta, "blanket_topology", np.asarray("be_outer", dtype=h5py.string_dtype("utf-8")))
        _write_dataset(proxy_meta, "target_tbr_floor", np.asarray([1.05], dtype=np.float64))
        _write_dataset(proxy_meta, "source_paths", np.asarray([
            "/projects/M3DC1/sjardin/helical5g/C1.h5",
            "/projects/M3DC1/sjardin/helical5f/C1.h5",
        ], dtype=h5py.string_dtype("utf-8")))

    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a source-inspired helical M3D-C1 proxy C1.h5.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = build_proxy(args.output)
    print(out)


if __name__ == "__main__":
    main()
