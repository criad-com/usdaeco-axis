"""Python UsdValidation plugin for the shared axis contract."""
from pathlib import Path
import os
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(os.environ.get("TOOLCHAIN_DIR", ROOT.parent / "usdaeco-toolchain")) / "tools"))
from usdaeco_check.validation import register_prim_validator, wrap_legacy
from usdaeco_axis.validators import findings
from . import validatorTokens as tokens


def register(name, error_name):
    def task(prim):
        return [finding for finding in findings(prim) if finding["name"] == error_name]
    register_prim_validator(name, wrap_legacy(name, task), ["UsdAecoAxisAxisAPI"])


register(tokens.AXIS_DEGENERATE_CHECKER, tokens.AXIS_DEGENERATE)
register(tokens.AXIS_LENGTH_MISMATCH_CHECKER, tokens.AXIS_LENGTH_MISMATCH)
register(tokens.AXIS_ARC_POINT_MISSING_CHECKER, tokens.AXIS_ARC_POINT_MISSING)
