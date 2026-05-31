# Screw-pinch force-balance derivation

This is a direct derivation of the cylindrical screw-pinch radial force balance from static single-fluid MHD.

## 1. Static MHD force balance

Start with the single-fluid MHD momentum equation:

```text
rho (dv/dt) = -grad(p) + J x B
```

For static equilibrium with no bulk flow:

```text
v = 0
```

so

```text
0 = -grad(p) + J x B
```

Therefore:

```text
grad(p) = J x B
```

Ampere's law, neglecting displacement current, is:

```text
mu0 J = curl(B)
```

or:

```text
J = (1/mu0) curl(B)
```

## 2. Screw-pinch geometry

Use cylindrical coordinates `(r, theta, z)`. For an axisymmetric screw pinch, take:

```text
B = B_theta(r) e_theta + B_z(r) e_z
B_r = 0
p = p(r)
```

with:

```text
partial/partial theta = 0
partial/partial z = 0
```

This is a screw pinch because the field has both axial and azimuthal components, so magnetic field lines wind helically around the column.

## 3. Compute curl(B)

In cylindrical coordinates:

```text
(curl B)_r = (1/r) partial B_z/partial theta - partial B_theta/partial z
(curl B)_theta = partial B_r/partial z - partial B_z/partial r
(curl B)_z = (1/r) partial(r B_theta)/partial r - (1/r) partial B_r/partial theta
```

Using the symmetry assumptions:

```text
(curl B)_r = 0
(curl B)_theta = -dB_z/dr
(curl B)_z = (1/r) d(r B_theta)/dr
```

Therefore:

```text
J_r = 0
J_theta = -(1/mu0) dB_z/dr
J_z = (1/(mu0 r)) d(r B_theta)/dr
```

## 4. Compute J x B

With:

```text
J = J_theta e_theta + J_z e_z
B = B_theta e_theta + B_z e_z
```

the radial component is:

```text
(J x B)_r = J_theta B_z - J_z B_theta
```

Substitute the current-density components:

```text
(J x B)_r = [-(1/mu0) dB_z/dr] B_z - [(1/(mu0 r)) d(r B_theta)/dr] B_theta
```

So:

```text
(J x B)_r = -(1/mu0) B_z dB_z/dr - (1/(mu0 r)) B_theta d(r B_theta)/dr
```

## 5. Radial force balance

Since `p = p(r)`, the pressure gradient is radial:

```text
grad(p) = (dp/dr) e_r
```

Using `grad(p) = J x B`, the radial equation is:

```text
dp/dr = -(1/mu0) B_z dB_z/dr - (1/(mu0 r)) B_theta d(r B_theta)/dr
```

This is already a valid cylindrical screw-pinch radial equilibrium equation.

## 6. Expanded form

Expand the azimuthal-field term:

```text
d(r B_theta)/dr = B_theta + r dB_theta/dr
```

so:

```text
(1/r) B_theta d(r B_theta)/dr = B_theta^2/r + B_theta dB_theta/dr
```

Substitute:

```text
dp/dr = -(1/mu0) [B_z dB_z/dr + B_theta dB_theta/dr + B_theta^2/r]
```

Use:

```text
B_z dB_z/dr = d(B_z^2/2)/dr
B_theta dB_theta/dr = d(B_theta^2/2)/dr
```

Then:

```text
dp/dr = -d/dr [(B_z^2 + B_theta^2)/(2 mu0)] - B_theta^2/(mu0 r)
```

Move the magnetic-pressure-gradient term to the left:

```text
d/dr [p + (B_z^2 + B_theta^2)/(2 mu0)] = -B_theta^2/(mu0 r)
```

Since:

```text
B^2 = B_z^2 + B_theta^2
```

the compact screw-pinch force-balance relation is:

```text
d/dr [p + B^2/(2 mu0)] = -B_theta^2/(mu0 r)
```

## 7. Interpretation

The term:

```text
p + B^2/(2 mu0)
```

is plasma pressure plus magnetic pressure.

The right-hand side:

```text
-B_theta^2/(mu0 r)
```

is the inward magnetic-tension / hoop-stress term caused by the azimuthal magnetic field.

So the screw-pinch radial equilibrium says:

```text
radial gradient of total pressure = inward azimuthal-field tension
```

This is a standard MHD force-balance result.

## 8. Relevance to the TCT-labeled work

This derivation is not proof of TCT. It is baseline MHD bookkeeping.

Any proposed edge-current, current-sheet, helical-field, lithium-wall-current, or TCT-labeled proxy must either remain consistent with this kind of MHD force balance or clearly state when a more complete model is being used.

The defensible TCT-related question is:

> Can current-sheet thickness, sheet aspect ratio, or proximity to reconnection onset serve as useful reduced observables after comparison against accepted MHD and edge-stability diagnostics?

If they do not add predictive value beyond established quantities, the proxy framing should be rejected or reduced to ordinary reconnection / edge-MHD terminology.
