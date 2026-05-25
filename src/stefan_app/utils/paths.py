"""Canonical project resource paths."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PACKAGE_ROOT.parent
PROJECT_ROOT = SRC_ROOT.parent
_FROZEN_ROOT = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
RESOURCE_ROOT = (_FROZEN_ROOT if getattr(sys, "frozen", False) else PROJECT_ROOT) / "resources"
STYLE_FILE = RESOURCE_ROOT / "styles" / "app.qss"
EXAMPLE_CASE_FILE = RESOURCE_ROOT / "examples" / "default_case.json"
APP_STATE_ROOT = (
    Path(os.environ["LOCALAPPDATA"]) / "StefanSimulator"
    if "LOCALAPPDATA" in os.environ
    else Path.home() / ".stefan_app"
)
LAST_SESSION_PARAMETERS_FILE = APP_STATE_ROOT / "last_parameters.json"
