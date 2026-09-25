"""Default source configuration placeholder.

Actual feed URLs should be approved and configured by the deployment environment.
"""

from .ingestion import FeedSource
from .models import NewsCategory


DEFAULT_SOURCES: tuple[FeedSource, ...] = ()


def sources_for(category: NewsCategory) -> tuple[FeedSource, ...]:
    return tuple(source for source in DEFAULT_SOURCES if source.category is category)
