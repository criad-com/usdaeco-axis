#!/pxrpythonsubst
import math
from pathlib import Path
import tempfile
import unittest
import numpy as np
import bootstrap
from pxr import Gf, Sdf, Usd, UsdGeom
from usdaeco_axis.derive import derive
from usdaeco_axis.validators import check_plan, path_elements
from usdaeco_axis.geometry import arc_geometry
from testUsdAecoAxisValidators import errors, fixture


class TestDerive(unittest.TestCase):
    def setUp(self):
        self.source = bootstrap.ROOT / "usdAecoAxis/examples/minimal.usda"
        self.stage = Usd.Stage.Open(str(self.source))
        self.output = Sdf.Layer.CreateAnonymous("derived.usda")

    def composed(self):
        root = Sdf.Layer.CreateAnonymous()
        root.subLayerPaths = [self.output.identifier, str(self.source)]
        return Usd.Stage.Open(root)

    def test_three_curves(self):
        before = self.source.read_bytes()
        edit_target = self.stage.GetEditTarget().GetLayer()
        stats = derive(self.stage, self.output)
        self.assertEqual(stats, {"axes": 3, "lengths": [3.0, 2.0, 2.0]})
        stage = self.composed()
        curves = [UsdGeom.BasisCurves(p) for p in stage.Traverse() if p.IsA(UsdGeom.BasisCurves)]
        self.assertEqual(len(curves), 3)
        for curve in curves:
            points = curve.GetPointsAttr().Get()
            length = sum((b-a).GetLength() for a,b in zip(points, points[1:]))
            self.assertAlmostEqual(length, curve.GetPrim().GetParent().GetAttribute("aeco:axis:length").Get(), delta=1e-9)
            self.assertEqual(curve.ComputePurpose(), "guide")
            self.assertEqual(curve.GetPrim().GetAttribute("aeco:derived:role").Get(), "axis")
            self.assertEqual(curve.GetPrim().GetAttribute("aeco:derived:approx").Get(), "exact")
        self.assertEqual(errors(stage), [])
        self.assertEqual(check_plan(stage), [])
        self.assertEqual(len(list(path_elements(stage))), 3)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(self.stage.GetEditTarget().GetLayer(), edit_target)
        for prim in self.stage.Traverse():
            self.assertFalse(prim.GetAttribute("aeco:axis:length").HasAuthoredValueOpinion())

    def test_output_has_no_drivers(self):
        derive(self.stage, self.output)
        text = self.output.ExportToString()
        for name in ("start", "end", "curve", "arcPoint"):
            self.assertNotIn("aeco:axis:" + name, text)
        self.assertNotIn("aecoDerived", text)

    def test_exact_tolerance(self):
        for meters in (1.0, 0.001):
            with self.subTest(meters_per_unit=meters):
                stage, prim = fixture()
                UsdGeom.SetStageMetersPerUnit(stage, meters)
                derive(stage, self.output)
                output = Usd.Stage.Open(self.output)
                curve = output.GetPrimAtPath("/Element/Axis")
                tolerance = curve.GetAttribute("aeco:derived:tolerance")
                self.assertTrue(tolerance.HasAuthoredValueOpinion())
                self.assertEqual(tolerance.Get(), 1e-9)
                self.assertEqual(curve.GetAttribute("aeco:derived:approx").Get(), "exact")
                # Point3f encoding must not understate endpoint error.
                prim.GetAttribute("aeco:axis:end").Set((1.23456789, 0, 0))
                derive(stage, self.output)
                error = abs(curve.GetAttribute("points").Get()[-1][0] * meters - 1.23456789)
                self.assertGreater(error, 1e-9)
                self.assertAlmostEqual(tolerance.Get(), error, delta=1e-15)

    def test_arc_segmented_tolerance(self):
        for radius, segments, meters in ((1.0, 2, 1.0), (1.0, 32, 1.0), (2.0, 8, 0.001)):
            with self.subTest(radius=radius, segments=segments, meters_per_unit=meters):
                stage, prim = fixture()
                UsdGeom.SetStageMetersPerUnit(stage, meters)
                for name, value in {"start": (radius, 0, 0), "arcPoint": (0, radius, 0),
                                    "end": (-radius, 0, 0), "curve": "arc"}.items():
                    prim.GetAttribute("aeco:axis:" + name).Set(value)
                derive(stage, self.output, segments=segments)
                output = Usd.Stage.Open(self.output)
                curve = output.GetPrimAtPath("/Element/Axis")
                encoded = np.array(curve.GetAttribute("points").Get(), dtype=float) * meters
                angles = np.linspace(0, math.pi, segments + 1)
                analytic = radius * np.column_stack((np.cos(angles), np.sin(angles), np.zeros_like(angles)))
                rounding = float(np.max(np.linalg.norm(encoded - analytic, axis=1)))
                chord_deviation = radius * (1 - math.cos(math.pi / (2 * segments)))
                tolerance = curve.GetAttribute("aeco:derived:tolerance")
                self.assertTrue(tolerance.HasAuthoredValueOpinion())
                self.assertGreater(tolerance.Get(), 0)
                self.assertTrue(math.isfinite(tolerance.Get()))
                self.assertAlmostEqual(tolerance.Get(), chord_deviation + rounding, delta=1e-12)
                self.assertEqual(curve.GetAttribute("aeco:derived:approx").Get(), "arcSegmented")
                self.assertEqual(len(encoded), segments + 1)
                midpoints = (encoded[:-1] + encoded[1:]) / 2
                measured = np.max(np.abs(radius - np.linalg.norm(midpoints, axis=1)))
                self.assertLessEqual(measured, tolerance.Get() + 1e-12)

    def test_idempotent(self):
        derive(self.stage, self.output)
        first = self.output.ExportToString()
        derive(self.stage, self.output)
        self.assertEqual(self.output.ExportToString(), first)

    def test_transaction_and_source_refusals(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "axis.derived.usda"
            derive(self.stage, target)
            before = target.read_bytes()
            root = Sdf.Layer.CreateAnonymous();root.TransferContent(self.stage.GetRootLayer())
            stage = Usd.Stage.Open(root)
            stage.GetPrimAtPath("/Run/Pipe3").GetAttribute("aeco:axis:end").Set((0,0,0))
            with self.assertRaises(ValueError): derive(stage, target)
            self.assertEqual(target.read_bytes(), before)
            with self.assertRaises(ValueError): derive(self.stage, self.source)
            with self.assertRaises(ValueError): derive(self.stage, self.stage.GetRootLayer())
            foreign = Sdf.Layer.CreateNew(str(Path(tmp)/"foreign.usda"));foreign.customLayerData={"owner":"another-tool"};foreign.Save()
            with self.assertRaises(ValueError): derive(self.stage, foreign.realPath)

    def test_arc_geometry(self):
        points, length, error = arc_geometry((1,0,0),(0,1,0),(-1,0,0))
        self.assertEqual(len(points),33)
        self.assertAlmostEqual(length,math.pi,delta=1e-12)
        self.assertGreater(error,0)
        self.assertGreater(points[16][1],0.999)
        stage,prim=fixture()
        for name,value in {"start":(1,0,0),"end":(-1,0,0),"arcPoint":(0,1,0),"curve":"arc"}.items():prim.GetAttribute("aeco:axis:"+name).Set(value)
        derive(stage,self.output)
        output=Usd.Stage.Open(self.output)
        self.assertEqual(output.GetPrimAtPath("/Element/Axis").GetAttribute("aeco:derived:approx").Get(),"arcSegmented")
        self.assertAlmostEqual(output.GetPrimAtPath("/Element").GetAttribute("aeco:axis:length").Get(),math.pi,delta=1e-12)

    def test_non_metre_stage(self):
        stage,prim=fixture();UsdGeom.SetStageMetersPerUnit(stage,0.001)
        derive(stage,self.output)
        output=Usd.Stage.Open(self.output)
        points=output.GetPrimAtPath("/Element/Axis").GetAttribute("points").Get()
        self.assertEqual(points[-1],Gf.Vec3f(1000,0,0))
        self.assertEqual(output.GetPrimAtPath("/Element").GetAttribute("aeco:axis:length").Get(),1)

    def test_plan_missing_axis(self):
        derive(self.stage,self.output)
        stage=self.composed()
        stage.GetPrimAtPath("/Run/Pipe2").RemoveAPI("AecoAxisAPI")
        self.assertEqual([f["path"] for f in check_plan(stage)],["/Run/Pipe2"])

    def test_nested_element_geometry_ownership(self):
        stage=Usd.Stage.CreateInMemory()
        outer=stage.DefinePrim("/Outer","Xform");outer.ApplyAPI("AecoElementAPI");outer.ApplyAPI("AecoClassificationAPI","ifc");outer.GetAttribute("aeco:class:ifc:code").Set("IfcWall")
        inner=stage.DefinePrim("/Outer/Inner","Xform");inner.ApplyAPI("AecoElementAPI")
        UsdGeom.Cube.Define(stage,"/Outer/Inner/Body")
        self.assertEqual(check_plan(stage),[])
        UsdGeom.Cube.Define(stage,"/Outer/Body")
        self.assertEqual([f["path"] for f in check_plan(stage)],["/Outer"])


if __name__ == "__main__":
    unittest.main()
