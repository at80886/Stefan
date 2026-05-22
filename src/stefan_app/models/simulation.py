"""Core simulation data structures."""

from __future__ import annotations

from dataclasses import dataclass, field

from stefan_app.utils.exceptions import StefanAppError


@dataclass(frozen=True)
class BoundaryCondition:
    """Boundary temperature definition for one side of the domain."""

    location: str
    temperature: float

    def validate(self) -> None:
        """Ensure the boundary belongs to one side of the one-dimensional domain."""
        if self.location not in {"left", "right"}:
            raise StefanAppError(
                f"Unsupported boundary location: {self.location}",
                user_message="Boundary location must be left or right.",
            )


@dataclass(frozen=True)
class StefanParameters:
    """Physical and numerical parameters for a one-dimensional Stefan case."""

    domain_length: float = 1.0
    node_count: int = 101
    initial_temperature: float = 273.15
    melting_temperature: float = 273.15
    left_boundary: BoundaryCondition = field(default_factory=lambda: BoundaryCondition("left", 293.15))
    right_boundary: BoundaryCondition = field(default_factory=lambda: BoundaryCondition("right", 273.15))
    thermal_diffusivity: float = 1.0e-4
    stefan_number: float = 1.0
    phase_change_interval: float = 0.5
    time_step: float = 0.01
    duration: float = 1.0
    output_stride: int = 1

    def validate(self) -> None:
        """Ensure simulation parameters are physically and numerically meaningful."""
        self.left_boundary.validate()
        self.right_boundary.validate()
        if self.domain_length <= 0:
            raise StefanAppError("Domain length must be positive.")
        if self.node_count < 3:
            raise StefanAppError("Node count must be at least 3.")
        if self.thermal_diffusivity <= 0:
            raise StefanAppError("Thermal diffusivity must be positive.")
        if self.stefan_number <= 0:
            raise StefanAppError("Stefan number must be positive.")
        if self.phase_change_interval <= 0:
            raise StefanAppError("Phase change interval must be positive.")
        if self.time_step <= 0:
            raise StefanAppError("Time step must be positive.")
        if self.duration < 0:
            raise StefanAppError("Duration cannot be negative.")
        if self.output_stride < 1:
            raise StefanAppError("Output stride must be at least 1.")


@dataclass
class SimulationState:
    """Mutable state reported while a simulation task is running."""

    time: float = 0.0
    interface_position: float = 0.0
    status: str = "idle"
    step_index: int = 0
    progress: float = 0.0
    message: str = ""


@dataclass(frozen=True)
class SimulationSummary:
    """Compact result summary for UI status panels and logs."""

    final_time: float
    final_interface_position: float
    minimum_temperature: float
    maximum_temperature: float
    stored_steps: int
    status: str = "completed"
    message: str = ""


@dataclass(frozen=True)
class SimulationResult:
    """Tabular simulation output shared by plotting and export modules."""

    x_coordinates: tuple[float, ...] = ()
    times: tuple[float, ...] = ()
    positions: tuple[float, ...] = ()
    temperatures: tuple[tuple[float, ...], ...] = ()
    states: tuple[SimulationState, ...] = ()
    status: str = "completed"
    message: str = ""

    @property
    def final_time(self) -> float:
        """Return the last recorded simulation time."""
        return self.times[-1] if self.times else 0.0

    @property
    def final_interface_position(self) -> float:
        """Return the last recorded interface position."""
        return self.positions[-1] if self.positions else 0.0

    def summarize(self) -> SimulationSummary:
        """Build a compact summary from the stored result history."""
        flat_temperatures = [value for row in self.temperatures for value in row]
        minimum = min(flat_temperatures) if flat_temperatures else 0.0
        maximum = max(flat_temperatures) if flat_temperatures else 0.0
        return SimulationSummary(
            final_time=self.final_time,
            final_interface_position=self.final_interface_position,
            minimum_temperature=minimum,
            maximum_temperature=maximum,
            stored_steps=len(self.times),
            status=self.status,
            message=self.message,
        )
