#!/pxrpythonsubst
import math
import unittest
import bootstrap
from pxr import Plug, Usd, UsdValidation
from usdaeco_check.validation import run

Plug.Registry().RegisterPlugins(str(bootstrap.ROOT / "usdAecoAxisValidators"))


def fixture():
    stage = Usd.Stage.CreateInMemory()
    prim = stage.DefinePrim("/Element", "Xform")
    prim.ApplyAPI("AecoAxisAPI")
    return stage, prim


def errors(stage):
    return run(stage, ["UsdAecoAxisValidators"])


class TestValidators(unittest.TestCase):
    def test_AxisDegenerate(self):
        stage, prim = fixture()
        prim.GetAttribute("aeco:axis:end").Set((0, 0, 0))
        found = errors(stage)
        self.assertEqual([e.GetName() for e in found], ["AxisDegenerate"])
        self.assertEqual(found[0].GetType(), UsdValidation.ValidationErrorType.Error)
        prim.GetAttribute("aeco:axis:end").Set((2, 0, 0))
        self.assertEqual(errors(stage), [])
        prim.GetAttribute("aeco:axis:end").Set((float("nan"), 0, 0))
        self.assertEqual([e.GetName() for e in errors(stage)], ["AxisDegenerate"])

    def test_AxisLengthMismatch(self):
        stage, prim = fixture()
        prim.GetAttribute("aeco:axis:length").Set(5)
        found = errors(stage)
        self.assertEqual([e.GetName() for e in found], ["AxisLengthMismatch"])
        self.assertEqual(found[0].GetType(), UsdValidation.ValidationErrorType.Warn)
        prim.GetAttribute("aeco:axis:length").Set(1)
        self.assertEqual(errors(stage), [])
        prim.GetAttribute("aeco:axis:start").Set((1, 0, 0))
        prim.GetAttribute("aeco:axis:end").Set((-1, 0, 0))
        prim.GetAttribute("aeco:axis:arcPoint").Set((0, 1, 0))
        prim.GetAttribute("aeco:axis:curve").Set("arc")
        prim.GetAttribute("aeco:axis:length").Set(math.pi)
        self.assertEqual(errors(stage), [])
        prim.GetAttribute("aeco:axis:length").Set(2)
        self.assertEqual([e.GetName() for e in errors(stage)], ["AxisLengthMismatch"])

    def test_AxisArcPointMissing(self):
        stage, prim = fixture()
        prim.GetAttribute("aeco:axis:curve").Set("arc")
        for point in ((0, 0, 0), (1, 0, 0), (0.5, 0, 0)):
            prim.GetAttribute("aeco:axis:arcPoint").Set(point)
            found = errors(stage)
            self.assertEqual([e.GetName() for e in found], ["AxisArcPointMissing"])
            self.assertEqual(found[0].GetType(), UsdValidation.ValidationErrorType.Warn)
        prim.GetAttribute("aeco:axis:arcPoint").Set((0.5, 0.5, 0))
        self.assertEqual(errors(stage), [])

    def test_plugin_listing(self):
        registry = UsdValidation.ValidationRegistry()
        metadata = registry.GetValidatorMetadataForKeyword("UsdAecoAxisValidators")
        self.assertEqual(len(metadata), 3)
        self.assertTrue(all(registry.GetOrLoadValidatorByName(m.name) for m in metadata))


if __name__ == "__main__":
    unittest.main()
