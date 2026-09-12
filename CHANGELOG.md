# Changelog

## 0.1.5

- public re-pin: toolchain v0.3.10, core v0.9.4, datacentre v0.4.8;
  record each checked revision alongside its public release tag.
- Build core from its source input with the pinned shared toolchain, avoiding
  recursive evaluation of the core release's older flake inputs.
- Keep supported requirement ranges and the unreleased v0.1.5 package version.
  Republish the example through its runner; retain the v0.1.3 derivation and
  presentation stamps because those implementations are unchanged.

## 0.1.4

- Public names → github.com/criad-com; pin toolchain v0.3.8.
- Preserve the v0.1.3 derivation producer stamp and committed results;
  update only the example manifest toolchain pin for the current checks.
- Include S29 from the pinned toolchain in the minimal-example structure gate.

## 0.1.3

- Re-pin to train aeco-0.7.0: toolchain v0.3.5, core v0.9.2 and
  datacentre v0.4.5; keep the supported requirement ranges unchanged.
- Refresh example pin provenance and patch-version producer stamps; schema,
  geometry, drivers, findings and committed renders are unchanged.

## 0.1.2

- Publish under MIT and pin core v0.9.2 and toolchain v0.3.2.
- Add the minimal example harness: three straight paths, a circular bend,
  separate driver/derived/presentation layers and zero core/axis findings.
- Commit the flattened standalone crate, owned USDA layers, overview render
  and a fresh-process stock USD render; check freshness with `check_example`.
- Apply the toolchain's S21–S28 rules to the library's minimal example.
- Preserve the schema source and generated schema unchanged.

## 0.1.1

- Specify the positive 1e-9 m numerical tolerance for exact line derivation;
  retain a larger bound when float32 guide points require it.
- Compute arc chord deviation from the actual radius, sweep and segment count
  using a stable sagitta formula; include point-encoding error in the bound.
- Require the core Python validator plugin in the gate, run its eight rules,
  and seed a missing tolerance to prove E15 executes.
- Add line/arc tolerance regressions, the minimal derived layer baseline and a
  read-only consumer validation runner. The schema is unchanged.
- Pin checked dependencies to core v0.9.1 and toolchain v0.3.0.

## 0.1.0

- Extract AecoAxisAPI unchanged from core into a shared section-tier library.
- Register three Python UsdValidation rules and provide the plan traversal CLI.
- Port line and circular-arc guide derivation from the sync engine into a named
  derived layer; report lengths without editing source drivers.
- Add the three-segment pipe run, Embree image, source tests and public pins.
