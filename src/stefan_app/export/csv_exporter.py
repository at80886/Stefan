"""CSV export support for simulation result bundles."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from stefan_app.models import SimulationResult, StefanParameters
from stefan_app.models.case_io import save_parameters_json
from stefan_app.utils.exceptions import StefanAppError


@dataclass(frozen=True)
class ExportedResultFiles:
    """Paths written by a complete simulation result export."""

    directory: Path
    parameters: Path
    summary: Path
    interface_history: Path
    temperature_history: Path


def export_result_csv(result: SimulationResult, target: Path) -> Path:
    """Write time and interface position history to a CSV file."""
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["time", "interface_position"])
            writer.writerows(zip(result.times, result.positions))
    except OSError as exc:
        raise StefanAppError("Unable to export interface history.", user_message="无法导出相界面轨迹。") from exc
    return target


def export_result_bundle(
    result: SimulationResult,
    parameters: StefanParameters,
    target_directory: Path,
) -> ExportedResultFiles:
    """Write parameters, summary, interface history, and temperature history."""
    try:
        target_directory.mkdir(parents=True, exist_ok=True)
        parameter_file = save_parameters_json(parameters, target_directory / "parameters.json")
        summary_file = _write_summary_csv(result, target_directory / "summary.csv")
        interface_file = export_result_csv(result, target_directory / "interface_history.csv")
        temperature_file = _write_temperature_history_csv(result, target_directory / "temperature_history.csv")
    except StefanAppError:
        raise
    except OSError as exc:
        raise StefanAppError("Unable to export result bundle.", user_message="无法导出完整仿真结果。") from exc
    return ExportedResultFiles(
        directory=target_directory,
        parameters=parameter_file,
        summary=summary_file,
        interface_history=interface_file,
        temperature_history=temperature_file,
    )


def _write_summary_csv(result: SimulationResult, target: Path) -> Path:
    summary = result.summarize()
    rows = (
        ("status", summary.status),
        ("message", summary.message),
        ("final_time", summary.final_time),
        ("final_interface_position", summary.final_interface_position),
        ("minimum_temperature", summary.minimum_temperature),
        ("maximum_temperature", summary.maximum_temperature),
        ("stored_steps", summary.stored_steps),
    )
    with target.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["metric", "value"])
        writer.writerows(rows)
    return target


def _write_temperature_history_csv(result: SimulationResult, target: Path) -> Path:
    with target.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["time", *(f"x={coordinate:.12g}" for coordinate in result.x_coordinates)])
        for time, temperatures in zip(result.times, result.temperatures):
            writer.writerow([time, *temperatures])
    return target
