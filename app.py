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


RAG_STAGES = (
    "Data Ingestion",
    "Text Chunking",
    "Embedding Generation",
    "Vector Database Storage",
    "Query Processing",
    "Similarity Search",
    "Prompt Augmentation",
    "Response Generation",
)


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
        questions[category] = tuple(f"What happened in {title}?" for title in titles[:3])
    return questions


def build_todays_briefing(store: VectorStore, now: datetime | None = None) -> list[tuple[NewsCategory, QueryResponse]]:
    """Build one grounded response per domain from the last 24 hours."""
    clock = lambda: now or datetime.now(timezone.utc)
    engine = QueryEngine(store, interpreter=QueryInterpreter(clock=clock), retrieval_limit=6)
    briefing: list[tuple[NewsCategory, QueryResponse]] = []
    seen_urls: set[str] = set()
    for category in NewsCategory:
        topic = "stock market" if category is NewsCategory.STOCKS else category.value
        response = engine.answer(f"latest {topic} news today", relevance_threshold=0.0)
        citations = [citation for citation in response.citations if citation.url not in seen_urls]
        if len(citations) < 6:
            latest_response = engine.answer(f"latest {topic} news", relevance_threshold=0.0)
            category_urls = {citation.url for citation in citations}
            citations.extend(
                citation
                for citation in latest_response.citations
                if citation.url not in seen_urls and citation.url not in category_urls
            )
        citations = tuple(citations[:6])
        if not citations:
            continue
        seen_urls.update(citation.url for citation in citations)
        briefing.append((category, QueryResponse(answer=response.answer, citations=citations, grounded=True)))
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

    @st.dialog("Article details")
    def show_article_details(title: str, source: str, published_date: str, summary: str, url: str) -> None:
        st.subheader(title)
        st.caption(f"{source} | {published_date}")
        st.write(summary)
        st.link_button("Read full article", url)

    st.set_page_config(page_title="News RAG", page_icon="N", layout="wide")
    st.markdown(
        """
        <style>
        @media (max-width: 640px) {
            [data-testid="stHorizontalBlock"] {
                flex-direction: column;
                gap: 0.75rem;
            }
            [data-testid="stHorizontalBlock"] > div {
                width: 100% !important;
                flex: 1 1 100% !important;
            }
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            min-height: 170px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("News RAG Analyst")
    st.caption("Answers are generated only from indexed, dated source material.")

    with st.sidebar:
        st.header("Filters")
        category_value = st.selectbox("Category", ["All", *[category_label(category) for category in NewsCategory]])
        start_date = st.date_input("Published after", value=None)
        st.divider()
        show_briefing = st.checkbox("Today's Briefing")
        st.metric("Indexed chunks", store.count())
        ingestion_done = st.session_state.get("ingestion_completed", False)
        ingestion_color = "#198754" if ingestion_done else "#dc3545"
        ingestion_label = "Complete" if ingestion_done else "Required"
        if not ingestion_done:
            st.markdown(
                f'<div style="color:{ingestion_color};font-weight:700">Run Ingestion: {ingestion_label}</div>',
                unsafe_allow_html=True,
            )
        if st.button("Run ingestion", type="primary" if ingestion_done else "secondary"):
            with st.spinner("Collecting and indexing sources..."):
                report = pipeline.run_once()
            if report.succeeded:
                st.session_state.ingestion_completed = True
            if report.succeeded:
                st.success(f"Stored {report.chunks_stored} chunks from {report.articles_fetched} articles.")
            else:
                st.warning("Ingestion completed with errors: " + "; ".join(report.errors))

        rag_done = st.session_state.get("rag_pipeline_completed", False)
        rag_color = "#198754" if rag_done else "#dc3545"
        rag_label = "Complete" if rag_done else "Required"
        st.markdown(
            f'<div style="color:{rag_color};font-weight:700">Run RAG Pipeline: {rag_label}</div>',
            unsafe_allow_html=True,
        )
        if st.button("Run RAG pipeline", type="primary"):
            with st.status("Running RAG pipeline", expanded=True) as pipeline_status:
                report = pipeline.run_once()
                st.write("Data Ingestion: complete")
                st.write("Text Chunking: complete")
                st.write("Embedding Generation: complete")
                st.write("Vector Database Storage: complete" if not report.errors else "Vector Database Storage: check errors")
                st.write("Query Processing: ready for a question")
                st.write("Similarity Search: ready for a question")
                st.write("Prompt Augmentation: ready for a question")
                st.write("Response Generation: ready for a question")
                pipeline_status.update(label="RAG pipeline ready", state="complete")
            if report.succeeded:
                st.session_state.ingestion_completed = True
                st.session_state.rag_pipeline_completed = True

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

    @st.fragment
    def render_briefing() -> None:
        if not show_briefing:
            return
        ingestion_key = date.today().isoformat()
        if st.session_state.get("briefing_ingestion_date") != ingestion_key:
            with st.spinner("Updating today's category news..."):
                daily_report = pipeline.run_once()
            st.session_state.briefing_ingestion_date = ingestion_key
            if daily_report.succeeded:
                st.session_state.ingestion_completed = True
            if daily_report.errors:
                st.warning("Some categories could not be updated: " + "; ".join(daily_report.errors))
        st.subheader("Today's Briefing")
        briefing = build_todays_briefing(store)
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
                                    response.answer,
                                    citation.url,
                                )

    render_briefing()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    chat_disabled = store.count() == 0
    if chat_disabled:
        st.info("Run ingestion before asking a question.")
    question = st.chat_input(
        "Run ingestion to enable questions" if chat_disabled else "Ask about recent news",
        disabled=chat_disabled,
    )
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
