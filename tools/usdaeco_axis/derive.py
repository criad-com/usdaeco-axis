"""Write guides and derived lengths into a dedicated, replaceable layer."""
from pathlib import Path
import numpy as np
from pxr import Gf, Sdf, Usd, UsdGeom, Vt
from . import iter_axes
from .geometry import evaluate

# Metres: numerical precision of derivation from double-precision endpoints.
# Float32 guide encoding may require a larger declared tolerance.
NUMERIC_TOLERANCE_M = 1e-9

# Last derivation release; public URL changes do not republish derived output.
PRODUCER_VERSION = "0.1.3"


def derive(stage, target, segments=32):
    """Replace an owned derived layer atomically after evaluating every axis.

    Source layers and the caller's edit target are unchanged. The output contains
    only length opinions and plain Axis curves, never start/end/curve drivers.
    The caller chooses where to compose the returned layer.
    """
    if isinstance(target, (str, Path)):
        path = Path(target).resolve()
        if not path.suffix in (".usd", ".usda", ".usdc"):
            raise ValueError("Derived output must be a named USD layer")
        if any(layer.realPath and Path(layer.realPath).resolve() == path for layer in stage.GetLayerStack()):
            raise ValueError("Derived output must be separate from every input layer")
        existing = Sdf.Layer.FindOrOpen(str(path)) if path.exists() else None
        if existing and existing.customLayerData.get("aeco:axis:layer") != "derived":
            raise ValueError("Refusing to replace a layer not owned by aeco-axis")
    else:
        path = None
        existing = target
        if existing in stage.GetLayerStack():
            raise ValueError("Derived output must be separate from every input layer")
        if not existing.empty and existing.customLayerData.get("aeco:axis:layer") != "derived":
            raise ValueError("Refusing to replace a layer not owned by aeco-axis")
    # Resolve before mutation: one invalid axis cannot leave partial output.
    axes = [(p, evaluate(p, segments)) for p in iter_axes(stage)]
    layer = Sdf.Layer.CreateAnonymous("axis.derived.usda")
    stamp = "aeco-axis " + PRODUCER_VERSION
    layer.customLayerData = {"aeco:axis:layer": "derived", "aeco:axis:producer": stamp}
    output = Usd.Stage.Open(layer)
    meters = UsdGeom.GetStageMetersPerUnit(stage)
    for prim, (points, length, deflection, approx) in axes:
        owner = output.OverridePrim(prim.GetPath())
        owner.CreateAttribute("aeco:axis:length", Sdf.ValueTypeNames.Double, custom=False).Set(length)
        curve = UsdGeom.BasisCurves.Define(output, prim.GetPath().AppendChild("Axis"))
        local = points / meters
        encoded = local.astype(np.float32)
        rounding = float(np.max(np.linalg.norm(encoded.astype(float) * meters - points, axis=1)))
        # Exact lines have no chord error. Arcs use the sagitta computed for
        # their actual radius, sweep and segment count, plus encoding error.
        tolerance = max(NUMERIC_TOLERANCE_M, deflection + rounding)
        curve.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(*(float(v) for v in p)) for p in encoded]))
        curve.CreateCurveVertexCountsAttr([len(points)])
        curve.CreateTypeAttr("linear")
        curve.CreateWrapAttr("nonperiodic")
        curve.CreatePurposeAttr("guide")
        width = 0.06 / meters
        curve.CreateWidthsAttr([width])
        curve.SetWidthsInterpolation("constant")
        curve.CreateExtentAttr([Gf.Vec3f(*(np.min(local, axis=0) - width / 2)),
                               Gf.Vec3f(*(np.max(local, axis=0) + width / 2))])
        curve.CreateDisplayColorAttr([(0.12, 0.58, 0.88)])
        marked = curve.GetPrim()
        marked.ApplyAPI("AecoDerivedGeometryAPI")
        for name, value in {"source": prim.GetAttribute("aeco:id").Get() or "", "role": "axis",
                            "approx": approx, "stamp": stamp,
                            "tolerance": tolerance}.items():
            marked.GetAttribute("aeco:derived:" + name).Set(value)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Export to a peer file then replace: the existing output survives failure.
        import os
        import tempfile
        handle, temporary = tempfile.mkstemp(prefix=".axis-", suffix=path.suffix, dir=path.parent)
        os.close(handle)
        try:
            layer.Export(temporary)
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)
        if existing:
            existing.Reload(force=True)
    else:
        existing.TransferContent(layer)
    return {"axes": len(axes), "lengths": [values[1] for _, values in axes]}
