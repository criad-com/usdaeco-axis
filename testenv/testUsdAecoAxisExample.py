#!/pxrpythonsubst
"""Verify the published paths and separation of drivers from representations."""
import math
import os
from pathlib import Path
import sys
import unittest
import bootstrap
from pxr import Sdf, Usd, UsdGeom
from usdaeco_axis.example import KEYWORDS, load_axis_validators
from usdaeco_check.validation import run
from check import load_core_validators

# Register the core Python descriptor during collection, before the shared
# ValidationRegistry caches plugin metadata on the first validator test.
sys.path.insert(0, str(Path(os.environ.get("CORE_DIR", bootstrap.ROOT.parent / "usdaeco-core"))))
CORE_NAMES = load_core_validators()


class TestExample(unittest.TestCase):
    def test_published_line_and_arc_contract(self):
        self.assertEqual(len(CORE_NAMES), 8)
        self.assertEqual(len(load_axis_validators()), 3)
        stage = Usd.Stage.Open(str(bootstrap.ROOT / "examples/minimal/result/example.usdc"))
        self.assertEqual(run(stage, KEYWORDS), [])
        axes = [UsdGeom.BasisCurves(p) for p in stage.Traverse() if p.IsA(UsdGeom.BasisCurves)]
        self.assertEqual(len(axes), 4)
        expected = {"Inlet": 3, "Bend": math.pi / 2, "Outlet": 2, "Riser": 2}
        for axis in axes:
            prim = axis.GetPrim()
            owner = prim.GetParent()
            self.assertEqual(axis.ComputePurpose(), "guide")
            self.assertAlmostEqual(owner.GetAttribute("aeco:axis:length").Get(), expected[owner.GetName()], places=12)
            tolerance = prim.GetAttribute("aeco:derived:tolerance").Get()
            if owner.GetName() == "Bend":
                self.assertEqual(prim.GetAttribute("aeco:derived:approx").Get(), "arcSegmented")
                self.assertEqual(list(axis.GetCurveVertexCountsAttr().Get()), [33])
                self.assertGreaterEqual(tolerance, 1 - math.cos(math.pi / 128))
                self.assertLess(tolerance, .000302)
            else:
                self.assertEqual(prim.GetAttribute("aeco:derived:approx").Get(), "exact")
                self.assertEqual(tolerance, 1e-9)

    def test_archived_driver_layer_has_no_derived_geometry(self):
        path = bootstrap.ROOT / "examples/minimal/result/layers/out/drivers.usda"
        root = Sdf.Layer.CreateAnonymous()
        root.subLayerPaths = [str(path), str(path.with_name("base.usda"))]
        stage = Usd.Stage.Open(root)
        elements = [p for p in stage.Traverse() if p.HasAPI("AecoAxisAPI")]
        self.assertEqual(len(elements), 4)
        self.assertFalse(any(p.IsA(UsdGeom.Gprim) for p in stage.Traverse()))
        for prim in elements:
            self.assertFalse(prim.GetAttribute("aeco:axis:length").HasAuthoredValueOpinion())
        self.assertFalse(Sdf.Layer.FindOrOpen(str(path)).subLayerPaths)


if __name__ == "__main__":
    unittest.main()
