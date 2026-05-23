"""Offscreen tests for the PyQt6 simulation UI."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from stefan_app.models import BoundaryCondition, StefanParameters
from stefan_app.solver import BaselineStefanSolver
from stefan_app.ui.main_window import MainWindow


class UiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def tearDown(self) -> None:
        self.app.processEvents()

    def test_window_collects_editable_default_parameters(self) -> None:
        window = MainWindow()
        self.addCleanup(window.close)

        parameters = window._collect_parameters()

        self.assertEqual(parameters.node_count, 101)
        self.assertAlmostEqual(parameters.domain_length, 1.0)
        self.assertAlmostEqual(parameters.left_boundary.temperature, 293.15)
        self.assertTrue(window.start_button.isEnabled())
        self.assertFalse(window.pause_button.isEnabled())
        self.assertTrue(window.load_case_button.isEnabled())
        self.assertTrue(window.save_case_button.isEnabled())

    def test_window_applies_loaded_parameters_to_inputs(self) -> None:
        window = MainWindow()
        self.addCleanup(window.close)
        parameters = StefanParameters(
            domain_length=0.25,
            node_count=31,
            left_boundary=BoundaryCondition("left", 310.0),
            right_boundary=BoundaryCondition("right", 260.0),
            time_step=0.001,
            duration=0.5,
        )

        window._apply_parameters(parameters)
        collected = window._collect_parameters()

        self.assertEqual(collected.node_count, 31)
        self.assertAlmostEqual(collected.domain_length, 0.25)
        self.assertAlmostEqual(collected.left_boundary.temperature, 310.0)
        self.assertAlmostEqual(collected.right_boundary.temperature, 260.0)

    def test_completed_result_updates_ui_in_chinese(self) -> None:
        window = MainWindow()
        self.addCleanup(window.close)
        parameters = window._collect_parameters()
        result = BaselineStefanSolver().run(parameters)

        window._handle_result(result)

        self.assertEqual(window.state_value.text(), "已完成")
        self.assertEqual(window.progress_value.text(), "100%")
        self.assertEqual(window.start_button.text(), "重新运行")
        self.assertTrue(window.export_button.isEnabled())
        self.assertIs(window.plot_widget._result, result)
        self.assertEqual(window.plot_widget.tabs.count(), 3)
        self.assertEqual(
            [window.plot_widget.tabs.tabText(index) for index in range(window.plot_widget.tabs.count())],
            ["温度分布", "相界面-时间", "温度云图"],
        )
        self.assertIs(window.plot_widget.temperature_plot._result, result)
        self.assertIs(window.plot_widget.interface_plot._result, result)
        self.assertIs(window.plot_widget.cloud_plot._result, result)

    def test_plot_tabs_render_result_offscreen(self) -> None:
        window = MainWindow()
        self.addCleanup(window.close)
        result = BaselineStefanSolver().run(window._collect_parameters())

        window.plot_widget.set_result(result)
        window.plot_widget.resize(720, 480)
        for canvas in (
            window.plot_widget.temperature_plot,
            window.plot_widget.interface_plot,
            window.plot_widget.cloud_plot,
        ):
            canvas.resize(720, 480)
            image = QImage(720, 480, QImage.Format.Format_ARGB32)
            image.fill(0)
            canvas.render(image)
            self.assertFalse(image.isNull())
            self.assertGreater(self._count_non_background_pixels(image), 50)
            if canvas is window.plot_widget.cloud_plot:
                self.assertGreater(self._count_cloud_color_bar_pixels(image), 100)

    def test_solver_error_is_reported_in_status_panel(self) -> None:
        window = MainWindow()
        self.addCleanup(window.close)
        received: list[str] = []
        window.simulation_failed.connect(received.append)

        window._handle_error("当前时间步长过大，不满足基线显式求解器的稳定性要求。")

        self.assertTrue(received)
        self.assertEqual(window.state_value.text(), "错误")
        self.assertIn("时间步长", window.message_value.text())
        self.assertTrue(window.start_button.isEnabled())

    def _count_non_background_pixels(self, image: QImage) -> int:
        total = 0
        for x in range(0, image.width(), 8):
            for y in range(0, image.height(), 8):
                color = image.pixelColor(x, y)
                if color.red() < 245 or color.green() < 245 or color.blue() < 245:
                    total += 1
        return total

    def _count_cloud_color_bar_pixels(self, image: QImage) -> int:
        total = 0
        for x in range(int(image.width() * 0.84), int(image.width() * 0.92)):
            for y in range(int(image.height() * 0.22), int(image.height() * 0.62)):
                color = image.pixelColor(x, y)
                if color.saturation() > 35 and color.value() < 250:
                    total += 1
        return total


if __name__ == "__main__":
    unittest.main()
