# News RAG

A date-aware news analyst for Technology, Finance, and Politics. The system will collect approved news sources, process and index articles, and answer questions with grounded citations.

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

The ingestion button uses one Google News RSS search per domain in development. Set `NEWS_RAG_TECHNOLOGY_RSS_URLS`, `NEWS_RAG_FINANCE_RSS_URLS`, and `NEWS_RAG_POLITICS_RSS_URLS` in `.env` as comma-separated approved RSS URLs to replace those defaults.

## Repository structure

- `app.py`: Streamlit chat interface and manual ingestion controls
- `app.py`: Streamlit chat, filters, manual ingestion, and optional Today's Briefing
- `src/news_rag/models.py`: shared domain contracts
- `src/news_rag/ingestion.py`: RSS parsing and domain fetchers
- `src/news_rag/processing.py`: deterministic cleaning, enrichment, and chunking
- `src/news_rag/vector_store.py`: embeddings and persistent vector-store adapters
- `src/news_rag/orchestration.py`: manual pipeline runs and interval scheduling
- `src/news_rag/query_engine.py`: date-aware retrieval, grounded answers, and citations
- `src/news_rag/evaluation.py`: evaluation dataset and score utilities
- `tests/`: automated tests
- `evaluation/questions.json`: 20-case evaluation dataset
- `SystemRequirements.md`: original requirements
- `PLAN.md`: phased implementation plan
- `PROGRESS.md`: phase completion record
