"""Axis rules and the classification-based plan traversal."""
import math
import numpy as np
from pxr import Sdf, Usd, UsdGeom, UsdValidation
from .geometry import evaluate


def findings(prim):
    if not prim.HasAPI("AecoAxisAPI"):
        return []
    start = np.asarray(prim.GetAttribute("aeco:axis:start").Get(), float)
    end = np.asarray(prim.GetAttribute("aeco:axis:end").Get(), float)
    if not np.isfinite(start).all() or not np.isfinite(end).all() or np.linalg.norm(end - start) < 1e-9:
        return [{"name": "AxisDegenerate", "severity": "error", "message": "Axis endpoints must be distinct and finite."}]
    curve = prim.GetAttribute("aeco:axis:curve").Get()
    try:
        _, expected, _, _ = evaluate(prim)
    except ValueError as exc:
        return [{"name": "AxisArcPointMissing" if curve == "arc" else "AxisDegenerate",
                 "severity": "warn" if curve == "arc" else "error", "message": str(exc)}]
    length = prim.GetAttribute("aeco:axis:length").Get() or 0.0
    if not math.isfinite(length) or (length and abs(length - expected) > 1e-3 * max(1.0, expected)):
        return [{"name": "AxisLengthMismatch", "severity": "warn",
                 "message": f"Reported length {length:g} differs from evaluated length {expected:g}."}]
    return []


PATH_CLASSES = {"IfcWall", "IfcWallStandardCase", "IfcPipeSegment", "IfcDuctSegment",
                "IfcCableCarrierSegment", "IfcBeam", "IfcColumn", "IfcMember"}


def path_elements(stage):
    """Every classified path element owning geometry; nested elements own theirs."""
    for prim in stage.Traverse():
        if not prim.HasAPI("AecoElementAPI"):
            continue
        code = prim.GetAttribute("aeco:class:ifc:code")
        if not code or (code.Get() or "").split(".")[0] not in PATH_CLASSES:
            continue
        traversal = Usd.PrimRange(prim)
        iterator = iter(traversal)
        for child in iterator:
            if child != prim and child.HasAPI("AecoElementAPI"):
                iterator.PruneChildren()
                continue
            if child.IsA(UsdGeom.Gprim) or child.GetTypeName() == "BrepArray":
                yield prim
                break


def check_plan(stage):
    return [{"name": "AxisMissing", "severity": "error", "path": str(p.GetPath()),
             "message": "A classified path element with geometry needs AecoAxisAPI."}
            for p in path_elements(stage) if not p.HasAPI("AecoAxisAPI")]
