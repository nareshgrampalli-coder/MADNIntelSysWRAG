"""Logging setup for local runs and scheduled jobs."""

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure a consistent application-wide log format."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
