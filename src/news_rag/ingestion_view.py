"""Streamlit sidebar controls for filtering and updating the news index."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from itertools import cycle
from queue import Empty, Queue
from time import monotonic
from typing import Any

from .app_support import (
    retrieval_metrics,
    verify_grounding_quality,
    verify_query_interpretation,
    verify_retrieval_quality,
)
from .models import NewsCategory
from .orchestration import NewsPipeline
from .ui_helpers import category_label
from .vector_store import VectorStore


def render_ingestion_sidebar(
    st: Any,
    store: VectorStore,
    pipeline: NewsPipeline,
    on_reset: Callable[[], None],
) -> tuple[str, date | None, bool]:
    """Render sidebar filters and ingestion actions; return active view filters."""
    with st.sidebar:
        st.header("Filters")
        if getattr(store, "embedding_warning", None):
            st.warning(store.embedding_warning)
        category_value = st.selectbox(
            "Category",
            ["All", *[category_label(category) for category in NewsCategory]],
        )
        start_date = st.date_input("Published after", value=None)
        st.divider()
        show_briefing = st.checkbox("Today's Briefing", value=False)
        st.metric("Indexed chunks", store.count())
        if st.button("Reset Indexed chunks data", type="tertiary"):
            store.reset()
            on_reset()
            st.rerun()

        ingestion_done = st.session_state.get("ingestion_completed", False)
        ingestion_label = "Complete" if ingestion_done else "Required"
        status_class = "is-complete" if ingestion_done else "is-required"
        st.markdown(
            f'<span class="news-ingestion-status {status_class}">Run Ingestion: {ingestion_label}</span>',
            unsafe_allow_html=True,
        )
        if not ingestion_done and store.count() > 0:
            st.info("For a clean re-ingestion, reset indexed chunks data before running ingestion.")
        if st.button("Run ingestion", type="primary" if ingestion_done else "secondary"):
            _run_ingestion(st, store, pipeline)

        with st.expander("Sample questions for today"):
            st.markdown("- Summarize todays news in 3 bullet points.")
            st.markdown("- Summarize in 3 bullet points for each category.")
            st.markdown("- What is stock news today?")
            st.markdown("- What happened in finance this week?")
            st.markdown("- Which news should I focus on today?")

    return category_value, start_date, show_briefing


def _run_ingestion(st: Any, store: VectorStore, pipeline: NewsPipeline) -> None:
    started = monotonic()
    progress_messages: Queue[str] = Queue()
    idle_messages = cycle((
        "Checking the latest headlines for India relevance...",
        "Gathering article text from matching stories...",
        "Preparing news from all categories for indexing...",
        "Building searchable citations from the selected stories...",
    ))
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(pipeline.run_once, progress_messages.put)
        with st.status("Starting the news harvest...", expanded=True) as status:
            while not future.done():
                try:
                    message = progress_messages.get(timeout=1)
                except Empty:
                    message = next(idle_messages)
                status.update(label=message, state="running")
            report = future.result()
            status.update(label="News index updated.", state="complete")
    elapsed_seconds = monotonic() - started
    if not report.succeeded:
        st.warning(f"Ingestion completed with {len(report.errors)} error(s). Ingestion time: {elapsed_seconds:.1f}s.")
        for error in report.errors:
            st.error(error)
        return

    st.session_state.ingestion_completed = True
    category_counts = ", ".join(
        f"{category}: {count}" for category, count in sorted(report.articles_by_category.items())
    ) or "no category data"
    retrieval_coverage = verify_retrieval_quality(store)
    retrieval_summary = retrieval_metrics(retrieval_coverage)
    interpretation_checks = verify_query_interpretation()
    grounding_checks = verify_grounding_quality(store)
    coverage_counts = ", ".join(
        f"{category.value}: {count}" for category, count in retrieval_coverage.items()
    )
    uncovered = [category.value for category, count in retrieval_coverage.items() if count == 0]
    interpretation_passed = sum(interpretation_checks.values())
    grounding_passed = sum(grounding_checks.values())
    st.success(
        f"Stored {report.chunks_stored} chunks from {report.articles_fetched} articles. "
        f"By category: {category_counts}. "
        f"Retrieval check: {coverage_counts}. "
        f"Sources retrieved: {retrieval_summary['total_sources']}; "
        f"category coverage: {retrieval_summary['coverage_percent']:.1f}%. "
        f"Query interpretation: {interpretation_passed}/{len(interpretation_checks)} checks passed. "
        f"Grounding: {grounding_passed}/{len(grounding_checks)} checks passed. "
        f"Ingestion time: {elapsed_seconds:.1f}s."
    )
    if uncovered:
        st.warning("No retrievable evidence found for: " + ", ".join(uncovered) + ".")
    if interpretation_passed < len(interpretation_checks):
        st.warning("One or more query interpretation checks failed.")
    if grounding_passed < len(grounding_checks):
        st.warning("Grounding verification failed: supported answers must cite evidence and unsupported questions must refuse.")