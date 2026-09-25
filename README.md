# News RAG

A date-aware news analyst for Technology, Finance, and Politics. The system will collect approved news sources, process and index articles, and answer questions with grounded citations.

## Status

Phase 0 (foundation) is complete. Ingestion, processing, retrieval, orchestration, UI, evaluation, and deployment are planned but not implemented yet. See [PLAN.md](PLAN.md) and [PROGRESS.md](PROGRESS.md).

## Local setup

Requires Python 3.11 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
To run the optional Streamlit UI:

```powershell
py -m pip install -e ".[ui]"
streamlit run app.py
```
py -m pip install -e ".[dev]"
Copy-Item .env.example .env
pytest
- `app.py`: Streamlit chat interface and manual ingestion controls
- `src/news_rag/orchestration.py`: manual pipeline runs and interval scheduling
- `src/news_rag/query_engine.py`: date-aware retrieval, grounded answers, and citations
- `tests/`: automated tests
- `SystemRequirements.md`: original requirements
- `PLAN.md`: phased implementation plan
- `PROGRESS.md`: phase completion record
