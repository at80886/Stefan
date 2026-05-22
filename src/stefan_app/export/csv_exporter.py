"""CSV export support for simulation result summaries."""

from __future__ import annotations

import csv
from pathlib import Path

from stefan_app.models import SimulationResult


def export_result_csv(result: SimulationResult, target: Path) -> Path:
    """Write time and interface position history to a CSV file."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["time", "interface_position"])
        writer.writerows(zip(result.times, result.positions))
    return target
