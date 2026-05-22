"""Framework smoke tests that do not require launching the PyQt UI."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))


class FrameworkImportTests(unittest.TestCase):
    def test_core_package_imports(self) -> None:
        import stefan_app
        from stefan_app.models import BoundaryCondition, SimulationResult, SimulationState, StefanParameters

        self.assertEqual(stefan_app.__version__, "0.1.0")
        self.assertEqual(BoundaryCondition("left", 273.15).location, "left")
        self.assertEqual(StefanParameters().node_count, 101)
        self.assertEqual(SimulationState().status, "idle")
        self.assertEqual(SimulationResult().times, ())

    def test_resource_paths_exist(self) -> None:
        from stefan_app.utils.paths import EXAMPLE_CASE_FILE, RESOURCE_ROOT, STYLE_FILE

        self.assertTrue(RESOURCE_ROOT.exists())
        self.assertTrue(STYLE_FILE.exists())
        self.assertTrue(EXAMPLE_CASE_FILE.exists())


if __name__ == "__main__":
    unittest.main()
