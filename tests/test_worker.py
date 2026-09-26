import pytest

from worker import interval_seconds


def test_interval_seconds_defaults_to_daily(monkeypatch) -> None:
    monkeypatch.delenv("NEWS_RAG_INTERVAL_SECONDS", raising=False)

    assert interval_seconds() == 86400


def test_interval_seconds_accepts_hourly_schedule(monkeypatch) -> None:
    monkeypatch.setenv("NEWS_RAG_INTERVAL_SECONDS", "3600")

    assert interval_seconds() == 3600


@pytest.mark.parametrize("value", ["0", "-1", "invalid"])
def test_interval_seconds_rejects_invalid_values(monkeypatch, value) -> None:
    monkeypatch.setenv("NEWS_RAG_INTERVAL_SECONDS", value)

    with pytest.raises(ValueError, match="positive number"):
        interval_seconds()
