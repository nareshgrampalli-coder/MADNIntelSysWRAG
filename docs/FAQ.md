# Frequently Asked Questions

## What does the project do?

News RAG Analyst collects India-focused Technology, Finance, Politics, Stocks Market, and Sports news, indexes dated source material, and answers questions with grounded citations.

## How do I start the application?

Install the project dependencies, then run:

```powershell
streamlit run app.py
```

The Streamlit application is the public-facing user interface.

## Does the app ingest data when it opens?

No. Ingestion runs only when you click **Run ingestion**. However, if the store already contains indexed chunks from a previous run, the app recognizes this and enables chat immediately without re-ingesting.

## What categories are supported?

The supported categories are:

- Technology
- Finance
- Politics
- Stocks Market
- Sports

## What must happen before I ask a question?

The application must have indexed data. Run ingestion first when the store is empty. The chat input remains disabled until indexed content is available.

## What does Run Ingestion do?

The **Run ingestion** button in the sidebar executes the full data pipeline for every category:

1. **Fetch RSS feeds** — downloads the configured feeds: LiveMint (`/rss/news`, `/rss/money`, `/rss/politics`, `/rss/markets`, `/rss/sports`) plus Yahoo Finance for the Finance category.
2. **Hydrate articles** — follows each article link from the feed and downloads the full article page, fetching up to 3 articles per feed and 3 per category concurrently.
3. **Clean content** — extracts the article body and removes navigation, scripts, advertisements, sponsored/promotional blocks, subscription prompts, social widgets, and login/session boilerplate.
4. **Filter for relevance** — applies category-specific keywords, then keeps only articles whose title or original RSS summary contains India, Indian cities or institutions, Indian market identifiers such as NSE, Nifty, or Sensex, or India-specific sports signals such as IPL or BCCI. Incidental India mentions in the hydrated article body alone do not qualify an article.
5. **Deduplicate** — drops repeated articles by URL and by content hash.
6. **Chunk and embed** — splits each article into bounded chunks of up to 400 words, generates embeddings, and stores each chunk with its source, category, title, URL, and publication-date metadata.
7. **Evict stale data** — the JSON store removes chunks older than 14 days on each run (`NEWS_RAG_MAX_AGE_DAYS` is configurable).

8. **Verify the indexed data** — runs category retrieval checks, query interpretation checks, and grounding checks. Supported sample queries must return citations; unsupported queries must refuse without citations.

When the run finishes, the sidebar reports article and chunk counts, per-category retrieval counts, total retrieved sources, category coverage percentage, interpretation results, grounding results, and total ingestion time. Individual feed failures include the feed name and URL. Chat is unlocked only after a successful ingestion, or automatically when the store already contains indexed data from a previous run.

Use **Reset indexed chunked data** first if you want a completely fresh index before re-ingesting.

## How does Run Ingestion compare to the full RAG pipeline?

A complete RAG pipeline has eight stages. **Run ingestion** performs stages 1–4 and runs lightweight verification probes for stages 5–8; full versions of stages 5–8 execute for each user question:

| # | RAG stage | Covered by Run Ingestion? | When does it run? |
|---|-----------|---------------------------|-------------------|
| 1 | Data Ingestion (fetch feeds and article pages) | Yes | On button click |
| 2 | Text Chunking (split into ≤400-word chunks) | Yes | On button click |
| 3 | Embedding Generation (vectorize each chunk) | Yes | On button click |
| 4 | Vector Database Storage (persist with metadata) | Yes | On button click |
| 5 | Query Processing (interpret category/date filters) | Verification probe | Per user question |
| 6 | Similarity Search (retrieve relevant chunks) | Verification probe | Per user question |
| 7 | Evidence Selection (pass retrieved chunks to the extractive generator) | Verification probe | Per user question |
| 8 | Response Generation (extract relevant sentences or refuse without evidence) | Grounding probe | Per user question |

## What does Run Ingestion verify?

After storage, the app verifies retrieval coverage for each category, category/date query interpretation, follow-up and repeated-question handling, and grounding behavior. It reports the results inline and warns when a category has no retrievable evidence or a grounding check fails.

The app also caches RSS and article responses in `data/http_cache` using `ETag` and `Last-Modified` validators. Failed feeds are shown individually with their names and URLs.

## How can I verify the missing stages today?

After Run Ingestion completes, ask a question in chat (for example, `Summarize todays news in 3 bullet points.`). The ingestion result already performs automated checks for stages 5–8; a grounded, cited answer provides an additional live confirmation with the freshly indexed data.

## Which questions can I ask?

You can ask category and date-aware questions such as:

- `Summarize todays news in 3 bullet points.`
- `Summarize in 3 bullet points for each category.`
- `What is stock news today?`
- `What happened in finance this week?`

Broad summaries return only the available indexed evidence and do not invent missing stories.

## How does the app handle stale news?

Today's Briefing shows only articles published on the current calendar day. If no current-day article is available for a category, that category is omitted rather than showing older indexed stories.

## Are answers generated from the open web at question time?

No. Answers are generated from indexed source material in the configured vector store. Run ingestion to refresh the indexed news.

## Does every answer include sources?

Grounded answers include source URLs, source names, and publication dates when citations are available. If no relevant evidence is found, the app returns a no-answer response instead of fabricating information.

## Where is data stored?

The default local backend is JSON. ChromaDB is optional and can be selected through the project configuration for deployments with durable storage.

## Can I use semantic embeddings?

Sentence-transformers is the default provider, using `sentence-transformers/all-MiniLM-L6-v2`, downloaded locally on first use. Install its dependency with `py -m pip install -e ".[embeddings]"`. If the package is missing, the app falls back to `HashEmbeddingProvider` and displays a warning. Set `NEWS_RAG_EMBEDDING_PROVIDER=hash` to explicitly use the fallback. Reset and re-ingest the index whenever the embedding provider or model changes.

## How can I run scheduled ingestion?

Run the worker with:

```powershell
py worker.py
```

Set `NEWS_RAG_INTERVAL_SECONDS` to configure the interval. The default schedule is daily.

For Streamlit-only deployments, set `NEWS_RAG_AUTO_INGEST_SECONDS` to a positive number of seconds. The app will then run ingestion automatically through a timed Streamlit fragment while the app session is active. Leave it empty to keep ingestion manual. The worker remains the better option for reliable always-on scheduling because it does not depend on an open browser session.

## Is the application production-ready?

The project includes ingestion, retrieval, evaluation fixtures, deployment scaffolding, and tests. Production use still requires durable storage, source licensing review, rate-limit monitoring, alerting, authenticated worker triggers, and measured live evaluation.

## How do I run the tests?

Run the full test suite with:

```powershell
py -m pytest
```
