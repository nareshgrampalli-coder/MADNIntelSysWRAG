"""Pipeline orchestration for ingestion through vector storage."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from threading import Event
from time import sleep

from .ingestion import DomainFetcher
from .processing import process_and_chunk
from .vector_store import JsonVectorStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunReport:
    started_at: datetime
    completed_at: datetime
    articles_fetched: int
    chunks_stored: int
    errors: tuple[str, ...] = ()

    @property
    def succeeded(self) -> bool:
        return not self.errors


class NewsPipeline:
    def __init__(self, fetchers: Iterable[DomainFetcher], store: JsonVectorStore) -> None:
        self.fetchers = tuple(fetchers)
        self.store = store

    def run_once(self) -> RunReport:
        started_at = datetime.now(timezone.utc)
        articles = []
        errors: list[str] = []
        for fetcher in self.fetchers:
            try:
                articles.extend(fetcher.fetch())
            except Exception as error:
                name = fetcher.__class__.__name__
                logger.exception("Fetcher failed: %s", name)
                errors.append(f"{name}: {error}")
        chunks = process_and_chunk(articles)
        try:
            self.store.upsert(chunks)
        except Exception as error:
            logger.exception("Vector-store upsert failed")
            errors.append(f"vector_store: {error}")
        completed_at = datetime.now(timezone.utc)
        return RunReport(
            started_at=started_at,
            completed_at=completed_at,
            articles_fetched=len(articles),
            chunks_stored=len(chunks),
            errors=tuple(errors),
        )


@dataclass
class IntervalScheduler:
    """Minimal scheduler for a long-running worker process."""

    pipeline: NewsPipeline
    interval_seconds: float
    sleeper: Callable[[float], None] = sleep
    stop_event: Event = field(default_factory=Event)

    def run_forever(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        while not self.stop_event.is_set():
            self.pipeline.run_once()
            self.stop_event.wait(self.interval_seconds)

    def stop(self) -> None:
        self.stop_event.set()
