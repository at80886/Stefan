"""Solver boundary for one-dimensional Stefan simulations."""

from __future__ import annotations

from collections.abc import Callable
from math import ceil
from typing import Protocol

from stefan_app.models import SimulationResult, SimulationState, StefanParameters
from stefan_app.utils.exceptions import StefanAppError

ProgressCallback = Callable[[SimulationState], None]


class StefanSolver(Protocol):
    """Protocol implemented by concrete Stefan problem solvers."""

    def run(self, parameters: StefanParameters, progress_callback: ProgressCallback | None = None) -> SimulationResult:
        """Run a simulation and return result data."""


class BaselineStefanSolver:
    """Pure Python baseline solver for one-dimensional Stefan simulations."""

    def run(self, parameters: StefanParameters, progress_callback: ProgressCallback | None = None) -> SimulationResult:
        """Run an explicit apparent-heat-capacity simulation."""
        self._validate_stability(parameters)
        x_coordinates = self._build_x_coordinates(parameters)
        temperatures = self._initial_temperatures(parameters)
        step_count = int(ceil(parameters.duration / parameters.time_step)) if parameters.duration else 0

        times: list[float] = []
        positions: list[float] = []
        temperature_history: list[tuple[float, ...]] = []
        states: list[SimulationState] = []

        self._record_state(
            parameters,
            temperatures,
            x_coordinates=x_coordinates,
            time=0.0,
            step_index=0,
            step_count=step_count,
            times=times,
            positions=positions,
            temperature_history=temperature_history,
            states=states,
            progress_callback=progress_callback,
        )

        time = 0.0
        for step_index in range(1, step_count + 1):
            delta_time = min(parameters.time_step, parameters.duration - time)
            temperatures = self._advance_one_step(parameters, temperatures, delta_time)
            time = min(parameters.duration, time + delta_time)
            if step_index % parameters.output_stride == 0 or step_index == step_count:
                self._record_state(
                    parameters,
                    temperatures,
                    x_coordinates=x_coordinates,
                    time=time,
                    step_index=step_index,
                    step_count=step_count,
                    times=times,
                    positions=positions,
                    temperature_history=temperature_history,
                    states=states,
                    progress_callback=progress_callback,
                )

        return SimulationResult(
            x_coordinates=x_coordinates,
            times=tuple(times),
            positions=tuple(positions),
            temperatures=tuple(temperature_history),
            states=tuple(states),
            status="completed",
            message="基线仿真已完成。",
        )

    def _validate_stability(self, parameters: StefanParameters) -> None:
        parameters.validate()
        dx = parameters.domain_length / (parameters.node_count - 1)
        maximum_time_step = 0.5 * dx * dx / parameters.thermal_diffusivity
        if parameters.time_step > maximum_time_step:
            raise StefanAppError(
                f"Time step {parameters.time_step} exceeds explicit stability limit {maximum_time_step}.",
                user_message="当前时间步长过大，不满足基线显式求解器的稳定性要求。",
                recoverable=True,
            )

    def _build_x_coordinates(self, parameters: StefanParameters) -> tuple[float, ...]:
        dx = parameters.domain_length / (parameters.node_count - 1)
        return tuple(index * dx for index in range(parameters.node_count))

    def _initial_temperatures(self, parameters: StefanParameters) -> list[float]:
        temperatures = [parameters.initial_temperature for _ in range(parameters.node_count)]
        temperatures[0] = parameters.left_boundary.temperature
        temperatures[-1] = parameters.right_boundary.temperature
        return temperatures

    def _advance_one_step(
        self,
        parameters: StefanParameters,
        temperatures: list[float],
        delta_time: float,
    ) -> list[float]:
        dx = parameters.domain_length / (parameters.node_count - 1)
        scale = delta_time / (dx * dx)
        next_temperatures = temperatures.copy()
        next_temperatures[0] = parameters.left_boundary.temperature
        next_temperatures[-1] = parameters.right_boundary.temperature

        for index in range(1, parameters.node_count - 1):
            effective_alpha = parameters.thermal_diffusivity / self._heat_capacity_factor(parameters, temperatures[index])
            laplacian = temperatures[index - 1] - 2.0 * temperatures[index] + temperatures[index + 1]
            next_temperatures[index] = temperatures[index] + effective_alpha * scale * laplacian

        return next_temperatures

    def _heat_capacity_factor(self, parameters: StefanParameters, temperature: float) -> float:
        half_interval = parameters.phase_change_interval / 2.0
        if abs(temperature - parameters.melting_temperature) > half_interval:
            return 1.0
        active_delta = self._active_temperature_delta(parameters)
        latent_ratio = max(abs(active_delta), parameters.phase_change_interval) / (
            parameters.stefan_number * parameters.phase_change_interval
        )
        return 1.0 + latent_ratio

    def _record_state(
        self,
        parameters: StefanParameters,
        temperatures: list[float],
        *,
        x_coordinates: tuple[float, ...],
        time: float,
        step_index: int,
        step_count: int,
        times: list[float],
        positions: list[float],
        temperature_history: list[tuple[float, ...]],
        states: list[SimulationState],
        progress_callback: ProgressCallback | None,
    ) -> None:
        position = self._interface_position(parameters, temperatures)
        progress = 1.0 if step_count == 0 else min(1.0, step_index / step_count)
        temperature_snapshot = tuple(temperatures)
        times.append(time)
        positions.append(position)
        temperature_history.append(temperature_snapshot)
        state = SimulationState(
            time=time,
            interface_position=position,
            status="completed" if progress >= 1.0 else "running",
            step_index=step_index,
            progress=progress,
            total_duration=parameters.duration,
            message="基线仿真已完成。" if progress >= 1.0 else "正在运行仿真...",
            x_coordinates=x_coordinates,
            temperatures=temperature_snapshot,
        )
        states.append(state)
        if progress_callback is not None:
            progress_callback(state)

    def _active_boundary_side(self, parameters: StefanParameters) -> str:
        left_delta = parameters.left_boundary.temperature - parameters.melting_temperature
        right_delta = parameters.right_boundary.temperature - parameters.melting_temperature
        return "left" if abs(left_delta) >= abs(right_delta) else "right"

    def _active_temperature_delta(self, parameters: StefanParameters) -> float:
        if self._active_boundary_side(parameters) == "left":
            return parameters.left_boundary.temperature - parameters.melting_temperature
        return parameters.right_boundary.temperature - parameters.melting_temperature

    def _interface_position(self, parameters: StefanParameters, temperatures: list[float]) -> float:
        active_delta = self._active_temperature_delta(parameters)
        if abs(active_delta) < 1.0e-12:
            return 0.0
        return (
            self._left_interface_position(parameters, temperatures, active_delta)
            if self._active_boundary_side(parameters) == "left"
            else self._right_interface_position(parameters, temperatures, active_delta)
        )

    def _left_interface_position(
        self,
        parameters: StefanParameters,
        temperatures: list[float],
        active_delta: float,
    ) -> float:
        dx = parameters.domain_length / (parameters.node_count - 1)
        sign = 1.0 if active_delta > 0 else -1.0
        last_active_index = -1
        for index, temperature in enumerate(temperatures):
            if sign * (temperature - parameters.melting_temperature) > 1.0e-9:
                last_active_index = index
            else:
                break

        if last_active_index <= 0:
            return 0.0
        if last_active_index >= parameters.node_count - 1:
            return parameters.domain_length

        active_value = sign * (temperatures[last_active_index] - parameters.melting_temperature)
        inactive_value = sign * (temperatures[last_active_index + 1] - parameters.melting_temperature)
        ratio = self._crossing_ratio(active_value, inactive_value)
        return (last_active_index + ratio) * dx

    def _right_interface_position(
        self,
        parameters: StefanParameters,
        temperatures: list[float],
        active_delta: float,
    ) -> float:
        dx = parameters.domain_length / (parameters.node_count - 1)
        sign = 1.0 if active_delta > 0 else -1.0
        first_active_index = parameters.node_count
        for index in range(parameters.node_count - 1, -1, -1):
            if sign * (temperatures[index] - parameters.melting_temperature) > 1.0e-9:
                first_active_index = index
            else:
                break

        if first_active_index >= parameters.node_count - 1:
            return parameters.domain_length
        if first_active_index <= 0:
            return 0.0

        inactive_value = sign * (temperatures[first_active_index - 1] - parameters.melting_temperature)
        active_value = sign * (temperatures[first_active_index] - parameters.melting_temperature)
        denominator = active_value - inactive_value
        ratio = 0.0 if abs(denominator) < 1.0e-12 else (0.0 - inactive_value) / denominator
        ratio = max(0.0, min(1.0, ratio))
        return (first_active_index - 1 + ratio) * dx

    def _crossing_ratio(self, active_value: float, inactive_value: float) -> float:
        denominator = active_value - inactive_value
        if abs(denominator) < 1.0e-12:
            return 0.0
        return max(0.0, min(1.0, active_value / denominator))
