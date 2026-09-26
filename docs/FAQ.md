# Frequently Asked Questions

## What does the project do?

News RAG Analyst collects India-focused Technology, Finance, Politics, and Stocks Market news, indexes dated source material, and answers questions with grounded citations.

## How do I start the application?

Install the project dependencies, then run:

```powershell
streamlit run app.py
```

The Streamlit application is the public-facing user interface.

## Does the app ingest data when it opens?

Yes. Today's Briefing is enabled by default. On the initial page load, the app runs the daily ingestion flow and displays available briefing articles.

## What categories are supported?

The supported categories are:

- Technology
- Finance
- Politics
- India Stocks Market

## What must happen before I ask a question?

The application must have indexed data. Run ingestion first when the store is empty. The chat input remains disabled until indexed content is available.

## What does Run Ingestion do?

It fetches configured RSS sources, cleans and enriches articles, creates bounded chunks, generates embeddings, and stores chunks with source, category, title, URL, and publication-date metadata.

## What does Run RAG Pipeline do?

It runs ingestion through vector storage and then executes a real sample query through query interpretation, similarity search, evidence assembly, and grounded response generation. The status panel reports actual article, chunk, and retrieved-source counts.

## Which questions can I ask?

You can ask category and date-aware questions such as:

- `Summarize todays news in 3 bullet points.`
- `Summarize in 3 bullet points for each category.`
- `What is stock news today?`
- `What happened in finance this week?`

Broad summaries return only the available indexed evidence and do not invent missing stories.

## How does the app handle stale news?

Today's Briefing prefers articles from the current day. If no current-day article is available for a category, it may use the previous calendar day's verified articles. Older indexed stories are not presented as today's news.

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
