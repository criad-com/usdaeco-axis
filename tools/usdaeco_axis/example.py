"""Four path elements, derived guides and schematic strokes for stock imaging."""
import math
import shutil

from pxr import Gf, Sdf, Usd, UsdGeom, UsdValidation
from usdaeco_check.validation import run
from .derive import PRODUCER_VERSION, derive

KEYWORDS = ["UsdAecoValidators", "UsdAecoAxisValidators"]


def load_axis_validators():
    registry = UsdValidation.ValidationRegistry()
    names = [m.name for m in registry.GetValidatorMetadataForKeyword(KEYWORDS[1])]
    if len(names) != 3 or not all(registry.GetOrLoadValidatorsByName(names)):
        raise RuntimeError("all three axis validators must load")
    return names


def author_drivers(stage, layer):
    with Usd.EditContext(stage, layer):
        facility = stage.DefinePrim("/Run/Facility", "AecoFacility")
        facility.CreateAttribute("aeco:id", Sdf.ValueTypeNames.String, custom=False).Set(
            "b9000000-0000-4000-8000-000000000010")
        facility.SetDisplayName("demo-datacentre-01")
        paths = [
            ("Inlet", (0, 0, 0), (3, 0, 0), None),
            ("Bend", (3, 0, 0), (4, 1, 0), (3 + math.sqrt(.5), 1 - math.sqrt(.5), 0)),
            ("Outlet", (4, 1, 0), (4, 3, 0), None),
            ("Riser", (4, 3, 0), (4, 3, 2), None),
        ]
        for index, (name, start, end, arc_point) in enumerate(paths, 1):
            prim = UsdGeom.Xform.Define(stage, facility.GetPath().AppendChild(name)).GetPrim()
            for api in ("AecoElementAPI", "AecoAxisAPI"):
                prim.ApplyAPI(api)
            prim.ApplyAPI("AecoClassificationAPI", "ifc")
            prim.GetAttribute("aeco:id").Set(f"b9000000-0000-4000-8000-{index:012d}")
            prim.GetAttribute("aeco:class:ifc:code").Set("IfcPipeSegment")
            prim.GetAttribute("aeco:axis:start").Set(start)
            prim.GetAttribute("aeco:axis:end").Set(end)
            prim.GetAttribute("aeco:axis:curve").Set("arc" if arc_point else "line")
            if arc_point:
                prim.GetAttribute("aeco:axis:arcPoint").Set(arc_point)
    layer.Save()


def presentation(stage, layer):
    """Cylinder strokes follow every chord; radius is a drawing convention."""
    axes = [UsdGeom.BasisCurves(p) for p in stage.Traverse() if p.IsA(UsdGeom.BasisCurves)]
    colors = ((.12, .58, .88), (.95, .55, .15), (.12, .75, .52), (.65, .35, .85))
    with Usd.EditContext(stage, layer):
        for axis, color in zip(axes, colors):
            points = axis.GetPointsAttr().Get()
            for index, (a, b) in enumerate(zip(points, points[1:])):
                start, end = Gf.Vec3d(a), Gf.Vec3d(b)
                delta = end - start
                stroke = UsdGeom.Cylinder.Define(
                    stage, axis.GetPath().GetParentPath().AppendChild(f"ReviewStroke{index:02d}"))
                stroke.CreateRadiusAttr(.045)
                stroke.CreateHeightAttr(delta.GetLength())
                stroke.CreateAxisAttr("Z")
                stroke.CreatePurposeAttr("proxy")
                stroke.CreateDisplayColorAttr([color])
                transform = Gf.Matrix4d().SetRotate(Gf.Rotation(Gf.Vec3d(0, 0, 1), delta.GetNormalized()))
                transform.SetTranslateOnly((start + end) / 2)
                stroke.MakeMatrixXform().Set(transform)
                prim = stroke.GetPrim()
                prim.ApplyAPI("AecoDerivedGeometryAPI")
                for name, value in {
                    "source": axis.GetPrim().GetAttribute("aeco:derived:source").Get(),
                    "role": "proxy", "approx": "defaultDims",
                    "stamp": "aeco-axis review " + PRODUCER_VERSION,
                }.items():
                    prim.GetAttribute("aeco:derived:" + name).Set(value)
                prim.GetRelationship("aeco:derived:from").SetTargets([axis.GetPath()])
    layer.Save()


def hook(stage, out):
    # Preserve our seed as an owned layer too: the harness excludes source layers.
    shutil.copyfile(out.parent / "base.usda", out / "base.usda")
    drivers = Sdf.Layer.CreateNew(str(out / "drivers.usda"))
    drivers.documentation = "Editable axis drivers; lengths and geometry live in separate derived layers."
    stage.GetRootLayer().subLayerPaths.insert(0, drivers.realPath)
    author_drivers(stage, drivers)
    derived = out / "axis.derived.usda"
    derive(stage, derived, segments=32)
    stage.GetRootLayer().subLayerPaths.insert(0, str(derived))
    display = Sdf.Layer.CreateNew(str(out / "presentation.usda"))
    display.documentation = "Schematic cylinder strokes of radius 0.045 m, not physical pipe bodies or diameters."
    stage.GetRootLayer().subLayerPaths.insert(0, display.realPath)
    presentation(stage, display)
    # USD 26.8 sites expose GetPrim/GetProperty, not the harness's GetPath.
    # Execute the same UsdValidation registry selection and serialize all findings.
    findings = []
    for error in run(stage, KEYWORDS):
        paths = []
        for site in error.GetSites():
            target = site.GetProperty() if site.IsProperty() else site.GetPrim()
            paths.append(str(target.GetPath()))
        findings.append({"name": error.GetName(), "message": error.GetMessage(),
                         "severity": str(error.GetType()).split(".")[-1].lower(), "paths": paths})
    return findings
