#!/usr/bin/env python3
"""Validate sibling examples before/after deriving guides into temporary layers.

Run with the core checkout importable, as for check.py. Siblings are read only.
"""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from check import load_core_validators


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("pipe", "wall"))
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    name = "usdAeco" + args.kind.title()
    source = repo / name / "examples/minimal.usda"
    before = source.read_bytes()
    os.environ["AECO_AXIS_ROOT"] = str(ROOT)
    os.environ["AXIS_PLUGIN_DIR"] = str(ROOT / "out/plugins/usdAecoAxis/resources")
    sys.path.insert(0, str(repo / "tools"))
    library = importlib.import_module("usdaeco_" + args.kind)
    library.register_plugins()
    from pxr import Plug, Usd, UsdGeom
    Plug.Registry().RegisterPlugins(str(ROOT / "usdAecoAxisValidators"))
    names = load_core_validators()
    from usdaeco_axis import __version__
    from usdaeco_axis.derive import PRODUCER_VERSION, derive
    from usdaeco_axis.cli import compose
    from usdaeco_check.validation import run
    validators = importlib.import_module("usdaeco_" + args.kind + ".validators")
    axis = Plug.Registry().GetPluginWithName("usdAecoAxis")
    assert axis.metadata["aeco"]["version"] == __version__
    assert Path(axis.path).resolve() == (ROOT / "out/plugins/usdAecoAxis/resources").resolve()

    def findings(stage):
        # The same core + library + built-in selection as the sibling gate row.
        errors, warnings = validators.split(validators.validate_stage(stage, include_core=True))
        return {"errors": len(errors), "warnings": len(warnings),
                "names": sorted(e.GetName() for e in errors + warnings),
                "sites": sorted(str(site.GetPrim().GetPath()) for e in errors + warnings for site in e.GetSites())}

    stage = Usd.Stage.Open(str(source))
    raw = findings(stage)
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "axis.derived.usda"
        stats = derive(stage, target)
        composed = Usd.Stage.Open(compose(source, target, Path(tmp) / "run.usda"))
        derived = findings(composed)
        assert run(composed, ["UsdAecoAxisValidators"]) == []
        guides = [p for p in composed.Traverse() if p.IsA(UsdGeom.BasisCurves)
                  and p.GetAttribute("aeco:derived:stamp").Get() == "aeco-axis " + PRODUCER_VERSION]
        assert len(guides) == stats["axes"] > 0
        assert all(p.GetAttribute("aeco:derived:tolerance").Get() > 0 for p in guides)
    assert source.read_bytes() == before
    print(json.dumps({"repo": repo.name, "version": json.loads((repo / "library.json").read_text())["version"],
                      "axis_version": __version__, "core_rules_loaded": len(names),
                      "source_sha256": hashlib.sha256(before).hexdigest(), "source_unchanged": True,
                      "untouched": raw, "rederived": derived, "axes": stats["axes"]}, indent=2))
    return int(bool(derived["errors"] or derived["warnings"]))


if __name__ == "__main__":
    raise SystemExit(main())
