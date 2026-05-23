"""Tests for the baseline one-dimensional Stefan simulation core."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from stefan_app.models import BoundaryCondition, StefanParameters
from stefan_app.solver import BaselineStefanSolver
from stefan_app.utils.exceptions import StefanAppError


class SimulationCoreTests(unittest.TestCase):
    def test_baseline_solver_generates_temperature_and_interface_history(self) -> None:
        parameters = StefanParameters(
            domain_length=0.05,
            node_count=21,
            initial_temperature=273.15,
            melting_temperature=273.15,
            left_boundary=BoundaryCondition("left", 293.15),
            right_boundary=BoundaryCondition("right", 273.15),
            thermal_diffusivity=1.0e-4,
            stefan_number=1.0,
            phase_change_interval=0.5,
            time_step=0.01,
            duration=0.2,
            output_stride=2,
        )

        result = BaselineStefanSolver().run(parameters)

        self.assertEqual(result.status, "completed")
        self.assertEqual(len(result.x_coordinates), parameters.node_count)
        self.assertEqual(result.times[0], 0.0)
        self.assertAlmostEqual(result.times[-1], parameters.duration)
        self.assertEqual(len(result.times), len(result.positions))
        self.assertEqual(len(result.times), len(result.temperatures))
        self.assertEqual(len(result.times), len(result.states))
        self.assertEqual(len(result.temperatures[-1]), parameters.node_count)
        self.assertEqual(result.states[0].x_coordinates, result.x_coordinates)
        self.assertEqual(result.states[-1].temperatures, result.temperatures[-1])
        self.assertAlmostEqual(result.states[-1].total_duration, parameters.duration)
        self.assertGreaterEqual(result.positions[-1], result.positions[0])
        self.assertLessEqual(result.positions[-1], parameters.domain_length)

    def test_result_summary_reports_final_state_and_temperature_range(self) -> None:
        parameters = StefanParameters(domain_length=0.05, node_count=21, duration=0.05)

        result = BaselineStefanSolver().run(parameters)
        summary = result.summarize()

        self.assertAlmostEqual(summary.final_time, result.final_time)
        self.assertAlmostEqual(summary.final_interface_position, result.final_interface_position)
        self.assertEqual(summary.stored_steps, len(result.times))
        self.assertLessEqual(summary.minimum_temperature, summary.maximum_temperature)

    def test_right_boundary_can_drive_interface_from_the_right(self) -> None:
        parameters = StefanParameters(
            domain_length=0.05,
            node_count=21,
            left_boundary=BoundaryCondition("left", 273.15),
            right_boundary=BoundaryCondition("right", 293.15),
            duration=0.05,
        )

        result = BaselineStefanSolver().run(parameters)

        self.assertAlmostEqual(result.positions[0], parameters.domain_length)
        self.assertLess(result.positions[-1], result.positions[0])
        self.assertGreaterEqual(result.positions[-1], 0.0)

    def test_invalid_parameters_raise_recoverable_app_error(self) -> None:
        parameters = StefanParameters(node_count=2)

        with self.assertRaises(StefanAppError) as context:
            BaselineStefanSolver().run(parameters)

        self.assertTrue(context.exception.recoverable)

    def test_unstable_time_step_raises_recoverable_app_error(self) -> None:
        parameters = StefanParameters(domain_length=0.05, node_count=21, time_step=1.0)

        with self.assertRaises(StefanAppError) as context:
            BaselineStefanSolver().run(parameters)

        self.assertIn("时间步长", context.exception.user_message)
        self.assertTrue(context.exception.recoverable)


if __name__ == "__main__":
    unittest.main()
