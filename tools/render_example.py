#!/usr/bin/env python3
"""Render a pipe-run illustration from derived Axis guides with Embree."""
from pathlib import Path
import tempfile
import math
import shutil
import sys
import aeco_axis
from usdaeco_axis import register_plugins
from usdaeco_axis.derive import derive
from usdaeco_axis.cli import compose
from usdaeco_render import render
from pxr import Gf, Sdf, Usd, UsdGeom


def display_strokes(stage, layer):
    """Embree accepts mesh rprims; use native Cylinder guide strokes for lines.

    These temporary display gprims trace the derived points. Their radius is a
    drawing convention, not a pipe diameter or a host-generated body.
    """
    with Usd.EditContext(stage, layer):
        axes = [UsdGeom.BasisCurves(p) for p in stage.Traverse() if p.IsA(UsdGeom.BasisCurves)]
        for index, axis in enumerate(axes):
            points = axis.GetPointsAttr().Get()
            if len(points) != 2:
                raise ValueError("This illustration expects the three straight example segments")
            start, end = (Gf.Vec3d(p) for p in points)
            direction = end - start
            stroke = UsdGeom.Cylinder.Define(stage, axis.GetPath().GetParentPath().AppendChild("Proxy"))
            stroke.CreateRadiusAttr(0.035)
            stroke.CreateHeightAttr(direction.GetLength())
            stroke.CreateAxisAttr("Z")
            stroke.CreatePurposeAttr("proxy")
            stroke.CreateDisplayColorAttr([(0.12,0.58,0.88), (0.12,0.75,0.52), (0.9,0.5,0.16)][index:index+1])
            matrix = Gf.Matrix4d().SetRotate(Gf.Rotation(Gf.Vec3d(0,0,1), direction.GetNormalized()))
            matrix.SetTranslateOnly((start+end)/2)
            stroke.MakeMatrixXform().Set(matrix)
            prim = stroke.GetPrim(); prim.ApplyAPI("AecoDerivedGeometryAPI")
            for name,value in {"source":axis.GetPrim().GetAttribute("aeco:derived:source").Get(),
                               "role":"proxy", "approx":"defaultDims", "stamp":"aeco-axis illustration 0.1.0"}.items():
                prim.GetAttribute("aeco:derived:"+name).Set(value)
            prim.GetRelationship("aeco:derived:from").SetTargets([axis.GetPath()])


if __name__ == "__main__":
    register_plugins()
    root = aeco_axis.ROOT
    source = root / "usdAecoAxis/examples/minimal.usda"
    print("== stage: derive and render", flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp).resolve()
        derived = directory / "axis.derived.usda"
        derive(Usd.Stage.Open(str(source)), derived)
        stage_path = directory / "run.usda"
        root_layer = compose(source, derived, stage_path)
        strokes = Sdf.Layer.CreateNew(str(directory / "display.derived.usda"))
        strokes.customLayerData = {"aeco:axis:layer":"display", "aeco:axis:producer":"aeco-axis illustration 0.1.0"}
        root_layer.subLayerPaths.insert(0, "display.derived.usda")
        stage = Usd.Stage.Open(root_layer)
        display_strokes(stage, strokes)
        strokes.Save();root_layer.Save()
        # Frame the actual composed bounds, including the display proxies.
        bounds = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["guide", "proxy", "render"]).ComputeWorldBound(stage.GetPrimAtPath("/Run")).ComputeAlignedRange()
        center = bounds.GetMidpoint()
        radius = bounds.GetSize().GetLength() / 2
        camera_layer = Sdf.Layer.FindOrOpen(str(root / "testenv/render/cameras.usda"))
        camera_stage = Usd.Stage.Open(camera_layer)
        camera = UsdGeom.Camera(camera_stage.GetPrimAtPath("/Renders/usdAecoAxisExample"))
        camera.CreateHorizontalApertureAttr(24)
        camera.CreateVerticalApertureAttr(15)
        camera.CreateFocalLengthAttr(45)
        distance = radius / math.sin(math.atan(15 / (2 * 45))) * 1.15
        eye = center + Gf.Vec3d(1, -1.6, 1.1).GetNormalized() * distance
        camera.MakeMatrixXform().Set(Gf.Matrix4d().SetLookAt(eye, center, Gf.Vec3d(0,0,1)).GetInverse())
        camera_layer.Save()
        # Toolchain 0.2 fixes purposes to guide,render. This tiny invocation
        # adapter adds the explicit proxy purpose requested by this example.
        recorder = shutil.which("usdrecord")
        wrapper = directory / "record-with-proxy"
        wrapper.write_text(f"#!{sys.executable}\nimport os, sys\na=sys.argv[1:]\na[a.index('--purposes')+1]='guide,proxy,render'\nos.execv({recorder!r}, [{recorder!r}, *a])\n")
        wrapper.chmod(0o755)
        print(render(stage_path, cameras=root / "testenv/render/cameras.usda", output=root / "usdAecoAxis/userDoc",
                     manifest=root / "usdAecoAxis/userDoc/render.json", executable=wrapper))
