"""Streamlit user interface for the News RAG application."""

from datetime import date, datetime, timezone

from news_rag.config import Settings
from news_rag.ingestion import FinanceFetcher, PoliticsFetcher, StocksFetcher, TechnologyFetcher
from news_rag.models import ArticleChunk, NewsCategory, QueryResponse
from news_rag.orchestration import NewsPipeline
from news_rag.query_engine import QueryEngine, QueryInterpreter
from news_rag.sources import sources_for
from news_rag.vector_store import VectorStore, build_vector_store
from news_rag.ui_helpers import apply_filters, category_label, citation_lines


def build_store(settings: Settings) -> VectorStore:
    return build_vector_store(settings)


def build_pipeline(store: VectorStore) -> NewsPipeline:
    return NewsPipeline(
        fetchers=(
            TechnologyFetcher(sources_for(NewsCategory.TECHNOLOGY)),
            FinanceFetcher(sources_for(NewsCategory.FINANCE)),
            PoliticsFetcher(sources_for(NewsCategory.POLITICS)),
            StocksFetcher(sources_for(NewsCategory.STOCKS)),
        ),
        store=store,
    )


def build_sample_questions(store: VectorStore) -> dict[NewsCategory, tuple[str, ...]]:
    questions: dict[NewsCategory, tuple[str, ...]] = {}
    for category in NewsCategory:
        chunks = store.query(category.value, category=category, limit=4)
        titles: list[str] = []
        for chunk in chunks:
            title = chunk.metadata.get("title", "").strip()
            if title and title not in titles:
                titles.append(title)
        questions[category] = tuple(f"What is this story about: {title}?" for title in titles[:2])
    return questions


def build_todays_briefing(store: VectorStore, now: datetime | None = None) -> list[tuple[NewsCategory, QueryResponse]]:
    """Build one grounded response per domain from the last 24 hours."""
    clock = lambda: now or datetime.now(timezone.utc)
    engine = QueryEngine(store, interpreter=QueryInterpreter(clock=clock))
    briefing: list[tuple[NewsCategory, QueryResponse]] = []
    for category in NewsCategory:
        response = engine.answer(f"latest {category.value} news today")
        if response.grounded:
            briefing.append((category, response))
    return briefing


def main() -> None:
    try:
        import streamlit as st
    except ImportError as error:
        raise RuntimeError('Install the "ui" extra to run the Streamlit application') from error

    settings = Settings.from_environment()
    store = build_store(settings)
    engine = QueryEngine(store)
    pipeline = build_pipeline(store)

    st.set_page_config(page_title="News RAG", page_icon="N", layout="wide")
    st.title("News RAG Analyst")
    st.caption("Answers are generated only from indexed, dated source material.")

    with st.sidebar:
        st.header("Filters")
        category_value = st.selectbox("Category", ["All", *[category_label(category) for category in NewsCategory]])
        start_date = st.date_input("Published after", value=None)
        st.divider()
        show_briefing = st.checkbox("Today's Briefing")
        st.metric("Indexed chunks", store.count())
        if st.button("Run ingestion", type="secondary"):
            with st.spinner("Collecting and indexing sources..."):
                report = pipeline.run_once()
            if report.succeeded:
                st.success(f"Stored {report.chunks_stored} chunks from {report.articles_fetched} articles.")
            else:
                st.warning("Ingestion completed with errors: " + "; ".join(report.errors))

        with st.expander("Sample questions for today"):
            sample_questions = build_sample_questions(store)
            has_questions = False
            for category in NewsCategory:
                questions = sample_questions[category]
                if not questions:
                    continue
                has_questions = True
                st.markdown(f"**{category_label(category)}**")
                for question in questions:
                    st.markdown(f"- {question}")
            if not has_questions:
                st.info("Run ingestion to see questions from today's news.")

    if show_briefing:
        st.subheader("Today's Briefing")
        briefing = build_todays_briefing(store)
        if not briefing:
            st.info("No news has been indexed for today.")
        for category, response in briefing:
            with st.expander(category_label(category), expanded=True):
                st.markdown(response.answer)
                for line in citation_lines(response):
                    st.markdown(line)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Ask about recent technology, finance, or politics news")
    if question:
        category = next(
            (candidate for candidate in NewsCategory if category_label(candidate) == category_value),
            None,
        )
        effective_question = apply_filters(question, category, start_date)
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
            st.markdown(response.answer)
            if response.citations:
                with st.expander("Sources"):
                    for line in citation_lines(response):
                        st.markdown(line)
            elif not response.grounded:
                st.info("No matching sources were found.")
        st.session_state.messages.append({"role": "assistant", "content": response.answer})


if __name__ == "__main__":
    main()
