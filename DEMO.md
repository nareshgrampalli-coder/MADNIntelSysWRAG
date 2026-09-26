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
2. Click **Run ingestion**. The default source list is intentionally empty until approved RSS/API URLs are configured.
3. Ask a question about Technology, Finance, or Politics news.
4. Use the category and date filters to constrain retrieval.
5. Expand **Sources** to inspect links and publication dates.
6. Ask an unanswerable question and confirm the system responds that it has no matching news.

## Evaluation

The 20-case evaluation set is in `evaluation/questions.json`. Use `evaluation/SCORECARD.md` to record one score from 0 to 1 for accuracy, citation correctness, recency, and refusal quality for each case, then summarize the results using `news_rag.evaluation.summarize_scores`.
