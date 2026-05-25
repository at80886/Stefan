"""Main window for the interactive Stefan simulator."""

from __future__ import annotations

from pathlib import Path
from time import monotonic

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from stefan_app.export import export_result_bundle
from stefan_app.models import (
    BoundaryCondition,
    SimulationResult,
    SimulationState,
    StefanParameters,
    load_parameters_json,
    save_parameters_json,
)
from stefan_app.ui.plot_widgets import SimulationPlotWidget
from stefan_app.ui.worker import SimulationWorker
from stefan_app.utils.exceptions import StefanAppError
from stefan_app.utils.paths import EXAMPLE_CASE_FILE, LAST_SESSION_PARAMETERS_FILE


class MainWindow(QMainWindow):
    """Top-level PyQt6 window that connects parameters, solver, and result display."""

    simulation_completed = pyqtSignal(object)
    simulation_failed = pyqtSignal(str)

    def __init__(self, session_parameters_file: Path | None = None) -> None:
        super().__init__()
        self._session_parameters_file = session_parameters_file or LAST_SESSION_PARAMETERS_FILE
        self._thread: QThread | None = None
        self._worker: SimulationWorker | None = None
        self._last_result: SimulationResult | None = None
        self._last_parameters: StefanParameters | None = None
        self._is_paused = False
        self._suppress_stop_error = False
        self._realtime_x_coordinates: tuple[float, ...] = ()
        self._realtime_times: list[float] = []
        self._realtime_positions: list[float] = []
        self._realtime_temperatures: list[tuple[float, ...]] = []
        self._realtime_states: list[SimulationState] = []
        self._last_plot_refresh_time = 0.0
        self._plot_refresh_interval_seconds = 0.08

        self.setWindowTitle("一维 Stefan 问题模拟器")
        self.resize(1180, 760)
        self._build_widgets()
        self.setStatusBar(QStatusBar(self))
        self._set_idle_state()
        self._load_startup_parameters()

    def closeEvent(self, event) -> None:  # noqa: ANN001 - Qt override signature.
        self._save_last_session_parameters()
        self._stop_worker()
        super().closeEvent(event)

    def _build_widgets(self) -> None:
        container = QWidget(self)
        container.setObjectName("mainContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 10)
        layout.setSpacing(10)
        layout.addWidget(self._build_header())
        layout.addWidget(self._build_workspace(), stretch=1)
        self.setCentralWidget(container)

    def _build_header(self) -> QWidget:
        header = QWidget(self)
        header.setObjectName("appHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)
        title = QLabel("一维 Stefan 问题")
        title.setObjectName("appTitle")
        layout.addWidget(title)
        layout.addStretch(1)

        self.start_button = QPushButton("开始", self)
        self.start_button.setObjectName("startButton")
        self.pause_button = QPushButton("暂停", self)
        self.pause_button.setObjectName("pauseButton")
        self.reset_button = QPushButton("重置", self)
        self.reset_button.setObjectName("resetButton")
        self.load_case_button = QPushButton("加载参数", self)
        self.load_case_button.setObjectName("loadCaseButton")
        self.save_case_button = QPushButton("保存参数", self)
        self.save_case_button.setObjectName("saveCaseButton")
        self.export_button = QPushButton("导出", self)
        self.export_button.setObjectName("exportButton")
        self.export_button.setEnabled(False)

        self.start_button.clicked.connect(self._start_simulation)
        self.pause_button.clicked.connect(self._toggle_pause)
        self.reset_button.clicked.connect(self._reset_simulation)
        self.load_case_button.clicked.connect(self._load_case_file)
        self.save_case_button.clicked.connect(self._save_case_file)
        self.export_button.clicked.connect(self._export_result)

        for button in (
            self.start_button,
            self.pause_button,
            self.reset_button,
            self.load_case_button,
            self.save_case_button,
            self.export_button,
        ):
            layout.addWidget(button)
        return header

    def _build_workspace(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self._build_parameter_panel())
        splitter.addWidget(self._build_plot_panel())
        splitter.addWidget(self._build_status_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)
        return splitter

    def _build_parameter_panel(self) -> QGroupBox:
        panel = QGroupBox("参数设置", self)
        panel.setObjectName("parameterPanel")
        layout = QFormLayout(panel)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(8)

        self.domain_length_input = self._double_input(0.001, 1000.0, 1.0, 6)
        self.node_count_input = self._integer_input(3, 5001, 101)
        self.initial_temperature_input = self._double_input(0.0, 5000.0, 273.15, 3)
        self.melting_temperature_input = self._double_input(0.0, 5000.0, 273.15, 3)
        self.left_boundary_input = self._double_input(0.0, 5000.0, 293.15, 3)
        self.right_boundary_input = self._double_input(0.0, 5000.0, 273.15, 3)
        self.thermal_diffusivity_input = self._double_input(1.0e-9, 1.0, 1.0e-4, 9)
        self.stefan_number_input = self._double_input(1.0e-6, 1000.0, 1.0, 6)
        self.phase_change_interval_input = self._double_input(1.0e-6, 1000.0, 0.5, 6)
        self.time_step_input = self._double_input(1.0e-9, 1000.0, 0.01, 9)
        self.duration_input = self._double_input(0.0, 100000.0, 1.0, 6)
        self.output_stride_input = self._integer_input(1, 1000000, 1)

        for label, widget in (
            ("计算域长度", self.domain_length_input),
            ("节点数量", self.node_count_input),
            ("初始温度", self.initial_temperature_input),
            ("相变温度", self.melting_temperature_input),
            ("左边界温度", self.left_boundary_input),
            ("右边界温度", self.right_boundary_input),
            ("热扩散率", self.thermal_diffusivity_input),
            ("Stefan 数", self.stefan_number_input),
            ("相变区间", self.phase_change_interval_input),
            ("时间步长", self.time_step_input),
            ("仿真时长", self.duration_input),
            ("输出间隔", self.output_stride_input),
        ):
            layout.addRow(label, widget)
        return panel

    def _build_plot_panel(self) -> QGroupBox:
        panel = QGroupBox("结果预览", self)
        panel.setObjectName("plotPanel")
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 12, 10, 10)
        self.plot_widget = SimulationPlotWidget(panel)
        layout.addWidget(self.plot_widget)
        return panel

    def _build_status_panel(self) -> QGroupBox:
        panel = QGroupBox("仿真状态", self)
        panel.setObjectName("statusPanel")
        layout = QFormLayout(panel)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(10)
        self.time_value = QLabel("0.000000 s", self)
        self.interface_value = QLabel("0.000000 m", self)
        self.progress_value = QLabel("0%", self)
        self.state_value = QLabel("空闲", self)
        self.message_value = QLabel("", self)
        self.time_value.setObjectName("timeValue")
        self.interface_value.setObjectName("interfaceValue")
        self.progress_value.setObjectName("progressValue")
        self.state_value.setObjectName("stateValue")
        self.message_value.setObjectName("messageValue")
        self.state_value.setProperty("state", "idle")
        for widget in (self.time_value, self.interface_value, self.progress_value, self.state_value):
            widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_value.setWordWrap(True)
        for label, widget in (
            ("时间", self.time_value),
            ("界面位置", self.interface_value),
            ("进度", self.progress_value),
            ("状态", self.state_value),
            ("提示", self.message_value),
        ):
            layout.addRow(label, widget)
        return panel

    def _double_input(self, minimum: float, maximum: float, value: float, decimals: int) -> QDoubleSpinBox:
        widget = QDoubleSpinBox(self)
        widget.setRange(minimum, maximum)
        widget.setDecimals(decimals)
        widget.setValue(value)
        widget.setKeyboardTracking(False)
        return widget

    def _integer_input(self, minimum: int, maximum: int, value: int) -> QSpinBox:
        widget = QSpinBox(self)
        widget.setRange(minimum, maximum)
        widget.setValue(value)
        widget.setKeyboardTracking(False)
        return widget

    def _collect_parameters(self) -> StefanParameters:
        return StefanParameters(
            domain_length=self.domain_length_input.value(),
            node_count=self.node_count_input.value(),
            initial_temperature=self.initial_temperature_input.value(),
            melting_temperature=self.melting_temperature_input.value(),
            left_boundary=BoundaryCondition("left", self.left_boundary_input.value()),
            right_boundary=BoundaryCondition("right", self.right_boundary_input.value()),
            thermal_diffusivity=self.thermal_diffusivity_input.value(),
            stefan_number=self.stefan_number_input.value(),
            phase_change_interval=self.phase_change_interval_input.value(),
            time_step=self.time_step_input.value(),
            duration=self.duration_input.value(),
            output_stride=self.output_stride_input.value(),
        )

    def _apply_parameters(self, parameters: StefanParameters) -> None:
        self.domain_length_input.setValue(parameters.domain_length)
        self.node_count_input.setValue(parameters.node_count)
        self.initial_temperature_input.setValue(parameters.initial_temperature)
        self.melting_temperature_input.setValue(parameters.melting_temperature)
        self.left_boundary_input.setValue(parameters.left_boundary.temperature)
        self.right_boundary_input.setValue(parameters.right_boundary.temperature)
        self.thermal_diffusivity_input.setValue(parameters.thermal_diffusivity)
        self.stefan_number_input.setValue(parameters.stefan_number)
        self.phase_change_interval_input.setValue(parameters.phase_change_interval)
        self.time_step_input.setValue(parameters.time_step)
        self.duration_input.setValue(parameters.duration)
        self.output_stride_input.setValue(parameters.output_stride)

    def _load_default_case(self) -> None:
        if not EXAMPLE_CASE_FILE.exists():
            return
        try:
            self._apply_parameters(load_parameters_json(EXAMPLE_CASE_FILE))
        except StefanAppError as exc:
            self._update_message(exc.user_message)

    def _load_startup_parameters(self) -> None:
        if self._load_last_session_parameters():
            return
        self._load_default_case()

    def _load_last_session_parameters(self) -> bool:
        if not self._session_parameters_file.exists():
            return False
        try:
            self._apply_parameters(load_parameters_json(self._session_parameters_file))
        except StefanAppError as exc:
            self._update_message(f"{exc.user_message} 已改用默认参数。")
            return False
        return True

    def _save_last_session_parameters(self) -> None:
        try:
            save_parameters_json(self._collect_parameters(), self._session_parameters_file)
        except StefanAppError as exc:
            self._update_message(exc.user_message)

    def _load_case_file(self) -> None:
        target, _ = QFileDialog.getOpenFileName(
            self,
            "加载仿真参数",
            str(Path.cwd()),
            "JSON 文件 (*.json)",
        )
        if not target:
            return
        try:
            self._apply_parameters(load_parameters_json(Path(target)))
        except StefanAppError as exc:
            self._update_message(exc.user_message)
            return
        self._last_result = None
        self._clear_realtime_result()
        self.plot_widget.set_result(None)
        self.export_button.setEnabled(False)
        self._update_message(f"已加载参数文件 {target}")

    def _save_case_file(self) -> None:
        target, _ = QFileDialog.getSaveFileName(
            self,
            "保存仿真参数",
            str(Path.cwd() / "stefan_case.json"),
            "JSON 文件 (*.json)",
        )
        if not target:
            return
        try:
            saved = save_parameters_json(self._collect_parameters(), Path(target))
        except StefanAppError as exc:
            self._update_message(exc.user_message)
            return
        self._update_message(f"参数已保存到 {saved}")

    def _start_simulation(self) -> None:
        if self._thread is not None:
            return
        parameters = self._collect_parameters()
        self._last_result = None
        self._last_parameters = parameters
        self._clear_realtime_result()
        self.plot_widget.set_result(None)
        self._is_paused = False
        self.pause_button.setText("暂停")
        self._set_controls_running(True)
        self._update_message("正在运行仿真...")
        self.statusBar().showMessage("运行中")

        self._thread = QThread(self)
        self._worker = SimulationWorker(parameters)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress_changed.connect(self._update_progress)
        self._worker.result_ready.connect(self._handle_result)
        self._worker.error_occurred.connect(self._handle_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._handle_thread_finished)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _toggle_pause(self) -> None:
        if self._worker is None:
            return
        self._is_paused = not self._is_paused
        if self._is_paused:
            self._worker.pause()
            self.pause_button.setText("继续")
            self._set_state_indicator("已暂停", "paused")
            self.statusBar().showMessage("已暂停")
        else:
            self._worker.resume()
            self.pause_button.setText("暂停")
            self._set_state_indicator("运行中", "running")
            self.statusBar().showMessage("运行中")

    def _reset_simulation(self) -> None:
        if self._worker is not None:
            self._suppress_stop_error = True
            self._worker.stop()
        self._last_result = None
        self._clear_realtime_result()
        self.plot_widget.set_result(None)
        self._set_idle_state()

    def _stop_worker(self) -> None:
        if self._worker is not None:
            self._worker.stop()
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)

    def _update_progress(self, state: SimulationState) -> None:
        self.time_value.setText(f"{state.time:.6f} s")
        self.interface_value.setText(f"{state.interface_position:.6f} m")
        self.progress_value.setText(f"{state.progress * 100:.0f}%")
        if state.status == "running":
            self._set_state_indicator("运行中", "running")
        else:
            self._set_state_indicator("已完成", "completed")
        self.message_value.setText(state.message or "正在运行仿真...")
        self._append_realtime_state(state)
        self._maybe_refresh_realtime_plot(state)

    def _handle_result(self, result: SimulationResult) -> None:
        self._last_result = result
        self.plot_widget.set_result(result)
        summary = result.summarize()
        self.time_value.setText(f"{summary.final_time:.6f} s")
        self.interface_value.setText(f"{summary.final_interface_position:.6f} m")
        self.progress_value.setText("100%")
        self._set_state_indicator("已完成", "completed")
        self._update_message(summary.message or result.message)
        self.start_button.setText("重新运行")
        self.export_button.setEnabled(True)
        self.statusBar().showMessage("已完成")
        self.simulation_completed.emit(result)

    def _clear_realtime_result(self) -> None:
        self._realtime_x_coordinates = ()
        self._realtime_times.clear()
        self._realtime_positions.clear()
        self._realtime_temperatures.clear()
        self._realtime_states.clear()
        self._last_plot_refresh_time = 0.0

    def _append_realtime_state(self, state: SimulationState) -> None:
        if not state.x_coordinates or not state.temperatures:
            return
        if not self._realtime_x_coordinates:
            self._realtime_x_coordinates = state.x_coordinates
        self._realtime_times.append(state.time)
        self._realtime_positions.append(state.interface_position)
        self._realtime_temperatures.append(state.temperatures)
        self._realtime_states.append(state)

    def _maybe_refresh_realtime_plot(self, state: SimulationState) -> None:
        if not self._realtime_times:
            return
        now = monotonic()
        should_refresh = (
            self._last_plot_refresh_time == 0.0
            or state.status == "completed"
            or now - self._last_plot_refresh_time >= self._plot_refresh_interval_seconds
        )
        if not should_refresh:
            return
        self.plot_widget.set_result(self._build_realtime_result(state))
        self._last_plot_refresh_time = now

    def _build_realtime_result(self, state: SimulationState) -> SimulationResult:
        return SimulationResult(
            x_coordinates=self._realtime_x_coordinates,
            times=tuple(self._realtime_times),
            positions=tuple(self._realtime_positions),
            temperatures=tuple(self._realtime_temperatures),
            states=tuple(self._realtime_states),
            status=state.status,
            message=state.message,
        )

    def _handle_error(self, message: str) -> None:
        if self._suppress_stop_error and message == "仿真已停止。":
            self._suppress_stop_error = False
            return
        self._update_message(message)
        self._set_state_indicator("错误", "error")
        self.statusBar().showMessage("错误")
        self.simulation_failed.emit(message)

    def _handle_thread_finished(self) -> None:
        self._thread = None
        self._worker = None
        self._set_controls_running(False)
        if self._last_result is None and self.state_value.text() not in {"错误", "空闲"}:
            self._set_state_indicator("空闲", "idle")
            self.statusBar().showMessage("就绪")

    def _set_idle_state(self) -> None:
        self.time_value.setText("0.000000 s")
        self.interface_value.setText("0.000000 m")
        self.progress_value.setText("0%")
        self._set_state_indicator("空闲", "idle")
        self.message_value.setText("")
        self.start_button.setText("开始")
        self.statusBar().showMessage("就绪")
        self.export_button.setEnabled(False)
        self._set_controls_running(False)

    def _set_controls_running(self, running: bool) -> None:
        self.start_button.setEnabled(not running)
        self.pause_button.setEnabled(running)
        self.reset_button.setEnabled(True)
        self.load_case_button.setEnabled(not running)
        self.save_case_button.setEnabled(not running)
        for widget in (
            self.domain_length_input,
            self.node_count_input,
            self.initial_temperature_input,
            self.melting_temperature_input,
            self.left_boundary_input,
            self.right_boundary_input,
            self.thermal_diffusivity_input,
            self.stefan_number_input,
            self.phase_change_interval_input,
            self.time_step_input,
            self.duration_input,
            self.output_stride_input,
        ):
            widget.setEnabled(not running)

    def _update_message(self, message: str) -> None:
        self.message_value.setText(message)

    def _set_state_indicator(self, text: str, state: str) -> None:
        self.state_value.setText(text)
        self.state_value.setProperty("state", state)
        style = self.state_value.style()
        style.unpolish(self.state_value)
        style.polish(self.state_value)
        self.state_value.update()

    def _export_result(self) -> None:
        if self._last_result is None:
            return
        target = QFileDialog.getExistingDirectory(
            self,
            "导出仿真结果",
            str(Path.cwd()),
        )
        if not target:
            return
        try:
            exported = export_result_bundle(
                self._last_result,
                self._last_parameters or self._collect_parameters(),
                Path(target),
            )
        except StefanAppError as exc:
            self._update_message(exc.user_message)
            return
        self._update_message(f"结果已导出到 {exported.directory}")
