# Improvement Plan — 2026-09-27

This is the consolidated improvement plan. It replaces the undated and 2026-09-26 improvement-plan documents. Status: `[x]` implemented, `[~]` in progress, `[ ]` pending.

## Phase 1 — Reliability and data freshness

- [x] Preserve ingestion completion across Streamlit reruns in the current session; require fresh-session ingestion even when indexed data already exists.
- [x] Use sentence-boundary trimming for long chat responses.
- [x] Remove the unused Run RAG pipeline UI and keep the interval scheduler for the worker.
- [x] Evict stale JSON vector records using configurable `NEWS_RAG_MAX_AGE_DAYS` (default 14).
- [x] Reject malformed publication dates instead of treating them as current.
- [x] Add RSS/article HTTP caching with ETag and Last-Modified validators.
- [x] Add retries and isolate feed failures; report failing feed names and URLs in the UI.
- [x] Add optional in-app scheduled ingestion through `NEWS_RAG_AUTO_INGEST_SECONDS`.

## Phase 2 — Ingestion and article quality

- [x] Support Technology, Finance, Politics, Stocks, and Sports category fetchers, with LiveMint defaults and Yahoo Finance for Finance.
- [x] Allow multiple configured RSS feeds per category; deduplicate and return up to the newest three articles per category.
- [x] Filter on category relevance and India relevance using article title and original RSS summary.
- [x] Hydrate article pages when available and fall back to the RSS item content when hydration fails or yields no text.
- [x] Preserve the original RSS summary in processed article metadata for summary answers.
- [x] Clean common navigation, ad, subscription, and session boilerplate; deduplicate by URL and content.
- [ ] Improve detection and rejection of pages that return boilerplate or too little meaningful article text.
- [ ] Validate feed category assignment against article headlines to reduce miscategorized indexed stories.
- [ ] Complete source licensing, robots-policy, and rate-limit review for configured publishers.
- [ ] Add a CI smoke test for configured LiveMint and Yahoo feed availability.

## Phase 3 — Retrieval and embeddings

- [x] Use sentence-transformers by default, with `HashEmbeddingProvider` fallback and a visible UI warning if the dependency is missing.
- [x] Allow local sentence-transformers model selection through `NEWS_RAG_EMBEDDING_MODEL`.
- [x] Use the configured provider with both JSON and Chroma vector-store backends.
- [x] Detect persisted indexes built with a different provider/model and require reset plus re-ingestion.
- [x] Combine lexical and vector similarity and apply relevance/recency reranking.
- [x] Interpret category/date constraints and focus matching topic/article evidence.
- [ ] Add user-visible retrieval diagnostics for selected category, date filter, scores, and article-level evidence selection.
- [ ] Benchmark retrieval quality on a representative, recorded news snapshot.

## Phase 4 — Answer quality and grounding

- [x] Keep the deterministic extractive generator as the default; use retrieved chunks and citations.
- [x] Return a no-answer response when relevant evidence is unavailable.
- [x] Use article headlines for daily digests, filter category headlines for headline-level topic evidence, and refuse requests for certainty about future outcomes.
- [x] Add ingestion-time retrieval, interpretation, and grounding verification probes.
- [x] Add regression coverage for article-level coherence on forward-looking stock-market questions.
- [ ] Add an optional LLM-based grounded answer generator that answers only from supplied chunks and cites supporting articles.
- [ ] Preserve the extractive generator as a fallback if an LLM provider is unavailable or fails.
- [ ] Add timeout, latency, and cost limits plus grounding/refusal checks for generated answers.
- [ ] Reduce special-case query heuristics only after equivalent behavior is covered by evaluation tests.

## Phase 5 — Evaluation and operations

- [x] Maintain a 20-question evaluation dataset and scoring utilities.
- [x] Report category retrieval coverage, ingestion freshness, feed failures, and verification results.
- [x] Provide JSON and optional Chroma storage backends and document reset/reindex requirements.
- [x] Add focused tests for the API health endpoint, worker, and Streamlit chat-context support.
- [ ] Run and record evaluation scores against a representative live-data snapshot.
- [ ] Add alerts for repeated feed failures and zero-article ingestion runs.
- [ ] Configure durable production storage, authenticated worker triggers, and external monitoring.

## Phase 6 — Documentation maintenance

- [x] Align README, architecture, FAQ, deployment, demo, progress, and compliance docs with current behavior.
- [x] Consolidate the improvement plans into this single dated document.
- [ ] Keep this plan updated as items are implemented; create a new dated copy only when a new snapshot is needed.
