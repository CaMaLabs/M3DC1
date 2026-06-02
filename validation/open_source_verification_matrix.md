# Open Source Verification Matrix

This matrix maps the current M3D-C1 smoke cases to the closest open-source
verification codes. The goal is not a 1:1 physics replacement for every case.
The goal is to start with the best open-source solver for each smoke case class
and define what should be compared.

## Case Mapping

| M3D-C1 smoke case | Open-source verifier(s) | Compare | Why this is the right first target | Caveats |
|---|---|---|---|---|
| `RMP` | [OpenFUSIONToolkit](https://github.com/OpenFUSIONToolkit/OpenFUSIONToolkit) | Linear response, edge current perturbation, wall-current coupling | OFT includes `MUG` for time-dependent nonlinear extended MHD and `ThinCurr` for inductively excited thin-wall currents. | Best fit for response physics, not a full M3D-C1 clone. |
| `RMP_nonlin` | [OpenFUSIONToolkit](https://github.com/OpenFUSIONToolkit/OpenFUSIONToolkit) | Nonlinear growth, control response, wall coupling, saturation trend | Same OFT components match the coupled plasma/wall-current nature of the case. | If the case relies on M3D-C1-specific transport details, keep those as internal regressions. |
| `NCSX` | [VMEC++](https://github.com/proximafusion/vmecpp), [DESC](https://github.com/PlasmaControl/DESC) | Equilibrium geometry, flux surface shape, field-line consistency, force balance | Both are open-source stellarator equilibrium solvers; VMEC++ is a VMEC reimplementation and DESC solves 3D MHD equilibria. | Use both if you want a stronger equilibrium cross-check. |
| `adapt` | [OpenFUSIONToolkit](https://github.com/OpenFUSIONToolkit/OpenFUSIONToolkit) plus local mesh-quality checks | Mesh quality, conservation drift, stability of adapted solution | This is mainly a mesh/regression case, so the right verification target is mesh behavior rather than a new physics solver. | Treat as infrastructure validation first. |
| `KPRAD_2D` | No clean 1:1 open-source replacement | KPRAD-integrated impurity response, radiation loss trends, restart behavior | KPRAD is a M3D-C1-specific impurity/radiation model. There is no direct open-source substitute I would treat as equivalent. | Use OFT or another MHD solver only to validate the surrounding plasma response. |
| `KPRAD_restart` | No clean 1:1 open-source replacement | Restart fidelity and post-restart state continuity | Same limitation as `KPRAD_2D`, plus restart logic makes it even more code-specific. | Keep this as a M3D-C1 regression unless you build explicit surrogate diagnostics. |
| `pellet` | No clean 1:1 open-source replacement | Particle source coupling, impurity injection response, transient edge dynamics | Pellet ablation and impurity coupling are tightly embedded in the M3D-C1 workflow. | Validate with M3D-C1-native regressions and surrounding plasma checks; do not force a fake 1:1 match. |

## Secondary verification path

If the liquid-lithium side of the concept matters independently of the plasma
smoke cases, add:

- [FreeMHD](https://github.com/PlasmaControl/FreeMHD) for free-surface liquid
  metal and conducting-flow behavior.

FreeMHD is useful for the lithium-wall side of the concept, but it is not a
substitute for the plasma-side M3D-C1 smoke cases.

## Recommended starting order

1. Use [OpenFUSIONToolkit](https://github.com/OpenFUSIONToolkit/OpenFUSIONToolkit)
   for `RMP`, `RMP_nonlin`, and `adapt`.
2. Use [VMEC++](https://github.com/proximafusion/vmecpp) and
   [DESC](https://github.com/PlasmaControl/DESC) for `NCSX`.
3. Use [FreeMHD](https://github.com/PlasmaControl/FreeMHD) if you want to
   check the liquid-metal behavior separately.
4. Keep `KPRAD_2D`, `KPRAD_restart`, and `pellet` as internal M3D-C1 regression
   cases unless you build a custom surrogate workflow.

## Practical validation rule

Use open-source verification to answer the question:

- "Does this smoke case belong to a physically plausible family of MHD or
  equilibrium problems?"

Use M3D-C1-native regression to answer the question:

- "Did the exact M3D-C1 feature set, restart behavior, and KPRAD coupling stay
  stable?"
