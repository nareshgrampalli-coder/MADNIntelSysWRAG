# System Architecture

```mermaid
flowchart TD
    S[Scheduler or manual trigger] --> F[Technology / Finance / Politics fetchers]
    F --> P[Cleaning and enrichment]
    P --> C[300-500 word chunks with provenance]
    C --> E[Embedding provider]
    E --> V[(ChromaDB or local JSON vector store)]
    U[Streamlit chat] --> Q[Date/category query interpreter]
    Q --> V
    V --> R[Recency-aware retrieval]
    R --> A[Grounded answer generator]
    A --> U
    R --> X[Source URL and publication date citations]
```

## Runtime boundaries

- Fetching, processing, embeddings, vector storage, and scheduled work belong in the Python service/worker.
- The initial Streamlit app is a local/demo UI. The planned production frontend can run on Vercel and call a separately hosted Python API.
- Every chunk carries category, source, URL, publication date, title, tags, and entities.
- The query engine refuses when filtered retrieval returns no evidence.

## Operational concerns

Source licensing, API rate limits, provider credentials, retry behavior, vector-store backups, logs, cost controls, and evaluation scores must be reviewed before production deployment.
