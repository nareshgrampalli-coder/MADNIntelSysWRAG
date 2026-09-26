import json

from news_rag.evaluation import EvaluationScore, category_counts, load_cases, summarize_scores


def test_load_cases_and_count_categories(tmp_path) -> None:
    path = tmp_path / "questions.json"
    path.write_text(json.dumps([{"id": "Q1", "category": "finance", "question": "Q?", "expected_behavior": "Cite."}]))

    cases = load_cases(path)

    assert cases[0].case_id == "Q1"
    assert category_counts(cases) == {"finance": 1}


def test_summarize_scores_returns_dimension_and_overall_averages() -> None:
    scores = [EvaluationScore(1.0, 0.5, 1.0, 0.0), EvaluationScore(0.5, 1.0, 0.5, 1.0)]

    summary = summarize_scores(scores)

    assert summary["accuracy"] == 0.75
    assert summary["citation_correctness"] == 0.75
    assert summary["overall"] == 0.6875
