# Evaluation Scorecard

**Dataset:** `evaluation/questions.json`  
**Scoring scale:** 0.0 to 1.0 per dimension  
**Overall score:** arithmetic mean of accuracy, citation correctness, recency, and refusal quality

## Rubric

- **Accuracy:** 1.0 = answer fully supported and addresses the question; 0.5 = partially supported or incomplete; 0.0 = incorrect, invented, or unsupported.
- **Citation correctness:** 1.0 = every material claim has a valid source URL, source name, and publication date; 0.5 = citations exist but are incomplete; 0.0 = missing or invalid citations.
- **Recency:** 1.0 = requested date/category constraints are followed; 0.5 = mostly compliant; 0.0 = stale or out-of-range evidence is used.
- **Refusal quality:** 1.0 = unsupported questions are clearly refused without fabrication; 0.5 = cautious but ambiguous; 0.0 = fabricated or overconfident answer. For answerable cases, use 1.0 when the response remains grounded and 0.0 only when it fabricates.

## Results

Run the evaluation after ingestion against a fixed news snapshot. Record the evaluator name, snapshot date, and commit before entering scores.

| ID | Category | Accuracy | Citation | Recency | Refusal | Overall | Notes |
|---|---|---:|---:|---:|---:|---:|---|
| Q01 | finance |  |  |  |  |  |  |
| Q02 | finance |  |  |  |  |  |  |
| Q03 | finance |  |  |  |  |  |  |
| Q04 | technology |  |  |  |  |  |  |
| Q05 | technology |  |  |  |  |  |  |
| Q06 | technology |  |  |  |  |  |  |
| Q07 | politics |  |  |  |  |  |  |
| Q08 | politics |  |  |  |  |  |  |
| Q09 | politics |  |  |  |  |  |  |
| Q10 | cross-domain |  |  |  |  |  |  |
| Q11 | cross-domain |  |  |  |  |  |  |
| Q12 | cross-domain |  |  |  |  |  |  |
| Q13 | refusal |  |  |  |  |  |  |
| Q14 | refusal |  |  |  |  |  |  |
| Q15 | refusal |  |  |  |  |  |  |
| Q16 | citation |  |  |  |  |  |  |
| Q17 | citation |  |  |  |  |  |  |
| Q18 | recency |  |  |  |  |  |  |
| Q19 | recency |  |  |  |  |  |  |
| Q20 | recency |  |  |  |  |  |  |

## Summary

| Metric | Score |
|---|---:|
| Accuracy |  |
| Citation correctness |  |
| Recency |  |
| Refusal quality |  |
| Overall |  |

## Reproducibility

1. Run ingestion against approved sources and record the resulting vector-store snapshot date.
2. Run every question in `evaluation/questions.json` against that same snapshot.
3. Save the responses and citations before scoring.
4. Score each dimension using the rubric above.
5. Calculate dimension averages with `news_rag.evaluation.summarize_scores`.
6. Do not compare scorecards from different snapshots without recording their source set and dates.

Scores are intentionally blank until a representative news snapshot is available; blank values must not be reported as passing scores.
