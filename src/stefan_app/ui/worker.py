"""Background simulation worker for the PyQt6 UI."""

from __future__ import annotations

from threading import Event

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from stefan_app.models import SimulationResult, SimulationState, StefanParameters
from stefan_app.solver import BaselineStefanSolver
from stefan_app.utils.exceptions import StefanAppError


class SimulationCancelled(Exception):
    """Internal signal used to stop a running simulation worker."""


class SimulationWorker(QObject):
    """Run the solver outside the UI thread and report progress through signals."""

    progress_changed = pyqtSignal(object)
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, parameters: StefanParameters) -> None:
        super().__init__()
        self._parameters = parameters
        self._pause_event = Event()
        self._pause_event.set()
        self._stop_event = Event()

    @pyqtSlot()
    def run(self) -> None:
        """Execute the baseline simulation in the worker thread."""
        try:
            result = BaselineStefanSolver().run(self._parameters, progress_callback=self._report_progress)
        except SimulationCancelled:
            self.error_occurred.emit("仿真已停止。")
        except StefanAppError as exc:
            self.error_occurred.emit(exc.user_message)
        except Exception as exc:  # pragma: no cover - defensive UI boundary.
            self.error_occurred.emit(str(exc))
        else:
            self.result_ready.emit(result)
        finally:
            self.finished.emit()

    def pause(self) -> None:
        """Pause progress between solver output frames."""
        self._pause_event.clear()

    def resume(self) -> None:
        """Resume a paused simulation."""
        self._pause_event.set()

    def stop(self) -> None:
        """Request worker cancellation."""
        self._stop_event.set()
        self._pause_event.set()

    def _report_progress(self, state: SimulationState) -> None:
        while not self._pause_event.wait(0.05):
            if self._stop_event.is_set():
                raise SimulationCancelled()
        if self._stop_event.is_set():
            raise SimulationCancelled()
        self.progress_changed.emit(state)
