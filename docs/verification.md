# Verification

Version 0.1.2, measured with Python 3.13 and OpenUSD 26.8, core v0.9.2 and
toolchain v0.3.2. The [JSON record](verification.json) includes the exact
checked revisions, manifest sizes and limitations.

| Acceptance | Result |
|---|---|
| check.py | **53 checks, 0 failed** |
| pytest | **21 passed**, plus 5 successful subtests |
| Structure | **28 PASS, 0 FAIL**; S21–S28 executed on the minimal example; S20 inapplicable to a library |
| MIT | LICENSE, README Licence, library.json agree; S01 passes |
| Core loading | **8/8 rules**, including E15; Python module imported and plugin loaded |
| Axis loading | **3/3 rules** through UsdValidation |
| Example findings | **0 errors, 0 warnings** |
| Non-vacuous validation | Missing core import fails; blocking exact tolerance produces exactly **1 E15 warning** |
| Paths | **4 guides**: 3 exact straight paths plus a circular bend with **32 chords** |
| Lengths | **3, π/2, 2, 2 m**; exact guides declare **1e-9 m** tolerance |
| Source fixture | Three original straight guides still match the committed baseline; only the producer version changed |
| Schema | Source and generated schema byte-identical to v0.1.1 |
| Standalone result | **47 prims**, relocated plugin-free; **0 composition errors**, complete AecoFacility → Xform fallback |
| Freshness | Flattened crate normalized serialization and owned layer bytes match a fresh run |
| Crate | **9,935 bytes** |
| Owned layers | **5 USDA files, 46,607 bytes total**; largest **38,532 bytes** |
| Complete result/ | **129,979 bytes**, cap 10,000,000 bytes |
| Owned overview render | **1280×800, 72,693 bytes**, non-uniform |
| Vanilla render | **1280×800, 72,762 bytes**, non-uniform; fresh process with no family plugins |
| Term sweep | **PASS**, including committed result text layers |
| Nix | **1 attempt**, exit **1** during input resolution; **not proven** |

The source fixture's existing length/ownership/idempotence tests remain in the
gate. The new example tests check published line/arc lengths and tolerances,
registered validation and the absence of derived geometry in the driver layer.
The stock render is visually inspected and shows all four coloured path elements.

## Reproduce

Use the setup in the repository README. The measured core checkout has a stale
built resource descriptor (v0.9.1), so these checks selected its committed
v0.9.2 source resource plugin:

```sh
export CORE_PLUGIN_DIR="$CORE_DIR/usdAeco"
env -u PYTHONPATH PYTHONPATH="$CORE_DIR:$PWD" "$PYTHON" check.py
env -u PYTHONPATH "$PYTHON" -m pytest -q
```

The source plugin includes schema.usda, generatedSchema.usda and plugInfo.json
and is accepted by the shared builder as a dependency. No sibling checkout was
built or changed. The gate's plugin requirement row reports **usdAeco 0.9.2,
usdAecoAxis 0.1.2**. The example runner restores CORE_DIR to its import path
when the shared harness launches it with PYTHONPATH removed.

## Deviations

- Toolchain v0.3.2 skips library examples and fixes its default example path
  to examples/datacentre. The local adapter applies the unchanged example rule
  functions to examples/minimal; no failure is converted into a pass.
- The shared harness requires a data-centre pin even in minimal mode.
  dependencies.json records v0.4.2, and the manifest explicitly records
  `source.mode = minimal`. No data-centre release composition is claimed.
- Core's pre-existing built descriptor is v0.9.1. The v0.9.2 committed source
  plugin was used through the override above; the stale installation remains
  for its owner to refresh.
- USD 26.8 validator sites expose GetPrim/GetProperty. The example hook runs
  the shared registry selection and serializes those sites directly; the
  harness's GetPath-based serializer is bypassed. Findings are not filtered.
- Straight guides declare exactness; a segmented circular guide declares
  arcSegmented. The review cylinders are schematic proxies, with a drawing
  radius unrelated to a physical pipe section.
- The single Nix attempt used offline mode, zero HTTP connections, no
  substitutes and local overrides for the three direct inputs. Resolution
  reported HTTP 404 for core's transitive data-centre v0.4.1 input. No Nix
  checks completed, and no second attempt was made.
