# News RAG

A date-aware news analyst for Technology, Finance, Politics, and the India-only Stocks category. The system will collect approved news sources, process and index articles, and answer questions with grounded citations.

## Status

The MVP implementation is complete. See [PLAN.md](PLAN.md), [PROGRESS.md](PROGRESS.md), and [DEPLOYMENT.md](DEPLOYMENT.md) for the phase record and deployment instructions.

## Local setup

Requires Python 3.11 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev]"
Copy-Item .env.example .env
py -m pytest
```

To run the optional Streamlit UI:

```powershell
py -m pip install -e ".[ui]"
streamlit run app.py
```

Run scheduled ingestion with `py worker.py`. Set `NEWS_RAG_INTERVAL_SECONDS=3600` for hourly runs; the default is daily. Set `NEWS_RAG_VECTOR_BACKEND=chroma` when the optional ChromaDB dependency and durable storage are available.

The ingestion button uses multiple Google News RSS searches per domain in development to improve daily coverage. Set `NEWS_RAG_TECHNOLOGY_RSS_URLS`, `NEWS_RAG_FINANCE_RSS_URLS`, `NEWS_RAG_POLITICS_RSS_URLS`, and `NEWS_RAG_STOCKS_RSS_URLS` in `.env` as comma-separated feed URLs to replace those defaults. For production, use the matching `*_APPROVED_RSS_URLS` variables for operator-approved official feeds.

## Repository structure

- `app.py`: Streamlit chat, filters, manual ingestion, and optional Today's Briefing
- `src/news_rag/models.py`: shared domain contracts
- `src/news_rag/ingestion.py`: RSS parsing and domain fetchers
- `src/news_rag/processing.py`: deterministic cleaning, enrichment, and chunking
- `src/news_rag/vector_store.py`: embeddings and persistent vector-store adapters
- `src/news_rag/orchestration.py`: manual pipeline runs and interval scheduling
- `worker.py`: standalone scheduled ingestion worker
- `api/health.py`: Vercel health endpoint with deployment metadata
- `src/news_rag/query_engine.py`: date-aware retrieval, grounded answers, and citations
- `src/news_rag/ui_helpers.py`: Streamlit filter and citation presentation helpers
- `src/news_rag/evaluation.py`: evaluation dataset and score utilities
- `tests/`: automated tests
- `evaluation/questions.json`: 20-case evaluation dataset
- `SystemRequirements.md`: original requirements
- `PLAN.md`: phased implementation plan
- `PROGRESS.md`: phase completion record
- `COMPLIANCE_REPORT.md`: requirements compliance matrix
