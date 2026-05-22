"""Main window shell for the Stefan simulator."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    """Top-level UI shell with placeholders for the simulation workflow."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Stefan 1D Simulator")
        self.resize(1100, 720)
        self.setCentralWidget(self._build_central_widget())
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Ready")

    def _build_central_widget(self) -> QWidget:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.addWidget(self._build_header())
        layout.addWidget(self._build_workspace(), stretch=1)
        return container

    def _build_header(self) -> QWidget:
        header = QWidget(self)
        layout = QHBoxLayout(header)
        title = QLabel("One-Dimensional Stefan Problem")
        title.setObjectName("appTitle")
        layout.addWidget(title)
        layout.addStretch(1)
        for label in ("Start", "Pause", "Reset", "Export"):
            layout.addWidget(QPushButton(label))
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
        panel = QGroupBox("Parameters", self)
        layout = QFormLayout(panel)
        for name, value in (
            ("Domain length", "1.0 m"),
            ("Initial temperature", "273.15 K"),
            ("Boundary temperature", "293.15 K"),
            ("Time step", "0.01 s"),
        ):
            layout.addRow(QLabel(name), QLabel(value))
        return panel

    def _build_plot_panel(self) -> QFrame:
        panel = QFrame(self)
        panel.setObjectName("plotPanel")
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(panel)
        label = QLabel("Temperature and interface plots will appear here.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        return panel

    def _build_status_panel(self) -> QGroupBox:
        panel = QGroupBox("Simulation Status", self)
        layout = QFormLayout(panel)
        for name, value in (
            ("Time", "0.00 s"),
            ("Interface", "0.000 m"),
            ("State", "Idle"),
        ):
            layout.addRow(QLabel(name), QLabel(value))
        return panel
