#!/pxrpythonsubst
"""A missing core Python plugin must never produce a vacuous passing gate."""
import os
import subprocess
import sys
import unittest
import bootstrap


class TestGate(unittest.TestCase):
    def test_missing_core_validators_fails_loudly(self):
        env = {k: v for k, v in os.environ.items()
               if k not in ("PYTHONPATH", "PXR_PLUGINPATH_NAME")}
        code = """
import importlib.abc
import sys
class MissingCore(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == 'usdAecoValidators':
            raise ModuleNotFoundError('usdAecoValidators is unavailable')
sys.meta_path.insert(0, MissingCore())
from check import load_core_validators
load_core_validators()
"""
        result = subprocess.run([sys.executable, "-c", code], cwd=bootstrap.ROOT,
                                env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usdAecoValidators", result.stderr)


if __name__ == "__main__":
    unittest.main()
