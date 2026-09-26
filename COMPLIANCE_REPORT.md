# Requirements Compliance Report

**Project:** News RAG Analyst  
**Reviewed:** 2026-09-26  
**Source requirements:** [SystemRequirements.md](SystemRequirements.md)

## Overall Status

**MVP compliance: Substantially compliant.** The repository contains a working Streamlit application, RSS ingestion pipeline, processing and chunking, local vector retrieval, grounded answers with citations, evaluation fixtures, documentation, and deployed application/API surfaces.

**Production compliance: Partial.** Persistent hosted storage, measured evaluation scores, authenticated ingestion endpoints, and a separately hosted worker remain operational hardening tasks.

## Requirement Matrix

| Requirement | Status | Evidence / Gap |
|---|---|---|
| Technology, Finance, and Politics fetcher agents | Complete | `src/news_rag/ingestion.py` defines separate domain fetchers; `src/news_rag/sources.py` provides default feeds and environment overrides. |
| Collect headline, body, URL, publication date, and source | Complete | RSS normalization produces typed `RawArticle` records with these fields. |
| Source relevance rules and approved official sources | Partial | Domain boundaries and configurable feeds exist, but default feeds are Google News searches and official-source coverage is not guaranteed. |
| Scheduled orchestration | Partial | Manual runs and a lightweight interval scheduler exist in `src/news_rag/orchestration.py`; durable production scheduling is not deployed. |
| Failure handling, retries, and run logging | Complete for MVP | RSS retries, fetcher isolation, run reports, timestamps, and errors are implemented and tested. |
| Deduplication and boilerplate cleaning | Complete | URL/content-hash deduplication and deterministic HTML/boilerplate cleaning are implemented and tested. |
| Summaries, tags, entities, and category metadata | Complete for MVP | Processing derives extractive summaries, tags, entities, and category metadata. |
| 300-500 token/article chunks | Complete for MVP | Bounded word-based chunking is implemented with provenance preservation. |
| Embeddings and vector database | Partial | Deterministic hash embeddings and persistent JSON storage are available by default; ChromaDB is optional and not runtime-tested in this environment. |
| Rich metadata filtering | Complete | Category, publication date, source, URL, entities, and ingestion metadata are stored or preserved for retrieval. |
| Query interpretation | Complete for MVP | Category, relative date ranges, and explicit dates are supported. |
| Hybrid search and reranking | Complete for MVP | JSON retrieval combines semantic similarity with lexical term overlap, then the query engine reranks candidates by relevance and bounded recency. A production-scale reranker remains optional. |
| Grounded answer generation | Complete for MVP | Extractive answers use retrieved evidence and refuse when no evidence matches. A hosted LLM adapter is not configured. |
| Citations with links and dates | Complete | Query responses expose source citations and the Streamlit UI renders links and publication dates. |
| Streamlit chat interface | Complete | `app.py` provides chat, filters, date selection, loading/error states, ingestion, and Today's Briefing. |
| 20-30 evaluation questions and scoring | Complete for MVP | Twenty evaluation cases, scoring utilities, and a reviewer-ready scorecard with rubric and reproducibility instructions are present. Measured scores remain blank until a representative news snapshot is captured. |
| README and setup documentation | Complete | README, deployment guide, demo runbook, architecture diagram, and progress record are present. |
| Working deployed app or local demo | Complete | Streamlit Community Cloud deployment is configured for `app.py`; Vercel separately hosts the health API. |
| Production persistence and monitoring | Not complete | Streamlit Cloud local storage is ephemeral; external persistent vector storage, structured production logs, monitoring, and authenticated worker triggers remain required. |

## Dependency Compliance

### Streamlit Community Cloud

`requirements.txt` contains:

```text
-e .
streamlit>=1.40
```

This installs the local package and the Streamlit UI dependency. The requirements resolve successfully in the development environment.

### Development and optional dependencies

`pyproject.toml` provides:

- `dev`: pytest
- `vector`: optional ChromaDB adapter dependency
- `ui`: optional Streamlit dependency for local installation

The Vercel API uses the standard library and does not require the vector or UI extras.

## Validation Evidence

- Full automated test suite: **27 passed**.
- Requirements dependency dry run: **successful**.
- Vercel preview deployment: **successful** after configuring `api.health:handler`.
- Vercel production health API: deployed under the `news-rag` project.
- Streamlit application: deployed/configured through Streamlit Community Cloud.

## Recommended Completion Items

1. Run the 20 evaluation questions against a populated, representative news index and record accuracy, citation, recency, and refusal scores.
2. Move production vectors to ChromaDB, Qdrant, Pinecone, or pgvector with persistent storage.
3. Add authenticated ingestion and query API endpoints on a Python-compatible host.
4. Add durable scheduling, structured logs, monitoring, and source licensing review.
5. Add hybrid retrieval and a production LLM/embedding provider only after evaluation establishes the baseline.

## Conclusion

The project satisfies the requested MVP architecture and deliverables. The remaining gaps are production-readiness items rather than missing core functionality, and they are explicitly documented above.
