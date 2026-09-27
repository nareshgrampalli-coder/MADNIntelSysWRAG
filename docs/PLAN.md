# News RAG Implementation Plan

## Goal

Build a news analyst that collects India-relevant Technology, Finance, Politics, Stocks, and Sports news, processes it into a dated knowledge base, and answers questions with grounded citations.

## Phases

### Phase 0: Foundation

- Create the Python project structure, dependency management, configuration, logging, and test scaffolding.
- Add `.env.example` and document local setup.
- Define typed contracts for articles, processed content, chunks, metadata, and query responses.

### Phase 1: News Ingestion

- Implement common RSS/API source adapters.
- Add separate Technology, Finance, Politics, and India Stocks Market fetchers.
- Normalize titles, article text, URLs, sources, and publication dates.
- Add timeouts, retries, duplicate detection, and failure logging.

### Phase 2: Article Processing

- Clean article text and remove boilerplate.
- Generate summaries, tags, and entities.
- Split content into chunks of up to 400 words.
- Preserve source and date provenance throughout the pipeline.

### Phase 3: Knowledge Base

- Generate embeddings and persist chunks in the configured JSON or ChromaDB backend.
- Store category, source, URL, publication date, entities, and ingestion time as metadata.
- Support idempotent upserts, date/category filters, and database rebuilds.

### Phase 4: Orchestration

- Implement the pipeline: `fetch -> process -> embed -> store`.
- Support manual and scheduled runs with the built-in interval worker.
- Isolate agent failures, retry failed work, and record run summaries.

### Phase 5: RAG Query Engine

- Parse category and date constraints from user questions.
- Retrieve relevant chunks using vector search and metadata filtering.
- Apply recency-aware ranking.
- Generate answers only from retrieved evidence.
- Include source links and dates, with a clear no-answer response when evidence is insufficient.

### Phase 6: User Interface

- Build the chat experience with Streamlit for the initial MVP.
- Add chat history, category filters, date selection, citations, loading/error states, and manual ingestion.
- Optionally add a Today's Briefing panel.

### Phase 7: Evaluation and Documentation

- Create 20-30 test questions covering accuracy, citations, recency, filtering, and unanswerable questions.
- Record evaluation scores and known limitations.
- Add the README, architecture diagram, setup instructions, demo script, and secret-handling guidance.

### Phase 8: Vercel Deployment

- Host the Streamlit UI on Streamlit Community Cloud or another Python-compatible platform.
- Use Vercel for lightweight API functions and host the ingestion worker separately on a Python-compatible platform.
- Configure preview and production environment variables.
- Use Vercel Cron only for lightweight authenticated trigger requests when appropriate.
- Keep fetching, processing, embeddings, vector storage, and long-running jobs outside Vercel serverless functions.
- Add CORS, protected ingestion endpoints, health checks, timeouts, and production logging.

## Recommended Initial Stack

- Python
- Streamlit for the first local UI
- ChromaDB for local vector storage
- Built-in interval worker for scheduled ingestion
- RSS and approved public news APIs
- Configurable LLM and embedding providers
- Vercel for lightweight API functions
- Separate Python hosting for the API and worker

## RAG Pipeline Execution

The implemented pipeline covers ingestion through vector storage; each chat question runs query interpretation, retrieval/reranking, and extractive answer generation:

1. Data Ingestion: fetch category RSS sources with retries and relevance filtering.
2. Text Chunking: clean articles and split them into bounded provenance-preserving chunks.
3. Embedding Generation: use the configured embedding provider. Sentence-transformers is the default; deterministic local hash embeddings are the dependency-free fallback.
4. Vector Database Storage: persist chunks and metadata in JSON or ChromaDB.
5. Query Processing: interpret category and date constraints from the user question.
6. Similarity Search: retrieve and rerank relevant chunks using vector similarity, lexical overlap, and recency.
7. Evidence Selection: pass retrieved chunks directly to the extractive answer generator; there is no separate prompt-augmentation service.
8. Response Generation: return selected extractive sentences grounded in retrieved chunks, or a no-answer response when evidence is insufficient; no LLM is currently configured.

The Streamlit sidebar provides manual ingestion, optional timed ingestion through `NEWS_RAG_AUTO_INGEST_SECONDS`, and post-ingestion retrieval/interpretation/grounding verification. It does not expose a separate **Run RAG pipeline** action.

## Validation

1. Run formatting, linting, type checks, and unit tests after each phase.
2. Test ingestion through storage with fixture articles.
3. Verify metadata filtering, idempotency, citations, and no-answer behavior.
4. Run the application locally with representative date and category questions.
5. Perform a Vercel deployment smoke test.
6. Run the evaluation set and confirm the final working tree is clean.

## Scope Boundaries

The first iteration excludes large-scale web crawling, guaranteed complete news coverage, multi-tenant authentication, advanced analytics, and high-availability infrastructure. Production readiness will additionally require source licensing, rate-limit handling, monitoring, cost controls, and stronger evaluation.
