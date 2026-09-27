# News RAG

A date-aware news analyst for Technology, Finance, Politics, Stocks, and Sports. It collects India-relevant articles from configured RSS sources, indexes article content, and answers questions with extractive, source-grounded citations.

## Status

The MVP implementation is complete. See [docs/PLAN.md](docs/PLAN.md), [docs/PROGRESS.md](docs/PROGRESS.md), and [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the phase record and deployment instructions.

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

Default RSS feeds are LiveMint for Technology, Finance, Politics, Stocks, and Sports, plus Yahoo Finance for Finance. Each category can use comma-separated custom feeds through `NEWS_RAG_<CATEGORY>_RSS_URLS`; operator-approved URLs can be set with the matching `NEWS_RAG_<CATEGORY>_APPROVED_RSS_URLS` variables. Approved URLs take precedence over regular overrides. Legacy `news.google.com` overrides are ignored. Articles are filtered for category relevance and India relevance before indexing.

The current answer generator is deterministic and extractive; no LLM is configured. Hash embeddings are the zero-dependency default. To enable local semantic embeddings, install `py -m pip install -e ".[embeddings]"`, set `NEWS_RAG_EMBEDDING_PROVIDER=sentence-transformers`, and optionally set `NEWS_RAG_EMBEDDING_MODEL` (default `sentence-transformers/all-MiniLM-L6-v2`). The model is downloaded on first use. After changing the provider or model, reset indexed data and re-ingest because vectors from different embedding spaces cannot be mixed.

## Repository structure

- `app.py`: Streamlit chat, filters, manual ingestion, and optional Today's Briefing
- `src/news_rag/models.py`: shared domain contracts
- `src/news_rag/ingestion.py`: RSS parsing and domain fetchers
- `src/news_rag/processing.py`: deterministic cleaning, enrichment, and chunking
- `src/news_rag/vector_store.py`: embeddings and persistent vector-store adapters
- `src/news_rag/orchestration.py`: manual pipeline runs and interval scheduling
- `worker.py`: standalone scheduled ingestion worker
- `api/health.py`: Vercel health endpoint with deployment metadata
- `src/news_rag/query_engine.py`: date-aware retrieval, extractive grounded answers, and citations
- `src/news_rag/app_support.py`: briefing and indexed-title sample-question preparation
- `src/news_rag/ui_styles.py`: shared Streamlit presentation styles
- `src/news_rag/ui_helpers.py`: Streamlit filter and citation presentation helpers
- `src/news_rag/evaluation.py`: evaluation dataset and score utilities
- `tests/`: automated tests
- `evaluation/questions.json`: 20-case evaluation dataset
- `docs/SystemRequirements.md`: original requirements
- `docs/PLAN.md`: phased implementation plan
- `docs/PROGRESS.md`: phase completion record
- `docs/COMPLIANCE_REPORT.md`: requirements compliance matrix
- `docs/FAQ.md`: project functionality and operational FAQ
