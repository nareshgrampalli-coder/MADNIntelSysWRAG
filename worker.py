"""Run scheduled news ingestion as a standalone Python worker."""

from __future__ import annotations

import logging
import os
import signal

from app import build_pipeline, build_store
from news_rag.config import Settings
from news_rag.logging_config import configure_logging
from news_rag.orchestration import IntervalScheduler

logger = logging.getLogger(__name__)


def interval_seconds() -> float:
    """Read a positive scheduling interval, defaulting to one day."""
    value = os.getenv("NEWS_RAG_INTERVAL_SECONDS", "86400")
    try:
        interval = float(value)
    except ValueError as error:
        raise ValueError("NEWS_RAG_INTERVAL_SECONDS must be a positive number") from error
    if interval <= 0:
        raise ValueError("NEWS_RAG_INTERVAL_SECONDS must be a positive number")
    return interval


def main() -> None:
    settings = Settings.from_environment()
    configure_logging(settings.log_level)
    store = build_store(settings)
    scheduler = IntervalScheduler(build_pipeline(store), interval_seconds())

    def stop_handler(signum: int, _frame: object) -> None:
        logger.info("Received signal %s; stopping ingestion worker", signum)
        scheduler.stop()

    signal.signal(signal.SIGINT, stop_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, stop_handler)
    logger.info("Starting ingestion worker with interval=%s seconds", scheduler.interval_seconds)
    scheduler.run_forever()


if __name__ == "__main__":
    main()
