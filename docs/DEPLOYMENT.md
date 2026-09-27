# Deployment

## Current deployment shape

The Streamlit application runs on Streamlit Community Cloud, which has a free tier and reads `app.py` as the application entrypoint. Vercel is configured separately for lightweight API endpoints and is not used to run Streamlit, ingestion workers, vector storage, or long-running scheduled jobs.

## Free Streamlit Community Cloud deployment

1. Push this repository to GitHub.
2. Open [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Create an app for this repository, branch `main`, and file `app.py`.
4. Add category RSS URL variables from `.env.example` under **Advanced settings > Secrets** only when custom sources are needed. Empty variables use LiveMint category feeds and Yahoo Finance for Finance; Sports is configurable with `NEWS_RAG_SPORTS_RSS_URLS` and `NEWS_RAG_SPORTS_APPROVED_RSS_URLS`.
5. Deploy and open the generated `streamlit.app` URL.

The `requirements.txt` file installs the package and Streamlit automatically. The local JSON vector store is suitable for a demo; Cloud restarts can discard local data, so production use requires persistent external storage.

## Vercel API scaffold

The repository includes:

- `vercel.json`: API function limits and CORS headers
- `api/health.py`: `GET /api/health` health endpoint
- `requirements.txt`: Vercel runtime dependency entry point
- `pyproject.toml`: explicit `api.health:handler` Vercel entrypoint so `app.py` is not selected

Deploy from the repository root:

```powershell
npx vercel
npx vercel --prod
```

After deployment, verify:

```powershell
Invoke-WebRequest https://<deployment>.vercel.app/api/health
```

Expected response:

```json
{"status":"ok","service":"news-rag-api","version":"0.1.0","environment":"production","vector_backend":"json"}
```

## Environment configuration

Configure these values in the Vercel project settings, not in committed files:

- `NEWS_RAG_ENV`
- `NEWS_RAG_LOG_LEVEL`
- `NEWS_RAG_VECTOR_STORE_DIR`
- `NEWS_RAG_VECTOR_BACKEND` (`json` for the free demo fallback, `chroma` for the optional persistent Chroma backend)
- `NEWS_RAG_INTERVAL_SECONDS` (`86400` for daily ingestion or `3600` for hourly ingestion)
- `NEWS_RAG_STRUCTURED_LOGS` (`1` for JSON worker logs)
- `NEWS_RAG_<CATEGORY>_RSS_URLS` for comma-separated feed overrides across Technology, Finance, Politics, Stocks, and Sports
- Matching `NEWS_RAG_<CATEGORY>_APPROVED_RSS_URLS` variables for operator-approved feeds; approved lists take precedence over regular overrides
- Legacy `news.google.com` URLs are ignored; remove them from existing Streamlit Secrets to use the verified publisher defaults
- `NEWS_RAG_EMBEDDING_PROVIDER=sentence-transformers` and optional `NEWS_RAG_EMBEDDING_MODEL` enable local semantic embeddings after installing the `embeddings` extra and downloading the model on first use
- Reset and re-ingest indexed data after changing embedding provider/model. LLM provider settings remain placeholders and are not used for answer generation.

## Production worker

Run the Streamlit UI and ingestion worker on a Python host such as Render, Railway, Fly.io, or a managed VM. Use a persistent vector database for production. Vercel Cron may call an authenticated, lightweight trigger endpoint, but it should not perform fetching, embedding, or vector writes directly.

## Security checklist

- Replace the permissive CORS value with the deployed frontend origin.
- Protect ingestion trigger endpoints with authentication.
- Keep API keys in platform secrets.
- Add request timeouts, structured logs, and error monitoring.
- Set `NEWS_RAG_STRUCTURED_LOGS=1` for JSON worker logs suitable for log aggregation.
- Confirm news-source licensing and storage terms.
