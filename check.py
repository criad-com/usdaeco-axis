#!/usr/bin/env python3
"""Build and check the axis contract; print N checks, M failed."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
KIT = Path(os.environ.get("TOOLCHAIN_DIR", HERE.parent / "usdaeco-toolchain"))
sys.path[:0] = [str(KIT / "tools"), str(HERE), str(HERE / "tools"), str(HERE / "testenv")]
from usdaeco_check import Report, can_apply, plugin_requires, registry_probe, validate_examples
from usdaeco_axis.structure import check_structure
from usdaeco_check.example import check_example


def load_core_validators():
    """Require an importable core Python plugin and load every declared rule."""
    from pxr import Plug, UsdValidation
    try:
        spec = importlib.util.find_spec("usdAecoValidators")
    except ImportError as exc:
        raise RuntimeError("Cannot import usdAecoValidators: make the core checkout importable through PYTHONPATH") from exc
    if spec is None or not spec.submodule_search_locations:
        raise RuntimeError("Cannot import usdAecoValidators: set PYTHONPATH to the core checkout (or its installed python directory)")
    Plug.Registry().RegisterPlugins(next(iter(spec.submodule_search_locations)))
    registry = UsdValidation.ValidationRegistry()
    metadata = registry.GetValidatorMetadataForKeyword("UsdAecoValidators")
    names = [m.name for m in metadata]
    if "usdAecoValidators:ExactWithoutToleranceChecker" not in names:
        raise RuntimeError("Core validators must include ExactWithoutToleranceChecker")
    try:
        loaded = registry.GetOrLoadValidatorsByName(names)
    except Exception as exc:
        raise RuntimeError("Cannot import/load usdAecoValidators; check the core Python dependencies") from exc
    plugin = Plug.Registry().GetPluginWithName("usdAecoValidators")
    if (len(loaded) != len(names) or not all(loaded) or not plugin.isLoaded
            or "usdAecoValidators" not in sys.modules):
        raise RuntimeError("usdAecoValidators did not load all declared rules")
    return names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-plugin", default=os.environ.get("CORE_PLUGIN_DIR", str(HERE.parent / "usdaeco-core/out/plugins/usdAeco/resources")))
    args = parser.parse_args()
    core = Path(args.core_plugin).resolve()
    os.environ["CORE_PLUGIN_DIR"] = str(core)
    os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
    report = Report()
    print("== stage: build", flush=True)
    env = {**os.environ, "PYTHON": sys.executable, "CORE_PLUGIN_DIR": str(core)}
    env.pop("PYTHONPATH", None); env.pop("PXR_PLUGINPATH_NAME", None)
    out = HERE / "out"; out.mkdir(exist_ok=True)
    with (out / "build.log").open("w") as log:
        build = subprocess.run(["bash", str(HERE / "build.sh"), "--install-root", str(out)], env=env, stdout=log, stderr=subprocess.STDOUT)
    if not report.check("build with declared core dependency", build.returncode == 0, "out/build.log"):
        return report.finish()
    print("== stage: structure", flush=True)
    for result in check_structure(HERE, deps=[core]):
        report.add(result)
    print("== stage: registry", flush=True)
    if not report.add(plugin_requires([core, out / "plugins/usdAecoAxis/resources"])):
        return report.finish()
    from pxr import Plug, Sdf, Usd, UsdGeom, UsdValidation, Tf
    Plug.Registry().RegisterPlugins(str(HERE / "usdAecoAxisValidators"))
    try:
        core_names = load_core_validators()
    except RuntimeError as exc:
        report.check("core Python validators loaded", False, str(exc))
        return report.finish()
    report.check("core Python validators loaded", True, f"{len(core_names)} rules, including E15; usdAecoValidators imported")
    report.add(registry_probe(["AecoAxisAPI"], ["AecoPort"]))
    report.add(can_apply([("Xform", "AecoAxisAPI", True), ("Mesh", "AecoAxisAPI", True), ("Material", "AecoAxisAPI", False), ("AecoSystem", "AecoAxisAPI", False)]))
    definition = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition("AecoAxisAPI")
    report.check("five properties, length derived", len(definition.GetPropertyNames()) == 5 and definition.GetPropertyMetadata("aeco:axis:length", "aecoDerived") is True)
    report.check("four drivers unmarked", all(not definition.GetPropertyMetadata("aeco:axis:" + n, "aecoDerived") for n in ("start", "end", "curve", "arcPoint")))
    report.check("registered type belongs to axis", not Tf.Type.FindByName("UsdAecoAxisAxisAPI").isUnknown and Tf.Type.FindByName("UsdAecoAxisAPI").isUnknown)
    registry = UsdValidation.ValidationRegistry()
    metadata = registry.GetValidatorMetadataForKeyword("UsdAecoAxisValidators")
    report.check("validator plugin listing", len(metadata) == 3 and all(registry.GetOrLoadValidatorByName(m.name) for m in metadata))
    from usdaeco_check.validation import run
    keywords = ["UsdAecoValidators", "UsdAecoAxisValidators"]
    report.add(validate_examples(HERE / "usdAecoAxis/examples", validators=[lambda stage: run(stage, keywords)]))
    print("== stage: derive and plan", flush=True)
    from usdaeco_axis.derive import derive
    from usdaeco_axis.cli import compose
    from usdaeco_axis.validators import check_plan, path_elements
    source = HERE / "usdAecoAxis/examples/minimal.usda"
    stage = Usd.Stage.Open(str(source)); before = source.read_bytes()
    with tempfile.TemporaryDirectory(dir=out) as temporary:
        destination = Path(temporary)
        target = destination / "axis.derived.usda"
        stats = derive(stage, target)
        composed = Usd.Stage.Open(compose(source, target, destination / "run.usda"))
        curves = [UsdGeom.BasisCurves(p) for p in composed.Traverse() if p.IsA(UsdGeom.BasisCurves)]
        report.check("minimal run yields three Axis guides", stats["axes"] == len(curves) == 3 and all(c.GetPrim().GetName() == "Axis" and c.ComputePurpose() == "guide" for c in curves))
        differences = []
        for c in curves:
            points = c.GetPointsAttr().Get()
            length = sum((b-a).GetLength() for a,b in zip(points, points[1:]))
            differences.append(abs(length - c.GetPrim().GetParent().GetAttribute("aeco:axis:length").Get()))
        report.check("lengths agree within 1e-9", len(differences) == 3 and max(differences) <= 1e-9, f"lengths={stats['lengths']}, max delta={max(differences, default=0):g}")
        report.check("derived run has zero core and axis validator findings", run(composed, keywords) == [])
        report.check("exact guides declare 1e-9 m tolerance", all(c.GetPrim().GetAttribute("aeco:derived:tolerance").HasAuthoredValueOpinion() and c.GetPrim().GetAttribute("aeco:derived:tolerance").Get() == 1e-9 for c in curves))
        baseline = Sdf.Layer.FindOrOpen(str(HERE / "testenv/baseline/minimal.derived.usda"))
        report.check("minimal derived layer matches committed baseline", baseline.ExportToString() == Sdf.Layer.FindOrOpen(str(target)).ExportToString())
        with Usd.EditContext(composed, composed.GetSessionLayer()):
            curves[0].GetPrim().GetAttribute("aeco:derived:tolerance").Block()
        detected = run(composed, keywords)
        report.check("core E15 detects missing exact tolerance", len(detected) == 1 and detected[0].GetName() == "ExactWithoutTolerance" and detected[0].GetType() == UsdValidation.ValidationErrorType.Warn)
        composed.GetSessionLayer().Clear()
        report.check("plan is a traversal", len(list(path_elements(composed))) == 3 and check_plan(composed) == [])
        composed.GetPrimAtPath("/Run/Pipe2").RemoveAPI("AecoAxisAPI")
        report.check("missing axis is detected", [f["path"] for f in check_plan(composed)] == ["/Run/Pipe2"])
        report.check("source drivers unchanged", source.read_bytes() == before and all(not p.GetAttribute("aeco:axis:length").HasAuthoredValueOpinion() for p in stage.Traverse() if p.HasAPI("AecoAxisAPI")))
        first = target.read_bytes(); derive(stage, target)
        report.check("derivation is idempotent", target.read_bytes() == first)
        vanilla = subprocess.run([sys.executable, "-c", "from pxr import Usd,UsdGeom; import sys; s=Usd.Stage.Open(sys.argv[1]); assert not s.GetCompositionErrors(); assert sum(p.IsA(UsdGeom.BasisCurves) for p in s.Traverse()) == 3", str(destination / "run.usda")], env=env, capture_output=True, text=True)
        report.check("derived guides compose plugin-free", vanilla.returncode == 0, vanilla.stderr[-300:])
    from testUsdAecoAxisValidators import fixture, errors
    for token, configure in [("AxisDegenerate", {"end": (0,0,0)}), ("AxisLengthMismatch", {"length": 8.0}), ("AxisArcPointMissing", {"curve": "arc"})]:
        seeded, prim = fixture()
        for key, value in configure.items(): prim.GetAttribute("aeco:axis:" + key).Set(value)
        report.check("seeded " + token, [e.GetName() for e in errors(seeded)] == [token])
    print("== stage: published example (S27 and S28)", flush=True)
    report.add(check_example(HERE / "examples/minimal"))
    return report.finish()


if __name__ == "__main__":
    raise SystemExit(main())
