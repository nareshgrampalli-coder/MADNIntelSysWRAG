# Improvement Plan — 2026-09-27

Status legend: `[x]` done, `[~]` in progress, `[ ]` pending.

Carried over from [IMPROVEMENT_PLAN_2026-09-26.md](IMPROVEMENT_PLAN_2026-09-26.md): Phases 1–2 are complete. This plan updates Phase 3 status and adds Phase 5 for LLM-based retrieval/generation.

## Phase 3 — Ops and observability (implemented 2026-09-26/27)

- [x] HTTP caching for RSS/article fetches (ETag/Last-Modified) — implemented in `RssSourceAdapter` with `data/http_cache`.
- [x] Per-feed success/failure status in the sidebar — `DomainFetcher.errors` reported inline per feed name/URL.
- [x] Post-ingestion verification probes for retrieval, query interpretation, and grounding — implemented in `app_support.py`.
- [x] Optional in-app scheduled ingestion (`NEWS_RAG_AUTO_INGEST_SECONDS`).
- [ ] Optional CI smoke test probing live feed URLs (LiveMint, Yahoo) for availability.

## Phase 4 — Semantic quality and docs (partially pending)

- [ ] Pluggable real embedding provider (e.g., sentence-transformers) behind `NEWS_RAG_EMBEDDING_PROVIDER`; hash embeddings remain the dev/test default.
- [ ] Test coverage for `api/`, `worker.py`, and the Streamlit chat-context flow (repeated/follow-up questions).
- [x] Refresh README and FAQ for Sports category, LiveMint sourcing, and summarization behavior.

## Phase 5 — LLM-assisted retrieval and generation (pending)

Motivation: `HashEmbeddingProvider` is a lexical bag-of-hashed-tokens with no semantic understanding, and `ExtractiveAnswerGenerator` relies on a growing set of regex-based heuristics (single-article focus, exact multi-word topic focus, forward-looking "tomorrow/prediction" focus) to keep answers coherent. Both are hitting their design ceiling.

- [ ] Add a real sentence-embedding provider (local `sentence-transformers` model or an API embedding endpoint) behind the existing `NEWS_RAG_EMBEDDING_PROVIDER` interface, keeping hash embeddings as the no-dependency dev/test fallback.
- [ ] Add an optional LLM-based grounded answer generator (strict "answer only from provided chunks, cite sources, refuse otherwise" prompt) as an alternative to `ExtractiveAnswerGenerator`, reusing existing grounding/refusal verification in `app_support.py`.
- [ ] Consolidate the accumulated topic-focus heuristics in `query_engine.py` once an LLM-based interpreter/generator is available, instead of adding further special cases.
- [ ] Add cost/latency guardrails (timeouts, fallback to extractive generator on LLM failure) so the app remains usable without external API access.

## Phase 6 — Test and doc maintenance (pending)

- [ ] Keep this improvement plan file in sync after each implemented phase; retire prior dated plans once fully superseded.
- [ ] Add regression tests for `api/` and `worker.py` before introducing an LLM-backed generator, to protect existing behavior during the migration.
