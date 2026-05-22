"""Application assembly for the Stefan simulator."""

from __future__ import annotations

from collections.abc import Sequence

from stefan_app.utils.paths import STYLE_FILE


def load_style_text() -> str:
    """Load the shared Qt stylesheet when it is available."""
    if STYLE_FILE.exists():
        return STYLE_FILE.read_text(encoding="utf-8")
    return ""


def run(argv: Sequence[str] | None = None) -> int:
    """Create the QApplication, show the main window, and start the UI loop."""
    from PyQt6.QtWidgets import QApplication

    from stefan_app.ui.main_window import MainWindow

    application = QApplication(list(argv or []))
    application.setApplicationName("Stefan 1D Simulator")
    application.setStyleSheet(load_style_text())

    window = MainWindow()
    window.show()
    return application.exec()
