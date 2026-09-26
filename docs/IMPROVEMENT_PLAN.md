# RAG Quality Improvement Plan

## Goal
Improve ingestion freshness, retrieval relevance, answer quality, and operational visibility without inventing unsupported news.

## Priorities

### Phase 1: Data Freshness and Recovery
- [x] Prevent Today's Briefing from using older-than-previous-day articles.
- [ ] Add a reset-and-reingest control for stale local vector data.
- [ ] Report per-category ingestion counts, rejected items, and feed errors.
- [ ] Reject malformed and future publication dates instead of silently treating them as current.

### Phase 2: Retrieval Quality
- [ ] Replace the 32-dimensional hash embedding fallback with a real embedding provider.
- [ ] Keep lexical and title-aware reranking as a fallback when the provider is unavailable.
- [ ] Add retrieval diagnostics showing selected category, date filter, and top scores.
- [ ] Expand regression fixtures for cross-category and stale-data queries.

### Phase 3: Article Evidence
- [ ] Fetch full article content where permitted instead of relying only on RSS snippets.
- [ ] Preserve source licensing, robots, timeout, retry, and provenance rules.
- [ ] Reject pages that do not produce meaningful article text.

### Phase 4: Answer Quality
- [ ] Keep broad queries explicitly cross-category.
- [ ] Add a citation-aware summarization provider behind a configuration boundary.
- [ ] Preserve the extractive generator as a deterministic fallback.
- [ ] Refuse unsupported forecasts, private-source requests, and evidence-free claims.

### Phase 5: Evaluation and Operations
- [ ] Add live-data evaluation runs with recorded retrieval and citation metrics.
- [ ] Add ingestion freshness and per-category coverage checks.
- [ ] Add alerts for repeated feed failures and zero-article runs.
- [ ] Document durable vector storage and reindex procedures.

## Current implementation

The first implementation step is the reset-and-reingest control in the Streamlit sidebar. It is intended for stale local JSON data and does not fabricate or delete source content outside the configured vector store.
