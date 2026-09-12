# Minimal axis example

Open [result/example.usdc](result/example.usdc) with stock USD. It is flattened,
self-contained and needs no family plugins or sibling checkouts. The facility
falls back to Xform. Enable guides to inspect the original Axis curves.

![Four path elements](result/vanilla.png)

The run authors three straight paths and a quarter-circle bend, then derives
four BasisCurves guides in their own layer. Lengths are 3, π/2, 2 and 2 metres.
The three straight guides declare `exact` with tolerance 1e-9 m. The bend uses
32 chords, declares `arcSegmented`, and records chord deviation plus point
encoding error. All eight core and three axis validators execute through
UsdValidation; the expected result is **0 errors, 0 warnings**.

The cylinders are schematic strokes with a drawing radius of 0.045 m. They
follow the guide points and carry `purpose = proxy`, `approx = defaultDims`,
and links to their source guides. Their radius is not a pipe diameter. The
original axes retain `purpose = guide`. No body generation is claimed.

From the repository root, in the environment described by the root README:

```sh
env -u PYTHONPATH PYTHONPATH="$CORE_DIR:$PWD" "$PYTHON" examples/minimal/run.py
env -u PYTHONPATH PYTHONPATH="$CORE_DIR:$PWD" "$PYTHON" examples/minimal/run.py --publish
usdview examples/minimal/result/example.usdc
```

Ordinary runs write `out/`; `--publish` also refreshes `result/`, `renders/`
and `manifest.json`. Expected findings are never rewritten. The gate compares
fresh output with committed output and independently re-renders the committed
crate in an isolated process with no family plugins.

| Layer | Purpose |
|---|---|
| base.usda | Empty metre/Z-up root and AecoFacility fallback |
| inputs/cameras.usda | Fixed overview camera |
| result/layers/out/drivers.usda | Facility identity and four editable path driver sets |
| result/layers/out/axis.derived.usda | Derived lengths, guide points and tolerance |
| result/layers/out/presentation.usda | Schematic strokes for ordinary imaging |
| result/layers/out/base.usda | Archived seed layer |

This is a minimal library example labelled `demo-datacentre-01`. The shared
harness requires a data-centre pin, so the manifest records v0.4.8 and
`source.mode = minimal`; no data-centre release stage is composed or tested.
The toolchain's unchanged S21–S28 functions run on this directory through the
library's structure adapter; its default library rules would skip examples.
