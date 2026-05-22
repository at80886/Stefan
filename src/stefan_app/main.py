"""Command-line entry point for the PyQt6 application."""

from __future__ import annotations

import sys

from stefan_app.app import run


def main() -> int:
    """Start the desktop application and return the process exit code."""
    return run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
