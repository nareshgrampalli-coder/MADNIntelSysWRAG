# Demo Runbook

## Local setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev,ui]"
Copy-Item .env.example .env
py -m pytest
```

## Demo flow

1. Start the UI with `streamlit run app.py`.
2. Click **Run ingestion**. Defaults use LiveMint feeds for all five categories and Yahoo Finance for Finance. Configure category-specific approved RSS URLs before production use.
3. Ask a question about Technology, Finance, Politics, Stocks, or Sports news. Answers use extractive sentence selection from indexed article chunks; no LLM is currently configured.
4. Use the category and date filters to constrain retrieval.
5. Expand **Sources** to inspect links and publication dates.
6. Ask an unanswerable question and confirm the system responds that it has no matching news.

## Scheduled ingestion

Run the standalone worker for daily ingestion:

```powershell
py worker.py
```

Set `NEWS_RAG_INTERVAL_SECONDS=3600` for hourly ingestion. The worker performs an immediate run, repeats at the configured interval, and stops cleanly on `Ctrl+C` or a process termination signal.

## Evaluation

The 20-case evaluation set is in `evaluation/questions.json`. Use `evaluation/SCORECARD.md` to record one score from 0 to 1 for accuracy, citation correctness, recency, and refusal quality for each case, then summarize the results using `news_rag.evaluation.summarize_scores`.
