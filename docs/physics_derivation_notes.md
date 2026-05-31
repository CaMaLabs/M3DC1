# Baseline plasma-physics derivation notes

This note separates standard plasma-physics background from the exploratory TCT-labeled proxy work in this repository. It is not intended to replace a textbook treatment. It is meant to make the baseline assumptions explicit enough that the proposed proxy metrics can be criticized or rejected cleanly.

## Purpose

A fair criticism of any new control framing is that it must first map to established plasma physics. The TCT-labeled work in this repository should therefore be read as a proposed **diagnostic / control-proxy hypothesis**, not as a new first-principles theory.

The main question is:

> Do current-sheet thickness, sheet aspect ratio, or related reconnection-onset indicators add useful predictive or control information beyond standard edge / MHD observables?

If the answer is no, the TCT framing should be rejected or reduced to ordinary current-sheet / reconnection terminology.

## 1. Ideal-MHD force balance

The static single-fluid MHD momentum equation, neglecting flow and gravity, is

```text
0 = -grad(p) + J x B
```

so equilibrium requires

```text
grad(p) = J x B
```

with

```text
mu0 J = curl(B)
```

This is the baseline force-balance relation. Any control proxy involving edge current, current-sheet geometry, magnetic shear, or pressure-gradient behavior ultimately has to be consistent with this balance or with a justified extension of it.

## 2. Cylindrical screw-pinch force balance

For a cylindrical screw pinch, use cylindrical coordinates `(r, theta, z)` and assume axisymmetry:

```text
B = B_theta(r) e_theta + B_z(r) e_z
p = p(r)
```

The current density follows from Ampere's law:

```text
mu0 J = curl(B)
```

For this geometry,

```text
J_theta = -(1 / mu0) dB_z/dr
J_z     =  (1 / mu0 r) d(r B_theta)/dr
```

The radial component of `J x B` is

```text
(J x B)_r = J_theta B_z - J_z B_theta
```

Substituting the expressions for current gives

```text
dp/dr = -(1 / mu0) B_z dB_z/dr - (1 / mu0 r) B_theta d(r B_theta)/dr
```

Expanding the azimuthal-field term:

```text
(1/r) B_theta d(r B_theta)/dr
= B_theta dB_theta/dr + B_theta^2/r
```

so the radial equilibrium may be written as

```text
dp/dr = -(1 / mu0) [ B_z dB_z/dr + B_theta dB_theta/dr + B_theta^2/r ]
```

or equivalently,

```text
d/dr [ p + (B_z^2 + B_theta^2)/(2 mu0) ] = - B_theta^2 / (mu0 r)
```

The final term is magnetic curvature / hoop stress from the azimuthal field. This is the kind of baseline relation that any current-channel, helical-field, or edge-current control idea has to respect.

## 3. Relation to current sheets and reconnection

A current sheet is not automatically a screw pinch, but the same MHD bookkeeping applies: magnetic geometry, pressure gradients, and current density are coupled. For a reconnecting sheet, a simplified local description often uses a sheet half-thickness `delta` and length `L`, with aspect ratio

```text
A = L / delta
```

The exploratory TCT framing should therefore avoid saying that thickness is fundamental by itself. A more defensible statement is:

> Current-sheet thickness and aspect ratio may be useful reduced observables if they correlate with reconnection onset, edge transport events, or event severity after controlling for accepted MHD variables.

The proxy fails if it does not add predictive value beyond standard quantities such as edge current density, pressure gradient, magnetic shear, resistivity, Lundquist number, bootstrap current, pedestal parameters, or established edge-stability metrics.

## 4. Plasmoid / tearing language

The phrase `plasmoid marginality` should not be treated as established terminology. Preferred language in this repository is:

- proximity to plasmoid-instability onset,
- distance from a plasmoid-instability threshold,
- current-sheet stability margin,
- tearing / reconnection onset proxy.

A plasmoid-related proxy should be defined relative to known instability criteria, not introduced as an undefined new state variable.

## 5. Bump-on-tail instability: why it is a different baseline

The bump-on-tail instability is a kinetic instability, not the primary model for the TCT edge-current-sheet proxy. It is still useful as a test of baseline plasma knowledge because it shows how instability can follow from the sign of the distribution-function slope near a wave phase velocity.

For electrostatic Langmuir waves with phase velocity

```text
v_phi = omega / k
```

Landau damping or growth depends on the slope of the electron distribution function near `v_phi`. In simplified terms:

```text
partial f0 / partial v < 0  -> damping
partial f0 / partial v > 0  -> growth
```

A beam or bump in the tail of the distribution can create a positive slope region. Particles near the wave phase velocity then transfer energy to the wave, producing instability rather than damping.

This is not the main derivation behind TCT. For TCT, the closer baseline is current-sheet formation, tearing / reconnection onset, edge-MHD stability, and whether reduced geometric observables survive comparison against accepted diagnostics.

## 6. How this constrains the TCT framing

The defensible version of the TCT hypothesis is:

> Current-sheet thickness, sheet aspect ratio, or proximity to reconnection / plasmoid-instability onset may serve as operational proxy observables for some edge-event behavior, but only if they add predictive value beyond accepted MHD and edge-stability variables.

The indefensible version would be:

> Current-sheet thickness is a new fundamental control variable that independently explains tokamak edge stability.

This repository is intended to test the first statement, not claim the second.

## 7. Failure criteria

The TCT-labeled proxy hypothesis should be weakened or rejected if:

1. Sheet thickness or aspect ratio does not add predictive value beyond standard edge variables.
2. Proxy improvements disappear under a real M3D-C1, JOREK, BOUT++, or comparable higher-fidelity workflow.
3. Reduced event-severity metrics do not correlate with accepted diagnostics.
4. Lithium-wall or current-coupling assumptions cannot be represented as plausible boundary conditions, actuators, or measurable diagnostics.
5. The framework cannot reproduce known limiting behavior in benchmark cases.

## 8. Practical next step

The next technical step is not to claim validation. It is to construct benchmark cases where the proxy is expected to fail or succeed for known reasons, then compare the proxy output to accepted diagnostics. A useful result is one that survives falsification attempts, not one that merely improves an internal score.
