"""Derive Axis guides or validate a classified path traversal."""
import argparse
import json
from pathlib import Path
import os
from pxr import Sdf, Usd, UsdValidation
from . import register_plugins
from .derive import derive
from .validators import check_plan, path_elements


def compose(source, derived, destination):
    source, derived, destination = map(lambda p: Path(p).resolve(), (source, derived, destination))
    if destination in (source, derived) or destination.exists():
        raise ValueError("Composed output must be a new path separate from the inputs")
    base = Sdf.Layer.FindOrOpen(str(source))
    destination.parent.mkdir(parents=True, exist_ok=True)
    root = Sdf.Layer.CreateNew(str(destination))
    root.subLayerPaths = [os.path.relpath(p, destination.parent) for p in (derived, source)]
    # Root-layer-only metadata must be copied explicitly.
    for key in ("defaultPrim", "metersPerUnit", "upAxis", "fallbackPrimTypes", "startTimeCode", "endTimeCode", "timeCodesPerSecond", "framesPerSecond"):
        if base.pseudoRoot.HasInfo(key):
            root.pseudoRoot.SetInfo(key, base.pseudoRoot.GetInfo(key))
    root.Save()
    return root


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("derive")
    p.add_argument("stage")
    p.add_argument("--out", required=True)
    p.add_argument("--composed")
    p.add_argument("--segments", type=int, default=32)
    p = sub.add_parser("check")
    p.add_argument("stage")
    args = parser.parse_args(argv)
    register_plugins()
    try:
        stage = Usd.Stage.Open(args.stage)
        if not stage or stage.GetCompositionErrors():
            raise ValueError("Stage does not compose")
        if args.command == "derive":
            if args.composed and (Path(args.composed).exists() or Path(args.composed).resolve() in (Path(args.stage).resolve(), Path(args.out).resolve())):
                raise ValueError("Composed output must be a new path separate from the inputs")
            result = derive(stage, args.out, args.segments)
            if args.composed:
                compose(args.stage, args.out, args.composed)
            print(json.dumps(result, sort_keys=True))
            return 0
        from usdaeco_check.validation import run
        findings = check_plan(stage)
        for error in run(stage, ["UsdAecoAxisValidators"]):
            findings.append({"name": error.GetName(), "severity": "error" if error.GetType() == UsdValidation.ValidationErrorType.Error else "warn",
                             "path": str(error.GetSites()[0].GetPrim().GetPath()), "message": error.GetMessage()})
        print(json.dumps({"path_elements": len(list(path_elements(stage))), "findings": findings}, sort_keys=True))
        return int(any(f["severity"] == "error" for f in findings))
    except (ValueError, OSError) as exc:
        parser.exit(1, f"aeco-axis: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
