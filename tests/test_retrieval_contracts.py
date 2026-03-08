"""Tests for retrieval provider abstraction contracts."""

from __future__ import annotations

from war_room.models import QuerySpec, RetrievalTask
from war_room.retrieval import (
    RetrievalContentsRequest,
    RetrievalSearchRequest,
    execute_retrieval_search,
    fetch_retrieval_contents,
    query_spec_to_retrieval_task,
)


class _FakeProvider:
    provider_name = "exa"

    def __init__(self) -> None:
        self.search_calls: list[tuple[str, dict[str, object]]] = []
        self.content_calls: list[tuple[list[str], dict[str, object]]] = []

    def search(self, query: str, **kwargs: object) -> list[dict[str, object]]:
        self.search_calls.append((query, kwargs))
        return [{"title": "Result", "url": "https://example.com/result"}]

    def get_contents(self, urls: list[str], **kwargs: object) -> list[dict[str, object]]:
        self.content_calls.append((urls, kwargs))
        return [{"title": "Content", "url": urls[0] if urls else ""}]


def test_query_spec_to_retrieval_task_builds_canonical_task():
    query_spec = QuerySpec(
        module="weather",
        query="milton pinellas weather.gov",
        category="damage_report",
        preferred_domains=["weather.gov"],
    )

    task = query_spec_to_retrieval_task(
        query_spec,
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
    )

    assert task.retrieval_task_id == "run-milton:weather:damage_report"
    assert task.run_id == "run-milton"
    assert task.provider == "exa"
    assert task.query_text == "milton pinellas weather.gov"


def test_execute_retrieval_search_forwards_task_query_and_options():
    provider = _FakeProvider()
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
        query_text="milton pinellas weather.gov",
    )

    results = execute_retrieval_search(
        provider,
        RetrievalSearchRequest(
            task=task,
            k=7,
            recency_days=30,
            include_domains=["weather.gov"],
            exclude_domains=["example.com"],
            max_chars=4321,
        ),
    )

    assert results[0]["url"] == "https://example.com/result"
    query, kwargs = provider.search_calls[0]
    assert query == "milton pinellas weather.gov"
    assert kwargs["k"] == 7
    assert kwargs["recency_days"] == 30
    assert kwargs["include_domains"] == ["weather.gov"]
    assert kwargs["exclude_domains"] == ["example.com"]
    assert kwargs["max_chars"] == 4321


def test_execute_retrieval_search_rejects_provider_mismatch():
    provider = _FakeProvider()
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="fixture",
        query_text="milton pinellas weather.gov",
    )

    try:
        execute_retrieval_search(provider, RetrievalSearchRequest(task=task))
    except ValueError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("Expected provider mismatch to raise ValueError.")


def test_fetch_retrieval_contents_uses_provider_contract():
    provider = _FakeProvider()
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
        query_text="milton pinellas weather.gov",
    )

    results = fetch_retrieval_contents(
        provider,
        RetrievalContentsRequest(
            task=task,
            urls=["https://example.com/a", "https://example.com/b"],
            max_chars=9000,
        ),
    )

    assert results[0]["url"] == "https://example.com/a"
    urls, kwargs = provider.content_calls[0]
    assert urls == ["https://example.com/a", "https://example.com/b"]
    assert kwargs["max_chars"] == 9000
