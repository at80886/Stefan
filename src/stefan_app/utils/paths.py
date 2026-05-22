"""Canonical project resource paths."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PACKAGE_ROOT.parent
PROJECT_ROOT = SRC_ROOT.parent
RESOURCE_ROOT = PROJECT_ROOT / "resources"
STYLE_FILE = RESOURCE_ROOT / "styles" / "app.qss"
EXAMPLE_CASE_FILE = RESOURCE_ROOT / "examples" / "default_case.json"
