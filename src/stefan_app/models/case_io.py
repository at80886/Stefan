"""JSON case-file support for Stefan simulation parameters."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from stefan_app.models.simulation import BoundaryCondition, StefanParameters
from stefan_app.utils.exceptions import StefanAppError


def parameters_to_dict(parameters: StefanParameters) -> dict[str, float | int]:
    """Convert simulation parameters to the flat JSON structure used by case files."""
    return {
        "domain_length": parameters.domain_length,
        "node_count": parameters.node_count,
        "initial_temperature": parameters.initial_temperature,
        "melting_temperature": parameters.melting_temperature,
        "left_boundary_temperature": parameters.left_boundary.temperature,
        "right_boundary_temperature": parameters.right_boundary.temperature,
        "thermal_diffusivity": parameters.thermal_diffusivity,
        "stefan_number": parameters.stefan_number,
        "phase_change_interval": parameters.phase_change_interval,
        "time_step": parameters.time_step,
        "duration": parameters.duration,
        "output_stride": parameters.output_stride,
    }


def parameters_from_dict(data: Mapping[str, Any]) -> StefanParameters:
    """Build validated simulation parameters from a case-file mapping."""
    defaults = StefanParameters()
    try:
        parameters = StefanParameters(
            domain_length=float(data.get("domain_length", defaults.domain_length)),
            node_count=int(data.get("node_count", defaults.node_count)),
            initial_temperature=float(data.get("initial_temperature", defaults.initial_temperature)),
            melting_temperature=float(data.get("melting_temperature", defaults.melting_temperature)),
            left_boundary=BoundaryCondition(
                "left",
                float(data.get("left_boundary_temperature", defaults.left_boundary.temperature)),
            ),
            right_boundary=BoundaryCondition(
                "right",
                float(data.get("right_boundary_temperature", defaults.right_boundary.temperature)),
            ),
            thermal_diffusivity=float(data.get("thermal_diffusivity", defaults.thermal_diffusivity)),
            stefan_number=float(data.get("stefan_number", defaults.stefan_number)),
            phase_change_interval=float(data.get("phase_change_interval", defaults.phase_change_interval)),
            time_step=float(data.get("time_step", defaults.time_step)),
            duration=float(data.get("duration", defaults.duration)),
            output_stride=int(data.get("output_stride", defaults.output_stride)),
        )
    except (TypeError, ValueError) as exc:
        raise StefanAppError("Invalid case-file value.", user_message="参数文件中包含无法识别的数值。") from exc
    parameters.validate()
    return parameters


def load_parameters_json(path: Path) -> StefanParameters:
    """Read and validate a simulation parameter JSON file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise StefanAppError("Unable to read parameter file.", user_message="无法读取参数文件。") from exc
    except json.JSONDecodeError as exc:
        raise StefanAppError("Invalid parameter JSON.", user_message="参数文件不是有效的 JSON 格式。") from exc
    if not isinstance(data, dict):
        raise StefanAppError("Parameter JSON must be an object.", user_message="参数文件内容必须是 JSON 对象。")
    return parameters_from_dict(data)


def save_parameters_json(parameters: StefanParameters, path: Path) -> Path:
    """Write simulation parameters to a UTF-8 JSON case file."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = parameters_to_dict(parameters)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise StefanAppError("Unable to write parameter file.", user_message="无法写入参数文件。") from exc
    return path
