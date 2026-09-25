# News RAG

A date-aware news analyst for Technology, Finance, and Politics. The system will collect approved news sources, process and index articles, and answer questions with grounded citations.

## Status

Phase 0 (foundation) is complete. Ingestion, processing, retrieval, orchestration, UI, evaluation, and deployment are planned but not implemented yet. See [PLAN.md](PLAN.md) and [PROGRESS.md](PROGRESS.md).

## Local setup

Requires Python 3.11 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev]"
Copy-Item .env.example .env
pytest
```

The project currently uses only the Python standard library at runtime. Provider and ingestion dependencies will be added in the phases that need them.

## Repository structure

- `src/news_rag/models.py`: shared domain contracts
- `src/news_rag/config.py`: environment-backed settings
- `src/news_rag/logging_config.py`: application logging setup
- `src/news_rag/processing.py`: deterministic cleaning, enrichment, and chunking
- `src/news_rag/vector_store.py`: embeddings and persistent vector-store adapters
- `src/news_rag/orchestration.py`: manual pipeline runs and interval scheduling
- `src/news_rag/query_engine.py`: date-aware retrieval, grounded answers, and citations
- `tests/`: automated tests
- `SystemRequirements.md`: original requirements
- `PLAN.md`: phased implementation plan
- `PROGRESS.md`: phase completion record
