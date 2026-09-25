# News RAG Implementation Plan

## Goal

Build a news analyst that collects Technology, Finance, and Politics news, processes it into a dated knowledge base, and answers questions with grounded citations.

## Phases

### Phase 0: Foundation

- Create the Python project structure, dependency management, configuration, logging, and test scaffolding.
- Add `.env.example` and document local setup.
- Define typed contracts for articles, processed content, chunks, metadata, and query responses.

### Phase 1: News Ingestion

- Implement common RSS/API source adapters.
- Add separate Technology, Finance, and Politics fetchers.
- Normalize titles, article text, URLs, sources, and publication dates.
- Add timeouts, retries, duplicate detection, and failure logging.

### Phase 2: Article Processing

- Clean article text and remove boilerplate.
- Generate summaries, tags, and entities.
- Split content into approximately 300-500 token chunks.
- Preserve source and date provenance throughout the pipeline.

### Phase 3: Knowledge Base

- Generate embeddings and persist chunks in ChromaDB.
- Store category, source, URL, publication date, entities, and ingestion time as metadata.
- Support idempotent upserts, date/category filters, and database rebuilds.

### Phase 4: Orchestration

- Implement the pipeline: `fetch -> process -> embed -> store`.
- Support manual and scheduled runs with APScheduler.
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

- Deploy a browser-based frontend to Vercel.
- Host the Python API and ingestion worker separately on a Python-compatible platform.
- Configure preview and production environment variables.
- Use Vercel Cron only for lightweight authenticated trigger requests when appropriate.
- Keep fetching, processing, embeddings, vector storage, and long-running jobs outside Vercel serverless functions.
- Add CORS, protected ingestion endpoints, health checks, timeouts, and production logging.

## Recommended Initial Stack

- Python
- Streamlit for the first local UI
- ChromaDB for local vector storage
- APScheduler for scheduled ingestion
- RSS and approved public news APIs
- Configurable LLM and embedding providers
- Vercel for the production web frontend
- Separate Python hosting for the API and worker

## Validation

1. Run formatting, linting, type checks, and unit tests after each phase.
2. Test ingestion through storage with fixture articles.
3. Verify metadata filtering, idempotency, citations, and no-answer behavior.
4. Run the application locally with representative date and category questions.
5. Perform a Vercel deployment smoke test.
6. Run the evaluation set and confirm the final working tree is clean.

## Scope Boundaries

The first iteration excludes large-scale web crawling, guaranteed complete news coverage, multi-tenant authentication, advanced analytics, and high-availability infrastructure. Production readiness will additionally require source licensing, rate-limit handling, monitoring, cost controls, and stronger evaluation.
