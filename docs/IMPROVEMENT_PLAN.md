# RAG Quality Improvement Plan

## Goal
Improve ingestion freshness, retrieval relevance, answer quality, and operational visibility without inventing unsupported news.

## Priorities

### Phase 1: Data Freshness and Recovery
- [x] Restrict Today's Briefing to articles from the current calendar day.
- [x] Add a reset-and-reingest control for stale local vector data.
- [x] Report per-category ingestion counts, rejected items, and feed errors.
- [x] Reject malformed publication dates instead of silently treating them as current.

### Phase 2: Retrieval Quality
- [ ] Replace or augment the 32-dimensional hash embedding fallback with a real embedding provider.
- [ ] Keep lexical and title-aware reranking as a fallback when the provider is unavailable.
- [ ] Add retrieval diagnostics showing selected category, date filter, and top scores.
- [x] Expand regression fixtures for cross-category and stale-data queries.

### Phase 3: Article Evidence
- [x] Hydrate article content from RSS item links when pages are accessible; fall back to RSS content when hydration fails or yields no text.
- [ ] Preserve source licensing, robots, timeout, retry, and provenance rules.
- [ ] Improve detection/rejection of pages that yield boilerplate or insufficient article text.

### Phase 4: Answer Quality
- [x] Keep broad queries explicitly cross-category.
- [ ] Add an optional citation-aware LLM summarization provider behind a configuration boundary.
- [x] Preserve the extractive generator as a deterministic fallback.
- [x] Refuse when retrieval has no relevant evidence; forecasts are limited to what retrieved articles report.

### Phase 5: Evaluation and Operations
- [ ] Add live-data evaluation runs with recorded retrieval and citation metrics.
- [x] Add ingestion freshness and per-category coverage checks.
- [ ] Add alerts for repeated feed failures and zero-article runs.
- [x] Document durable vector storage and reindex procedures.

## Current implementation

The locally verifiable data-quality and recovery improvements are implemented. Real semantic embeddings, LLM generation, live evaluation scoring, alert delivery, and durable production infrastructure remain pending provider and deployment choices.
