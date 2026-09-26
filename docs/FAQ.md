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
4. **Filter for relevance** — keeps only articles whose title or content matches category-specific keywords (for example, Stocks requires market terms such as NSE, Nifty, or Sensex).
5. **Deduplicate** — drops repeated articles by URL and by content hash.
6. **Chunk and embed** — splits each article into bounded chunks of up to 400 words, generates embeddings, and stores each chunk with its source, category, title, URL, and publication-date metadata.
7. **Evict stale data** — the JSON store removes chunks older than 14 days on each run (`NEWS_RAG_MAX_AGE_DAYS` is configurable).

When the run finishes, the sidebar reports how many articles and chunks were stored per category plus the total ingestion time in seconds. Chat is unlocked only after a successful ingestion, or automatically when the store already contains indexed data from a previous run.

Use **Reset indexed chunked data** first if you want a completely fresh index before re-ingesting.

## How does Run Ingestion compare to the full RAG pipeline?

A complete RAG pipeline has eight stages. **Run ingestion** covers the first four; the remaining four execute only when you ask a question:

| # | RAG stage | Covered by Run Ingestion? | When does it run? |
|---|-----------|---------------------------|-------------------|
| 1 | Data Ingestion (fetch feeds and article pages) | Yes | On button click |
| 2 | Text Chunking (split into ≤400-word chunks) | Yes | On button click |
| 3 | Embedding Generation (vectorize each chunk) | Yes | On button click |
| 4 | Vector Database Storage (persist with metadata) | Yes | On button click |
| 5 | Query Processing (interpret category/date filters) | No | Per user question |
| 6 | Similarity Search (retrieve relevant chunks) | No | Per user question |
| 7 | Prompt Augmentation (assemble grounded evidence) | No | Per user question |
| 8 | Response Generation (summarized, cited answer) | No | Per user question |

## What is missing from Run Ingestion?

Compared with a full end-to-end RAG run, Run Ingestion does **not**:

- **Verify retrieval quality** — it stores chunks but never runs a query, so a store with poor embeddings or wrong metadata still reports success.
- **Exercise query interpretation** — category mapping, date filtering, and the repeated/follow-up question handling are only tested when a user actually asks something.
- **Validate grounding** — it does not confirm that a sample question returns citations and a refusal when evidence is absent.
- **Report retrieval metrics** — the success message shows article/chunk counts per category and elapsed time, but not how many sources a query would retrieve.
- **Surface per-feed failures inline** — a failed feed is logged server-side; the sidebar shows only an aggregated error list.
- **Cache HTTP responses** — feeds and article pages are re-downloaded on every run; there is no ETag/Last-Modified caching yet.
- **Schedule itself** — recurring ingestion requires running [worker.py](../worker.py) separately.

## How can I verify the missing stages today?

After Run Ingestion completes, ask a question in chat (for example, `Summarize todays news in 3 bullet points.`). A grounded, cited answer confirms stages 5–8 work with the freshly indexed data. A visible "Run RAG pipeline" verification button that performs this check automatically is tracked in the [improvement plan](IMPROVEMENT_PLAN_2026-09-26.md) under Phase 3.

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

## How can I run scheduled ingestion?

Run the worker with:

```powershell
py worker.py
```

Set `NEWS_RAG_INTERVAL_SECONDS` to configure the interval. The default schedule is daily.

## Is the application production-ready?

The project includes ingestion, retrieval, evaluation fixtures, deployment scaffolding, and tests. Production use still requires durable storage, source licensing review, rate-limit monitoring, alerting, authenticated worker triggers, and measured live evaluation.

## How do I run the tests?

Run the full test suite with:

```powershell
py -m pytest
```
