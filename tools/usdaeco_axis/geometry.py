"""Circular-axis math ported from the sync guide derivation."""
import math
import numpy as np


def arc_geometry(start, middle, end, segments=32):
    if not isinstance(segments, int) or isinstance(segments, bool) or segments < 2:
        raise ValueError("An arc needs at least two segments")
    a, b, c = (np.asarray(p, dtype=float) for p in (start, middle, end))
    if any(p.shape != (3,) or not np.isfinite(p).all() for p in (a, b, c)):
        raise ValueError("Axis points must contain three finite coordinates")
    u = b - a
    normal = np.cross(u, c - a)
    if np.linalg.norm(normal) < 1e-12:
        raise ValueError("Arc points must be distinct and non-collinear")
    normal /= np.linalg.norm(normal)
    x = u / np.linalg.norm(u)
    y = np.cross(normal, x)
    bx, cx, cy = np.linalg.norm(u), np.dot(c - a, x), np.dot(c - a, y)
    center = a + x * (bx / 2) + y * ((cx * cx + cy * cy - bx * cx) / (2 * cy))
    radius = np.linalg.norm(a - center)
    e1 = (a - center) / radius
    e2 = np.cross(normal, e1)
    angle = lambda p: math.atan2(np.dot(p - center, e2), np.dot(p - center, e1)) % (2 * math.pi)
    mid, last = angle(b), angle(c)
    if mid > last:
        last -= 2 * math.pi
    points = np.array([center + radius * (math.cos(t) * e1 + math.sin(t) * e2)
                       for t in np.linspace(0, last, segments + 1)])
    points[0], points[-1] = a, c
    # r * (1 - cos(theta / (2*n))), evaluated without small-angle cancellation.
    deflection = 2 * radius * math.sin(abs(last) / (4 * segments)) ** 2
    return points, float(abs(last) * radius), float(deflection)


def evaluate(prim, segments=32):
    start = np.asarray(prim.GetAttribute("aeco:axis:start").Get(), dtype=float)
    end = np.asarray(prim.GetAttribute("aeco:axis:end").Get(), dtype=float)
    if any(p.shape != (3,) or not np.isfinite(p).all() for p in (start, end)):
        raise ValueError("Axis points must contain three finite coordinates")
    length = float(np.linalg.norm(end - start))
    if length < 1e-9:
        raise ValueError("Cannot derive a degenerate axis")
    curve = prim.GetAttribute("aeco:axis:curve").Get()
    if curve == "arc":
        return (*arc_geometry(start, prim.GetAttribute("aeco:axis:arcPoint").Get(), end, segments), "arcSegmented")
    if curve != "line":
        raise ValueError("Axis curve must be line or arc")
    return np.array([start, end]), length, 0.0, "exact"
