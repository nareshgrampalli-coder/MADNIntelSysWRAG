"""Evaluation dataset loading and report generation."""

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    category: str
    question: str
    expected_behavior: str


@dataclass(frozen=True)
class EvaluationScore:
    accuracy: float
    citation_correctness: float
    recency: float
    refusal_quality: float

    @property
    def overall(self) -> float:
        return (self.accuracy + self.citation_correctness + self.recency + self.refusal_quality) / 4


def load_cases(path: Path) -> list[EvaluationCase]:
    records = json.loads(path.read_text(encoding="utf-8"))
    return [
        EvaluationCase(
            case_id=record["id"],
            category=record["category"],
            question=record["question"],
            expected_behavior=record["expected_behavior"],
        )
        for record in records
    ]


def summarize_scores(scores: list[EvaluationScore]) -> dict[str, float]:
    if not scores:
        return {"accuracy": 0.0, "citation_correctness": 0.0, "recency": 0.0, "refusal_quality": 0.0, "overall": 0.0}
    return {
        "accuracy": sum(score.accuracy for score in scores) / len(scores),
        "citation_correctness": sum(score.citation_correctness for score in scores) / len(scores),
        "recency": sum(score.recency for score in scores) / len(scores),
        "refusal_quality": sum(score.refusal_quality for score in scores) / len(scores),
        "overall": sum(score.overall for score in scores) / len(scores),
    }


def category_counts(cases: list[EvaluationCase]) -> dict[str, int]:
    return dict(Counter(case.category for case in cases))
