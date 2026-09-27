# Improvement Plan — 2026-09-26

Status legend: `[x]` done, `[~]` in progress, `[ ]` pending.

## Phase 1 — Reliability quick wins (implemented 2026-09-26)

- [x] Persist ingestion state across app restarts: if the vector store already has chunks, mark `ingestion_completed` so users are not re-gated.
- [x] Replace hard 180-char mid-sentence truncation in chat answers with sentence-boundary trimming.
- [x] Remove dead UI code: `RAG_STAGES`, disabled `Run RAG pipeline` block, and associated session flags in [app.py](../app.py). (`IntervalScheduler` retained — used by [worker.py](../worker.py).)
- [x] Add TTL eviction to the JSON vector store (`NEWS_RAG_MAX_AGE_DAYS`, default 14) so stale chunks cannot accumulate forever.

## Phase 2 — Retrieval and content quality (implemented 2026-09-26)

- [x] Remove `stocks` from Finance relevance terms in [sources.py](../src/news_rag/sources.py) to stop Finance/Stocks cross-bleed.
- [x] Consolidate boilerplate/noise phrase lists into a shared `NOISE_PHRASES` constant used by both ingestion extraction and answer cleaning.
- [x] Make topic focusing order-independent: match chunks containing all significant query terms instead of consecutive-word phrases only.

## Phase 3 — Ops and observability (partially implemented)

- [x] HTTP caching for RSS/article fetches (ETag/Last-Modified) to cut repeated ingestion latency.
- [x] Per-feed failure details in the sidebar include feed name and URL; per-feed success status is not currently reported.
- [ ] Optional CI smoke test probing live feed URLs (LiveMint, Yahoo) for availability.

## Phase 4 — Semantic quality and docs (pending)

- [ ] Pluggable real embedding provider (e.g., sentence-transformers) behind `NEWS_RAG_EMBEDDING_PROVIDER`; hash embeddings remain the dev/test default.
- [x] Add focused test coverage for `api/`, `worker.py`, and Streamlit chat-context flow (repeated/follow-up questions).
- [x] Refresh README and FAQ for Sports category, LiveMint sourcing, and extractive summarization behavior.
