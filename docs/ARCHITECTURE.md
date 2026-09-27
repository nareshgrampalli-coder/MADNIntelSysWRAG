# System Architecture

```mermaid
flowchart TD
    S[Worker, optional in-app schedule, or manual trigger] --> F[Technology / Finance / Politics / Stocks / Sports fetchers]
    F --> P[Cleaning and enrichment]
    P --> C[Up to 400-word chunks with provenance]
    C --> E[Hash default or optional sentence-transformers]
    E --> V[(ChromaDB or local JSON vector store)]
    U[Streamlit chat] --> Q[Date/category query interpreter]
    Q --> V
    V --> R[Recency-aware retrieval]
    R --> A[Extractive grounded answer generator]
    A --> U
    R --> X[Source URL and publication date citations]
```

## Runtime boundaries

- Fetching, processing, embeddings, vector storage, and scheduled work belong in the Python service/worker.
- Streamlit Community Cloud hosts the demo UI; Vercel hosts the lightweight health API, while the worker and durable vector backend belong on a Python-compatible host.
- `NEWS_RAG_VECTOR_BACKEND=json` is the free/local fallback; production deployments should select Chroma with a durable mounted or external storage path.
- The default feeds are LiveMint category feeds plus Yahoo Finance for Finance; configured feeds are filtered for category and India relevance.
- Hash embeddings are the zero-dependency default; `NEWS_RAG_EMBEDDING_PROVIDER=sentence-transformers` opts into a local semantic model from the optional `embeddings` extra. No LLM generator is currently wired into the query path.
- Rebuild the index after changing the embedding provider or model; the vector store detects and rejects incompatible persisted vectors.
- The standalone worker supports configurable intervals through `NEWS_RAG_INTERVAL_SECONDS` and can emit structured JSON logs with `NEWS_RAG_STRUCTURED_LOGS=1`. Streamlit-only sessions can opt into timed ingestion with `NEWS_RAG_AUTO_INGEST_SECONDS`.
- Every chunk carries category, source, URL, publication date, title, tags, and entities.
- The query engine refuses when filtered retrieval returns no evidence and otherwise extracts relevant sentences from indexed chunks; it does not compose new prose with an LLM.

## Operational concerns

Source licensing, API rate limits, provider credentials, retry behavior, vector-store backups, external alerting, cost controls, and measured evaluation scores must be reviewed before production deployment.
