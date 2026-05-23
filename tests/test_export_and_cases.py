"""Tests for result export bundles and reusable parameter case files."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from stefan_app.export import export_result_bundle
from stefan_app.models import (
    BoundaryCondition,
    StefanParameters,
    load_parameters_json,
    parameters_to_dict,
    save_parameters_json,
)
from stefan_app.solver import BaselineStefanSolver


class ExportAndCaseTests(unittest.TestCase):
    def test_parameter_case_json_round_trips_flat_schema(self) -> None:
        parameters = StefanParameters(
            domain_length=0.05,
            node_count=21,
            left_boundary=BoundaryCondition("left", 294.0),
            right_boundary=BoundaryCondition("right", 270.0),
            duration=0.2,
            output_stride=2,
        )

        with TemporaryDirectory() as directory:
            target = Path(directory) / "case.json"
            save_parameters_json(parameters, target)
            loaded = load_parameters_json(target)

        self.assertEqual(loaded.node_count, parameters.node_count)
        self.assertAlmostEqual(loaded.domain_length, parameters.domain_length)
        self.assertAlmostEqual(loaded.left_boundary.temperature, 294.0)
        self.assertEqual(parameters_to_dict(loaded)["left_boundary_temperature"], 294.0)

    def test_result_bundle_exports_parameters_summary_interface_and_temperature_history(self) -> None:
        parameters = StefanParameters(domain_length=0.05, node_count=11, duration=0.03, time_step=0.01)
        result = BaselineStefanSolver().run(parameters)

        with TemporaryDirectory() as directory:
            exported = export_result_bundle(result, parameters, Path(directory) / "result")
            parameter_payload = json.loads(exported.parameters.read_text(encoding="utf-8"))
            with exported.summary.open(newline="", encoding="utf-8") as file:
                summary_rows = list(csv.reader(file))
            with exported.interface_history.open(newline="", encoding="utf-8") as file:
                interface_rows = list(csv.reader(file))
            with exported.temperature_history.open(newline="", encoding="utf-8") as file:
                temperature_rows = list(csv.reader(file))

        self.assertEqual(exported.directory.name, "result")
        self.assertEqual(parameter_payload["node_count"], parameters.node_count)
        self.assertIn(["metric", "value"], summary_rows)
        self.assertIn("final_time", {row[0] for row in summary_rows[1:]})
        self.assertEqual(interface_rows[0], ["time", "interface_position"])
        self.assertEqual(len(interface_rows), len(result.times) + 1)
        self.assertEqual(temperature_rows[0][0], "time")
        self.assertEqual(len(temperature_rows[0]), parameters.node_count + 1)
        self.assertEqual(len(temperature_rows), len(result.times) + 1)


if __name__ == "__main__":
    unittest.main()
