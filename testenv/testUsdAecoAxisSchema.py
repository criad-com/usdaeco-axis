#!/pxrpythonsubst
import unittest
import bootstrap
from pxr import Plug, Usd, Tf

Plug.Registry().RegisterPlugins(str(bootstrap.ROOT / "usdAecoAxis"))


class TestSchema(unittest.TestCase):
    def test_registry(self):
        registry = Usd.SchemaRegistry()
        api = registry.FindAppliedAPIPrimDefinition("AecoAxisAPI")
        self.assertEqual(len(api.GetPropertyNames()), 5)
        self.assertFalse(Tf.Type.FindByName("UsdAecoAxisAxisAPI").isUnknown)
        self.assertTrue(Tf.Type.FindByName("UsdAecoAxisAPI").isUnknown)

    def test_applicability(self):
        stage = Usd.Stage.CreateInMemory()
        for name in ("Xform", "Mesh", "Scope"):
            self.assertTrue(stage.DefinePrim("/" + name, name).CanApplyAPI("AecoAxisAPI"))
        for name in ("Material", "AecoSystem"):
            self.assertFalse(stage.DefinePrim("/" + name, name).CanApplyAPI("AecoAxisAPI"))

    def test_driver_derived_metadata(self):
        api = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition("AecoAxisAPI")
        self.assertTrue(api.GetPropertyMetadata("aeco:axis:length", "aecoDerived"))
        for name in ("start", "end", "arcPoint", "curve"):
            self.assertFalse(api.GetPropertyMetadata("aeco:axis:" + name, "aecoDerived"))

    def test_intent_length_is_recognized(self):
        stage = Usd.Stage.CreateInMemory()
        prim = stage.DefinePrim("/E", "Xform"); prim.ApplyAPI("AecoAxisAPI")
        prim.GetAttribute("aeco:axis:length").Set(2.5)
        prim.GetAttribute("aeco:axis:end").Set((0, 0, 2.5))
        derived = [p.name for p in stage.GetRootLayer().GetPrimAtPath("/E").properties
                   if prim.GetProperty(p.name).GetMetadata("aecoDerived")]
        self.assertEqual(derived, ["aeco:axis:length"])


if __name__ == "__main__":
    unittest.main()
