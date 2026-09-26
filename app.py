"""Streamlit user interface for the News RAG application."""

from datetime import date

from news_rag.config import Settings
from news_rag.ingestion import FinanceFetcher, PoliticsFetcher, StocksFetcher, TechnologyFetcher
from news_rag.models import NewsCategory
from news_rag.orchestration import NewsPipeline
from news_rag.query_engine import QueryEngine
from news_rag.sources import sources_for
from news_rag.vector_store import VectorStore, build_vector_store
from news_rag.ui_helpers import apply_filters, category_label, citation_lines
from news_rag.app_support import build_sample_questions, build_todays_briefing
from news_rag.ui_styles import apply_styles


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
    apply_styles(st)
    st.title("News RAG Analyst")
    st.caption("Answers are generated only from indexed, dated source material.")

    with st.sidebar:
        st.header("Filters")
        category_value = st.selectbox("Category", ["All", *[category_label(category) for category in NewsCategory]])
        start_date = st.date_input("Published after", value=None)
        st.divider()
        show_briefing = st.checkbox("Today's Briefing", value=True)
        st.metric("Indexed chunks", store.count())
        ingestion_done = st.session_state.get("ingestion_completed", False)
        ingestion_color = "#198754" if ingestion_done else "#dc3545"
        ingestion_label = "Complete" if ingestion_done else "Required"
        if not ingestion_done:
            st.markdown(
                f'<div style="color:{ingestion_color};font-weight:700">Run Ingestion: {ingestion_label}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="color:{ingestion_color};font-weight:700">Run Ingestion: {ingestion_label}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <style>
                section[data-testid="stSidebar"] div[data-testid="stButton"]:first-of-type button {
                    background-color: #198754;
                    border-color: #198754;
                    color: white;
                }
                section[data-testid="stSidebar"] div[data-testid="stButton"]:first-of-type button:hover {
                    background-color: #157347;
                    border-color: #146c43;
                    color: white;
                }
                </style>
                """,
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
        if not rag_done:
            st.markdown(
                """
                <style>
                section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] {
                    background-color: #dc3545;
                    border-color: #dc3545;
                    color: white;
                }
                section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover {
                    background-color: #bb2d3b;
                    border-color: #b02a37;
                    color: white;
                }
                section[data-testid="stSidebar"] div[data-testid="stButton"]:nth-of-type(2) button {
                    background-color: #dc3545;
                    border-color: #dc3545;
                    color: white;
                }
                section[data-testid="stSidebar"] div[data-testid="stButton"]:nth-of-type(2) button:hover {
                    background-color: #bb2d3b;
                    border-color: #b02a37;
                    color: white;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
        if st.button("Run RAG pipeline", type="primary" if rag_done else "secondary"):
            with st.status("Running RAG pipeline", expanded=True) as pipeline_status:
                report = pipeline.run_once()
                if report.succeeded and report.chunks_stored:
                    pipeline_query = "Summarize today's technology, finance, politics, and stocks news."
                    pipeline_response = engine.answer(pipeline_query)
                    st.write(f"Data Ingestion: fetched {report.articles_fetched} articles")
                    st.write(f"Text Chunking: created {report.chunks_stored} chunks")
                    st.write("Embedding Generation: generated and indexed embeddings")
                    st.write("Vector Database Storage: stored successfully")
                    st.write("Query Processing: interpreted category and date filters")
                    st.write(f"Similarity Search: retrieved {len(pipeline_response.citations)} sources")
                    st.write("Prompt Augmentation: assembled grounded excerpts")
                    st.write("Response Generation: generated grounded response")
                    pipeline_status.update(label="RAG pipeline complete", state="complete")
                else:
                    st.write("RAG pipeline stopped: ingestion produced no usable chunks")
                    pipeline_status.update(label="RAG pipeline failed", state="error")
            if report.succeeded and report.chunks_stored:
                st.session_state.ingestion_completed = True
                st.session_state.rag_pipeline_completed = True

        with st.expander("Sample questions for today"):
            st.markdown("- Summarize todays news in 3 bullet points.")
            st.markdown("- Summarize in 3 bullet points for each category.")

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
