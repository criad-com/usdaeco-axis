#!/usr/bin/env python3
"""Author, derive, validate and optionally publish the minimal axis example."""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
KIT = Path(os.environ.get("TOOLCHAIN_DIR", ROOT.parent / "usdaeco-toolchain"))
# check_example removes PYTHONPATH in its child: restore the explicit core root.
CORE = Path(os.environ.get("CORE_DIR", ROOT.parent / "usdaeco-core"))
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(KIT / "tools"), str(CORE)]

from check import load_core_validators
from usdaeco_axis import register_plugins
from usdaeco_axis.example import hook, load_axis_validators
from usdaeco_check.example import run_example


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if any(os.environ.get(key) for key in ("AECO_DATACENTRE_ROOT", "AECO_DATACENTRE_STAGE")):
        parser.error("this minimal example requires its own source; unset data-centre source overrides")
    os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
    register_plugins()
    core_names = load_core_validators()
    axis_names = load_axis_validators()
    print(f"== stage: validators ({len(core_names)} core, {len(axis_names)} axis; core Python plugin imported)", flush=True)
    example = Path(__file__).resolve().parent
    manifest = run_example(example, hook, minimal=example / "base.usda",
                           keywords=[], publish=args.publish)
    print(f"Example: {manifest['result']['prim_count']} prims; 0 errors, 0 warnings; {manifest['result']['bytes']} result bytes")


if __name__ == "__main__":
    main()
