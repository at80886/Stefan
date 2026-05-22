"""Framework-level plot data containers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TemperatureSeries:
    """Temperature curve data for a single simulation time."""

    x: tuple[float, ...]
    temperature: tuple[float, ...]


@dataclass(frozen=True)
class InterfaceSeries:
    """Interface position history data."""

    time: tuple[float, ...]
    position: tuple[float, ...]
