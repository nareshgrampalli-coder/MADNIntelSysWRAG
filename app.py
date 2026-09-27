"""Streamlit user interface for the News RAG application."""

from concurrent.futures import ThreadPoolExecutor
from time import monotonic, sleep

from news_rag.config import Settings
from news_rag.ingestion import FinanceFetcher, PoliticsFetcher, SportsFetcher, StocksFetcher, TechnologyFetcher
from news_rag.models import NewsCategory
from news_rag.orchestration import NewsPipeline
from news_rag.query_engine import QueryEngine
from news_rag.sources import sources_for
from news_rag.vector_store import VectorStore, build_vector_store
from news_rag.ui_helpers import apply_filters, category_label, citation_lines, trim_sentence
from news_rag.app_support import (
    build_sample_questions,
    build_contextual_question,
    build_todays_briefing,
    verify_grounding_quality,
    verify_query_interpretation,
    verify_retrieval_quality,
)
from news_rag.briefing_view import render_todays_briefing
from news_rag.ui_styles import apply_styles


def build_store(settings: Settings) -> VectorStore:
    return build_vector_store(settings)


def build_pipeline(store: VectorStore) -> NewsPipeline:
    return NewsPipeline(
        fetchers=(
            TechnologyFetcher(sources_for(NewsCategory.TECHNOLOGY)),
            FinanceFetcher(sources_for(NewsCategory.FINANCE)),
            PoliticsFetcher(sources_for(NewsCategory.POLITICS)),
            StocksFetcher(sources_for(NewsCategory.STOCKS)),
            SportsFetcher(sources_for(NewsCategory.SPORTS)),
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
    if store.count() > 0:
        st.session_state.setdefault("ingestion_completed", True)

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
        if st.button("Reset Indexed chunks data", type="tertiary"):
            store.reset()
            st.session_state.ingestion_completed = False
            st.session_state.pop("briefing_ingestion_date", None)
            st.rerun()
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
                section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
                    background-color: #198754;
                    border-color: #198754;
                    color: white;
                }
                section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover {
                    background-color: #157347;
                    border-color: #146c43;
                    color: white;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
        if st.button("Run ingestion", type="primary" if ingestion_done else "secondary"):
            countdown = st.empty()
            started = monotonic()
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(pipeline.run_once)
                while not future.done():
                    remaining = max(0, 90 - int(monotonic() - started))
                    countdown.info(f"Collecting and indexing sources... approximately {remaining}s remaining")
                    sleep(1)
                report = future.result()
            elapsed_seconds = monotonic() - started
            countdown.empty()
            if report.succeeded:
                st.session_state.ingestion_completed = True
            if report.succeeded:
                category_counts = ", ".join(
                    f"{category}: {count}" for category, count in sorted(report.articles_by_category.items())
                ) or "no category data"
                retrieval_coverage = verify_retrieval_quality(store)
                interpretation_checks = verify_query_interpretation()
                grounding_checks = verify_grounding_quality(store)
                coverage_counts = ", ".join(
                    f"{category.value}: {count}"
                    for category, count in retrieval_coverage.items()
                )
                uncovered = [category.value for category, count in retrieval_coverage.items() if count == 0]
                interpretation_passed = sum(interpretation_checks.values())
                grounding_passed = sum(grounding_checks.values())
                st.success(
                    f"Stored {report.chunks_stored} chunks from {report.articles_fetched} articles. "
                    f"By category: {category_counts}. "
                    f"Retrieval check: {coverage_counts}. "
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
            else:
                st.warning(
                    "Ingestion completed with errors: "
                    + "; ".join(report.errors)
                    + f" Ingestion time: {elapsed_seconds:.1f}s."
                )

        with st.expander("Sample questions for today"):
            st.markdown("- Summarize todays news in 3 bullet points.")
            st.markdown("- Summarize in 3 bullet points for each category.")
            st.markdown("- What is stock news today?")
            st.markdown("- What happened in finance this week?")
            st.markdown("- Which news should I focus on today?")

    @st.fragment
    def render_briefing() -> None:
        if not show_briefing:
            return
        render_todays_briefing(st, store, show_article_details)

    render_briefing()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    chat_disabled = not st.session_state.get("ingestion_completed", False)
    if chat_disabled:
        st.markdown(
            """
            <style>
            [data-testid="stChatInput"] {
                position: relative;
            }
            [data-testid="stChatInput"]:hover::after {
                content: "Click Run ingestion to load news before asking a question.";
                position: absolute;
                left: 0;
                bottom: calc(100% + 0.4rem);
                z-index: 10;
                padding: 0.45rem 0.65rem;
                border-radius: 0.35rem;
                background: #212529;
                color: #fff;
                font-size: 0.8rem;
                pointer-events: none;
                white-space: nowrap;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
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
            answer_lines = [line.strip("- ").strip() for line in response.answer.splitlines() if line.strip()]
            if len(answer_lines) < 3:
                answer_lines = [part.strip() for part in response.answer.split(". ") if part.strip()]
            chat_answer = "\n".join(
                f"- {trim_sentence(line)}" for line in answer_lines[:3]
            )
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
