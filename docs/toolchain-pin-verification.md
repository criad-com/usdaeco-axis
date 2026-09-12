# Public re-pin verification

Version 0.1.5, measured with Python 3.13.12, OpenUSD 26.8 and Pillow 12.3.0
against release baseline `3717906cd0488b8357ff83b463553156eaddc62d`.
The already prepared v0.1.5 patch release now selects published family tags.
Library, Python package and resource-plugin versions agree; requirement ranges
remain unchanged. Earlier verification files retain their historical pins.

| Acceptance | Result |
|---|---|
| check.py | **54 checks, 0 failed, 0 not run** |
| Structure with toolchain v0.3.10 | **29 PASS, 0 FAIL**; included in the full gate; S20 inapplicable to a library |
| S05 | PASS: tag-only family refs and flake/package version agreement |
| pytest from source | **21 passed, 5 subtests passed**; no installation or setuptools |
| Core / axis validators | **8 / 3** loaded through UsdValidation; seeded missing tolerance detected |
| Release metadata | library.json, pyproject.toml, source package and resource plugin report **0.1.5** |
| Direct pins | **3 / 3** target tags and exact checked revisions agree with the stable checkouts |
| Requirement ranges | **0 changes**; core v0.9.4 satisfies `>=0.9.2,<1.0` |
| Example | **47 prims**, **0 findings**, **129,979 result bytes**, source mode `minimal` |
| Republish | Runner completed with **8 core / 3 axis** validators and fresh overview/vanilla renders |
| Preserved artifacts | **11 byte-identical files**: 2 schemas, 1 crate, 5 archived layers, 3 images |
| Result changes | Source pin in result/README.md; manifest pins and that README's hash only |
| Public family tag lookups | **4 resolved, 1 unproven**, including the two nested family inputs |
| Legacy public-org references | **0** |
| Publication sweep | **64 files, 0 findings**, including decoded USD and image metadata |
| git diff --check | Clean |
| Offline Nix | **1 attempt**, exit **1**, **45.845 s**; **2 check derivations evaluated, 0 completed** |

[Machine-readable evidence](public-repin-verification.json) records artifact
hashes, changed manifest fields, fresh-render measurements and public tag
revisions separately from the checked source revisions.

## Pins and build shape

| Input | Tag | Checked source revision |
|---|---|---|
| toolchain | v0.3.10 | 59d3da5ff5114089b54efaaae38efdd7fe1b8e73 |
| core | v0.9.4 | 80a099e14e7bb825b207548d0a4f8a93e9ffa62f |
| datacentre | v0.4.8 | 9e22b14c4909e50806805e735f93b1b425ac48cb |
| toolchain/aeco-toolchain | v0.4.0 | 71c86d54aa1e4be180a301a089d9a40e727758cb |
| toolchain/core test fixture | v0.9.2 | 11000b2ca7a2f560bfcd1ffd439bf9b71a5f5c18 |

Direct revisions were resolved from the source service's release tags and
matched against the read-only sibling checkouts. Public orphan commits differ,
so flake URLs select tags and never these source revisions. Core and datacentre
are source inputs (`flake = false`). The shared toolchain builds the core
plugin, preserving its companion-package installation, without evaluating
core's older dependency graph. The toolchain's two nested family refs also
select release tags. Non-family upstream pins are unchanged.

Toolchain 0.3.10's CHANGELOG adds tag enforcement and preserves the upstream
USD output and Python interface. Core 0.9.3/0.9.4 change publication provenance
and package metadata while preserving the schema contract. Datacentre 0.4.6
through 0.4.8 preserve published stages; this minimal example does not load
them. No dependency behaviour change affects the derived result.

## Republish and byte comparison

The documented `examples/minimal/run.py --publish` rebuilt the complete
example with the new pins. The crate and five archived layers matched the
release baseline byte-for-byte immediately after publication. Derivation and
presentation retain their existing v0.1.3 producer stamps because their code
is unchanged. The generated result README changes only v0.4.5 to v0.4.8.

Fresh renders were both 1280 by 800 pixels and nonblank: 2,779 overview colours
and 2,817 vanilla colours. Their mean absolute channel differences from the
committed images were 0.017088 and 0.017083 on a 0–255 scale. S28 explicitly
does not require identical sampled PNG bytes between runs. After this fresh
render proof, the existing PNGs and their matching manifest inventories were
retained. The final gate re-rendered the result plugin-free and passed S28;
its fresh example completed in 11.698 seconds against a 180-second budget.
The final result diff is provenance-only.

## Reproduce

Use the README environment with the pinned source checkouts:

```sh
export CORE_PLUGIN_DIR="$CORE_DIR/usdAeco"
export PYTHONDONTWRITEBYTECODE=1
env -u PYTHONPATH -u PXR_PLUGINPATH_NAME ./build.sh
env -u PYTHONPATH -u PXR_PLUGINPATH_NAME PYTHONPATH="$CORE_DIR:$PWD" "$PYTHON" examples/minimal/run.py --publish
env -u PYTHONPATH -u PXR_PLUGINPATH_NAME PYTHONPATH="$CORE_DIR:$PWD" "$PYTHON" check.py
env -u PYTHONPATH -u PXR_PLUGINPATH_NAME "$PYTHON" -m pytest -q
git diff --check
```

For the one offline Nix attempt, direct overrides selected the stable siblings;
nested overrides selected isolated exact v0.4.0 and v0.9.2 source copies.
Each variable below names a physical directory with no symlink ancestor:

```sh
nix flake check --offline --no-write-lock-file --max-jobs 0 \
  --option http-connections 0 --option substituters '' --option builders '' \
  --override-input toolchain "path:$TOOLCHAIN_DIR" \
  --override-input core "path:$CORE_DIR" \
  --override-input datacentre "path:$DATACENTRE_DIR" \
  --override-input toolchain/aeco-toolchain "path:$AECO_TOOLCHAIN_DIR" \
  --override-input toolchain/core "path:$CORE_FIXTURE_DIR"
```

Nix evaluated both packages, both repository check derivations, the dev shell
and both apps for aarch64-darwin. It then failed on an uncached prerequisite
with local jobs, remote builders and substituters disabled. No repository
check completed and no lockfile was written. No retry was made for these pins.

## Deviations

- Keep the already prepared, unreleased **v0.1.5** patch version and existing
  pull request, as directed during review; no second patch bump is needed.
- Anonymous GitHub lookup of datacentre v0.4.8 requested authentication,
  including with credential helpers disabled. Retain the prescribed tag;
  public availability is **not proven**. The other four family tags resolved.
- Nix execution and public flake resolution remain **not proven**. Linux was
  not evaluated. The earlier toolchain-only candidate had its own failed
  attempt; the final pin set received exactly one attempt recorded above.
- The minimal example carries a datacentre metadata pin but loads its own
  source stage. Optional consumer integration checks were not rerun.
- Retain the existing sampled PNGs after fresh render validation so the final
  publication diff contains provenance only. Geometry and layers required no
  normalization or restoration.
