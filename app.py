"""Streamlit user interface for the News RAG application."""

import os
from time import monotonic

from news_rag.config import Settings
from news_rag.ingestion import FinanceFetcher, PoliticsFetcher, RssSourceAdapter, SportsFetcher, StocksFetcher, TechnologyFetcher
from news_rag.models import NewsCategory
from news_rag.orchestration import NewsPipeline
from news_rag.query_engine import QueryEngine
from news_rag.sources import sources_for
from news_rag.vector_store import VectorStore, build_vector_store
from news_rag.ui_helpers import apply_filters, category_label, citation_lines, format_chat_answer
from news_rag.app_support import (
    build_sample_questions,
    build_contextual_question,
    build_todays_briefing,
    initialize_ingestion_status,
)
from news_rag.briefing_view import render_todays_briefing
from news_rag.ingestion_view import render_ingestion_sidebar
from news_rag.ui_styles import apply_styles


def build_store(settings: Settings) -> VectorStore:
    return build_vector_store(settings)


def build_pipeline(store: VectorStore, cache_dir=None) -> NewsPipeline:
    adapter = RssSourceAdapter(cache_dir=cache_dir)
    return NewsPipeline(
        fetchers=(
            TechnologyFetcher(sources_for(NewsCategory.TECHNOLOGY), adapter),
            FinanceFetcher(sources_for(NewsCategory.FINANCE), adapter),
            PoliticsFetcher(sources_for(NewsCategory.POLITICS), adapter),
            StocksFetcher(sources_for(NewsCategory.STOCKS), adapter),
            SportsFetcher(sources_for(NewsCategory.SPORTS), adapter),
        ),
        store=store,
    )


def scheduled_ingestion_interval() -> float | None:
    value = os.getenv("NEWS_RAG_AUTO_INGEST_SECONDS", "").strip()
    if not value:
        return None
    try:
        interval = float(value)
    except ValueError as error:
        raise ValueError("NEWS_RAG_AUTO_INGEST_SECONDS must be a positive number") from error
    if interval <= 0:
        raise ValueError("NEWS_RAG_AUTO_INGEST_SECONDS must be a positive number")
    return interval


def main() -> None:
    try:
        import streamlit as st
    except ImportError as error:
        raise RuntimeError('Install the "ui" extra to run the Streamlit application') from error

    st.set_page_config(page_title="News RAG", page_icon="N", layout="wide")
    apply_styles(st)
    st.title("News RAG Analyst")
    st.caption("Answers are generated only from indexed, dated source material.")

    with st.spinner("Preparing the news index..."):
        settings = Settings.from_environment()
        store = build_store(settings)
        engine = QueryEngine(store)
        pipeline = build_pipeline(store, settings.data_dir / "http_cache")
        auto_ingest_seconds = scheduled_ingestion_interval()
        initialize_ingestion_status(st.session_state)

    @st.fragment(run_every=auto_ingest_seconds)
    def run_scheduled_ingestion() -> None:
        if auto_ingest_seconds is None:
            return
        started = monotonic()
        report = pipeline.run_once()
        st.session_state.scheduled_ingestion_at = monotonic()
        if report.succeeded:
            st.session_state.ingestion_completed = True
            st.toast(f"Scheduled ingestion stored {report.chunks_stored} chunks.")
        else:
            st.warning("Scheduled ingestion failed: " + "; ".join(report.errors))

    run_scheduled_ingestion()
    @st.dialog("Article details")
    def show_article_details(title: str, source: str, published_date: str, summary: str, url: str) -> None:
        st.subheader(title)
        st.caption(f"{source} | {published_date}")
        st.write(summary)
        st.link_button("Read full article", url)

    def reset_ingestion_state() -> None:
        st.session_state.ingestion_completed = False
        st.session_state.pop("briefing_ingestion_date", None)

    category_value, start_date, show_briefing = render_ingestion_sidebar(
        st,
        store,
        pipeline,
        reset_ingestion_state,
    )

    @st.fragment
    def render_briefing() -> None:
        if not show_briefing:
            return
        render_todays_briefing(st, store, show_article_details)

    if not show_briefing:
        st.info(
            "No news is displayed yet. Select **Today's Briefing** in the sidebar to view today's articles. "
            "If the briefing is empty, run ingestion first."
        )
    render_briefing()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    chat_disabled = not st.session_state.get("ingestion_completed", False)
    question = st.chat_input(
        "Click Run Ingestion button to ask questions" if chat_disabled else "Ask about recent news",
        disabled=chat_disabled,
    )
    if question:
        category = next(
            (candidate for candidate in NewsCategory if category_label(candidate) == category_value),
            None,
        )
        contextual_question = build_contextual_question(st.session_state.messages, question)
        effective_question = apply_filters(contextual_question, category, start_date)
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Searching indexed sources..."):
                try:
                    response = engine.answer(effective_question)
                except Exception as error:
                    st.error(f"Unable to answer this question: {error}")
                    return
            chat_answer = format_chat_answer(response.answer)
            st.markdown(chat_answer)
            if response.citations:
                with st.expander("Sources"):
                    for line in citation_lines(response):
                        st.markdown(line)
            elif not response.grounded:
                st.info("No matching sources were found.")
        st.session_state.messages.append({"role": "assistant", "content": chat_answer})


if __name__ == "__main__":
    main()
