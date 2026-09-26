# Deployment

## Current deployment shape

The Streamlit application is a Python process and should run on a Python-compatible host. Vercel is configured for lightweight API endpoints and is not used to run Streamlit, ingestion workers, vector storage, or long-running scheduled jobs.

## Vercel API scaffold

The repository includes:

- `vercel.json`: API function limits and CORS headers
- `api/health.py`: `GET /api/health` health endpoint
- `requirements.txt`: Vercel runtime dependency entry point

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
{"status":"ok","service":"news-rag-api"}
```

## Environment configuration

Configure these values in the Vercel project settings, not in committed files:

- `NEWS_RAG_ENV`
- `NEWS_RAG_LOG_LEVEL`
- `NEWS_RAG_VECTOR_STORE_DIR`
- Approved RSS URL variables for each domain
- Provider credentials when an external LLM or embedding provider is enabled

## Production worker

Run the Streamlit UI and ingestion worker on a Python host such as Render, Railway, Fly.io, or a managed VM. Use a persistent vector database for production. Vercel Cron may call an authenticated, lightweight trigger endpoint, but it should not perform fetching, embedding, or vector writes directly.

## Security checklist

- Replace the permissive CORS value with the deployed frontend origin.
- Protect ingestion trigger endpoints with authentication.
- Keep API keys in platform secrets.
- Add request timeouts, structured logs, and error monitoring.
- Confirm news-source licensing and storage terms.
