"""Streamlit rendering for the current-day news briefing."""

from collections.abc import Callable
from typing import Any

from .app_support import build_todays_briefing
from .models import NewsCategory
from .ui_helpers import category_label
from .vector_store import EmbeddingProviderMismatch, VectorStore


def render_todays_briefing(
    st: Any,
    store: VectorStore,
    show_article_details: Callable[[str, str, str, str, str], None],
) -> None:
    """Render indexed current-day articles without triggering ingestion."""
    st.subheader("Today's Briefing")
    if store.count() == 0:
        st.info("Run ingestion to load today's news briefing.")
        return
    try:
        with st.spinner("Loading today's news briefing..."):
            briefing = build_todays_briefing(store)
    except EmbeddingProviderMismatch as error:
        st.warning(
            f"{error} Use **Reset Indexed chunks data**, then **Run ingestion** to rebuild the index."
        )
        return
    if not briefing:
        st.info("No indexed news is available for today.")
    for category, response in briefing:
        with st.expander(category_label(category), expanded=False):
            columns = st.columns(min(3, max(1, len(response.citations))))
            for index, citation in enumerate(response.citations):
                with columns[index % len(columns)]:
                    with st.container(border=True):
                        st.markdown(f"**{citation.title}**")
                        st.caption(f"{citation.source} | {citation.published_at.strftime('%d-%b-%Y')}")
                        if st.button("View details", key=f"briefing-article-{category.value}-{index}"):
                            show_article_details(
                                citation.title,
                                citation.source,
                                citation.published_at.strftime("%d-%b-%Y"),
                                getattr(citation, "summary", "") or response.answer,
                                citation.url,
                            )