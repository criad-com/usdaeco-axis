"""Shared path drivers and derived Axis guide geometry."""
from pathlib import Path
import os
from pxr import Plug

AXIS_API = "AecoAxisAPI"
__version__ = "0.1.4"


def register_plugins(core_plugin=None, axis_plugin=None):
    root = Path(__file__).resolve().parents[2]
    core = core_plugin or os.environ.get("CORE_PLUGIN_DIR") or root.parent / "usdaeco-core/out/plugins/usdAeco/resources"
    for path in (core, axis_plugin or root / "usdAecoAxis", root / "usdAecoAxisValidators"):
        Plug.Registry().RegisterPlugins(str(Path(path).resolve()))


def iter_axes(stage):
    """Yield prims carrying the shared axis API."""
    return (p for p in stage.Traverse() if p.HasAPI(AXIS_API))


def axis_of(prim):
    """Return local start, end and reported length, or None without the API."""
    if not prim.HasAPI(AXIS_API):
        return None
    return (prim.GetAttribute("aeco:axis:start").Get(),
            prim.GetAttribute("aeco:axis:end").Get(),
            float(prim.GetAttribute("aeco:axis:length").Get() or 0))
