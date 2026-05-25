"""CSV export support for simulation result bundles."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from stefan_app.models import SimulationResult, StefanParameters
from stefan_app.models.case_io import parameters_to_dict, save_parameters_json
from stefan_app.utils.exceptions import StefanAppError

CSV_ENCODING = "utf-8"
CSV_ENCODING_WITH_SIGNATURE = "utf-8-sig"


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
        with target.open("w", newline="", encoding=CSV_ENCODING) as file:
            writer = csv.writer(file)
            writer.writerow(["time", "interface_position"])
            writer.writerows(
                (_format_number(time), _format_number(position))
                for time, position in zip(result.times, result.positions)
            )
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
        summary_file = _write_summary_csv(result, parameters, target_directory / "summary.csv")
        interface_file = export_result_csv(result, target_directory / "interface.csv")
        temperature_file = _write_temperature_distribution_csv(
            result,
            target_directory / "temperature.csv",
        )
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


def _write_summary_csv(result: SimulationResult, parameters: StefanParameters, target: Path) -> Path:
    summary = result.summarize()
    rows = tuple(parameters_to_dict(parameters).items()) + (
        ("final_interface_position", summary.final_interface_position),
    )
    with target.open("w", newline="", encoding=CSV_ENCODING_WITH_SIGNATURE) as file:
        writer = csv.writer(file)
        writer.writerow(["metric", "value"])
        writer.writerows((metric, _format_cell(value)) for metric, value in rows)
    return target


def _write_temperature_distribution_csv(result: SimulationResult, target: Path) -> Path:
    """Write the final temperature distribution only."""
    final_temperatures = result.temperatures[-1] if result.temperatures else ()
    with target.open("w", newline="", encoding=CSV_ENCODING) as file:
        writer = csv.writer(file)
        writer.writerow(["x", "temperature"])
        for x_coordinate, temperature in zip(result.x_coordinates, final_temperatures):
            writer.writerow([_format_number(x_coordinate), _format_number(temperature)])
    return target


def _format_cell(value: object) -> object:
    if isinstance(value, float):
        return _format_number(value)
    return value


def _format_number(value: float) -> str:
    return f"{value:.12g}"
