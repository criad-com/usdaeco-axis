# Shared path axes

## 1 The problem

Walls, pipes, beams and other path elements need the same local path drivers.
A shared API lets an editor change a location curve while a host or derivation
reports length and emits display geometry. A classified traversal produces a
plan without understanding each kind library's section contract.

## 2 The data as it arrives

The driver set comes from an IFC Axis representation, an extrusion's placement
and depth, or a native location curve. Start, end and an optional circular-arc
point are expressed in the element's local frame in SI metres. The element's
transform places the path. Identity and IFC classification already live on the
core prim. A reported length is evidence from a host or derivation, not input.

## 3 The model in USD

Apply AecoAxisAPI to an Imageable. It carries four driver properties and one
derived length. The definition of length carries `aecoDerived = true` as property
metadata. The metadata is registered by core; no stage authors that declaration.

`aeco-axis derive` writes only length opinions and BasisCurves children named
Axis into a separate named layer. Curves have guide purpose and the core derived
mark: source identity, role axis, approximation exact for straight lines or
arcSegmented for circular arcs, tolerance and producer stamp. Curves use stage
linear units; driver and length values remain metres. Axis derives no body and
introduces no new identity. A composed root can be written using relative paths.

## 4 Workflow

Run `examples/minimal/run.py --publish` in the environment described by the
repository README. The shared harness authors drivers, derives four guides,
validates them and publishes a standalone result. Consumers use
`aeco-axis derive` to regenerate guides from their own driver stages.

## 5 Validation

| Rule | Severity | Meaning |
|---|---|---|
| AxisDegenerate | error | Endpoints are coincident or non-finite; an unsupported curve cannot be derived |
| AxisLengthMismatch | warn | Nonzero reported length differs from evaluated line/arc length by more than 0.001 × max(1 m, length) |
| AxisArcPointMissing | warn | Arc point coincides with an endpoint, is non-finite or the three points are collinear |
| ExactWithoutTolerance (core E15) | warn | Exact geometry has missing, non-positive or non-finite tolerance in metres |

The keyword is `UsdAecoAxisValidators`; each rule is registered as
`usdAecoAxisValidators:<Rule>Checker`. Length 0 means unreported. Circular
length is analytic, while the guide is a segmented approximation. Every guide
authors a positive `aeco:derived:tolerance` in its dedicated derived layer.
Exact lines declare **1e-9 m**, the numerical precision of derivation from
double-precision endpoints, or the maximum float32 point-encoding error if
larger. For arcs, the chord deviation is
`r * (1 - cos(abs(sweep) / (2 * segments)))`; the implementation evaluates the
equivalent `2 * r * sin(abs(sweep) / (4 * segments))²` without cancellation.
Its tolerance adds maximum point-encoding error to that deviation, with a
1e-9 m floor. These values remain metres for non-metre stages.

`check.py` requires an importable `usdAecoValidators` Python plugin, loads all
eight core rules through `UsdValidation.ValidationRegistry`, and runs the core
and axis keywords. A deliberately blocked tolerance must produce exactly one
`ExactWithoutTolerance` warning, proving the core rule executed. Separate line
and arc tests check the numerical bound and stage-unit conversion.

The CLI additionally reports AxisMissing when a classified path element with
geometry lacks the API. Geometry owned by nested elements does not count as the
parent's body. No classification token is invented: the traversal reads IFC
classification codes. Guide-only elements count as having geometry.

## 6 The example on the demo data centre

The [minimal example](../examples/minimal/README.md) authors four paths under
the synthetic facility `demo-datacentre-01`: three exact straight guides and a
32-chord quarter circle. Lengths are 3, π/2, 2 and 2 m. Its committed crate,
owned layers and plugin-free render carry the complete review result.
The shared harness records a data-centre metadata pin but composes only the
minimal seed. Full facility studies belong to usdaeco-wall and usdaeco-pipe.

## 7 Trade-offs and alternatives

The driver set enables editing and a cheap plan traversal. A representation-first
route can have exact bodies without any drivers, which is why this library is
optional and the axis is no longer core. A straight guide can be exact as a
path; a sampled circular guide explicitly declares arcSegmented. Host length
drift warns because the host may include effects beyond a simple driver path.

Derivation validates every axis before replacing its dedicated layer. It refuses
input layers and outputs owned by other tools. Repeated derivations produce the
same layer bytes for the same drivers and runtime.

## 8 Out of scope and open questions

Body generation, joins, openings, section choice, native host transactions,
exact solid evaluation and non-circular splines belong elsewhere. The three
straight segments prove guide lengths to 1e-9; circular guide chord lengths
intentionally differ from analytic arc length. Cross-runtime identical render
pixels are not promised.

## 9 Status

Version 0.1.4; schema unchanged from v0.1.1, built against
core v0.9.2. [Verification](public-name-verification.md) records exact checked dependencies,
the schema and test results, rendered output and the Nix limitation.
