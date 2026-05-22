"""Logging configuration for application modules."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(log_file: Path | None = None) -> None:
    """Configure a simple application logger for console or file output."""
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )
