# Public-name release verification

Version 0.1.4, measured with Python 3.13.12 and OpenUSD 26.8. Five public
references now name github.com/criad-com. Only the toolchain dependency pin
changes, from v0.3.5 to v0.3.8; core v0.9.2 and data-centre v0.4.5 remain pinned.
The [JSON record](public-name-verification.json) records the measurements.

| Acceptance | Result |
|---|---|
| Full check.py gate | **54 checks, 0 failed, 0 not run** |
| Structure under toolchain v0.3.8 | **29 PASS, 0 FAIL**; S20 inapplicable to a library |
| S05 / S25 | Public input URLs and sanitization pass |
| pytest from source | **21 passed, 5 subtests passed**; no package installation |
| Old public references | **0** in tracked repository files |
| Release metadata | library.json, pyproject.toml, Python package and resource plugin report **0.1.4** |
| Core / axis validators | **8 / 3** rules loaded through UsdValidation |
| Validation execution | Missing core import fails loudly; missing exact tolerance raises **1** E15 warning |
| Example | **47 prims**, **0 findings**, fresh normalized crate and owned layers match |
| Preserved artifacts | **13 files** byte-identical to the release baseline: schema files, baseline, results and PNGs |
| Example manifest | Only `pins.toolchain.ref` changes; result inventory and hashes stay unchanged |
| Nix | **1 attempt**, exit **1**, **0 checks completed**; not proven |

The full gate used clean, separate source checkouts of toolchain v0.3.8
(`4ec5051c419ef056dba594e64be661cb41810275`) and core v0.9.2
(`11000b2ca7a2f560bfcd1ffd439bf9b71a5f5c18`). The toolchain release tag was
verified on the source service. Core's committed `usdAeco` resource directory
was used directly. Shared sibling checkouts were not built or modified.

## Reproduce

Follow the README setup with exact tagged source checkouts. Register the core
resource plugin and make its Python validators importable:

```sh
export CORE_PLUGIN_DIR="$CORE_DIR/usdAeco"
env -u PYTHONPATH PYTHONPATH="$CORE_DIR:$PWD" "$PYTHON" check.py
env -u PYTHONPATH "$PYTHON" -m pytest -q
```

The standard public Nix command and external source override instructions
are in the README. This release made one offline `nix flake check` attempt,
with exact local source overrides for direct and relevant transitive family
inputs, HTTP connections disabled, no substitutes and no builders. Resolution
reached `toolchain/aeco-toolchain/openusd`; its pinned commit lookup reported
HTTP 404. No Nix build or check completed, and no second attempt was made.

## Deviations

- Producer stamps previously followed every package version bump, which would
  make unchanged committed results fail the freshness gate. The package now
  reports 0.1.4 while the unchanged derivation and presentation retain producer
  version 0.1.3. The consumer helper checks the package version against plugin
  metadata and uses the producer version to identify derived guides. Future
  derivation changes must advance `PRODUCER_VERSION` and republish results.
- S22 and the freshness gate require manifest pins to match dependencies.json.
  The example manifest therefore updates its toolchain pin without a result
  republish. No manifest embeds a public URL.
- The existing adapter now includes the pinned toolchain's S29 rule for the
  minimal example and enumerates all rules instead of stopping at S28.
- Nix remains not proven because of the upstream OpenUSD input lookup. That
  transitive dependency belongs to the pinned processing toolchain and was
  left unchanged.
- The minimal example uses no data-centre stage. Optional consumer integration
  checks were not rerun for this release.
