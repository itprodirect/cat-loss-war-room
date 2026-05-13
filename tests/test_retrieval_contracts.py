"""Tests for retrieval provider abstraction contracts."""

from __future__ import annotations

import datetime as dt

from war_room.models import CaseIntake, QuerySpec, RetrievalTask
from war_room.retrieval import (
    RetrievalContentsRequest,
    RetrievalContractError,
    RetrievalSearchRequest,
    execute_retrieval_search,
    execute_retrieval_task,
    fetch_retrieval_contents,
    notebook_run_id_from_intake,
    query_spec_to_retrieval_task,
)


_UNSET = object()


class _FakeProvider:
    provider_name = "exa"

    def __init__(
        self,
        *,
        results: object = _UNSET,
        content_results: object = _UNSET,
        error: Exception | None = None,
    ) -> None:
        self.search_calls: list[tuple[str, dict[str, object]]] = []
        self.content_calls: list[tuple[list[str], dict[str, object]]] = []
        self._results = (
            results
            if results is not _UNSET
            else [{"title": "Result", "url": "https://example.com/result"}]
        )
        self._content_results = content_results
        self._error = error

    def search(self, query: str, **kwargs: object) -> object:
        self.search_calls.append((query, kwargs))
        if self._error is not None:
            raise self._error
        if isinstance(self._results, list):
            return list(self._results)
        return self._results

    def get_contents(self, urls: list[str], **kwargs: object) -> object:
        self.content_calls.append((urls, kwargs))
        if self._content_results is not _UNSET:
            if isinstance(self._content_results, list):
                return list(self._content_results)
            return self._content_results
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


def test_execute_retrieval_search_normalizes_partial_provider_rows():
    provider = _FakeProvider(
        results=[
            {"url": "https://example.com/partial", "text": "Full provider text"},
            {"title": "Missing URL result"},
        ]
    )
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
        query_text="milton pinellas weather.gov",
    )

    results = execute_retrieval_search(provider, RetrievalSearchRequest(task=task))

    assert results[0] == {
        "url": "https://example.com/partial",
        "text": "Full provider text",
        "title": "",
        "published_date": "",
        "snippet": "Full provider text",
        "score": None,
    }
    assert results[1]["title"] == "Missing URL result"
    assert results[1]["url"] == ""
    assert results[1]["snippet"] == ""


def test_execute_retrieval_search_rejects_none_provider_response():
    provider = _FakeProvider(results=None)
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
        query_text="milton pinellas weather.gov",
    )

    try:
        execute_retrieval_search(provider, RetrievalSearchRequest(task=task))
    except RetrievalContractError as exc:
        assert "expected list[dict]" in str(exc)
    else:
        raise AssertionError("Expected None search response to raise RetrievalContractError.")


def test_execute_retrieval_task_records_completed_attempt_state():
    provider = _FakeProvider(results=[{"title": "Result", "url": "https://example.com/result"}])
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
        query_text="milton pinellas weather.gov",
    )

    started_at = dt.datetime(2026, 3, 8, 12, 0, tzinfo=dt.UTC)
    result = execute_retrieval_task(
        provider,
        RetrievalSearchRequest(task=task),
        now=started_at,
    )

    assert result.task.status == "completed"
    assert result.task.attempt_count == 1
    assert result.task.requested_at == started_at
    assert result.task.completed_at == started_at
    assert result.warning is None
    assert [event.event_type for event in result.run_events] == ["retrieval_started", "retrieval_completed"]
    assert all(event.created_at == started_at for event in result.run_events)


def test_execute_retrieval_task_records_degraded_state_for_empty_results():
    provider = _FakeProvider(results=[])
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
        query_text="milton pinellas weather.gov",
    )

    completed_at = dt.datetime(2026, 3, 8, 12, 30, tzinfo=dt.UTC)
    result = execute_retrieval_task(provider, RetrievalSearchRequest(task=task), now=completed_at)

    assert result.task.status == "degraded"
    assert result.task.review_required is True
    assert result.task.completed_at == completed_at
    assert result.warning is not None
    assert result.run_events[-1].event_type == "retrieval_empty"
    assert all(event.created_at == completed_at for event in result.run_events)


def test_execute_retrieval_task_records_degraded_state_for_partial_results():
    provider = _FakeProvider(
        results=[
            {"title": "Useful Result", "url": "https://example.com/result"},
            object(),
            {"title": "No URL"},
        ]
    )
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
        query_text="milton pinellas weather.gov",
    )

    completed_at = dt.datetime(2026, 3, 8, 12, 35, tzinfo=dt.UTC)
    result = execute_retrieval_task(provider, RetrievalSearchRequest(task=task), now=completed_at)

    assert result.task.status == "degraded"
    assert result.task.review_required is True
    assert result.task.raw_artifact_refs == ["https://example.com/result"]
    assert result.warning is not None
    assert "dropped_malformed=1" in result.warning
    assert "missing_url=1" in result.warning
    assert result.run_events[-1].event_type == "retrieval_degraded"
    assert result.run_events[-1].artifact_refs == ["https://example.com/result"]


def test_execute_retrieval_task_reports_all_malformed_rows_as_degraded():
    provider = _FakeProvider(results=[object()])
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
        query_text="milton pinellas weather.gov",
    )

    completed_at = dt.datetime(2026, 3, 8, 12, 40, tzinfo=dt.UTC)
    result = execute_retrieval_task(provider, RetrievalSearchRequest(task=task), now=completed_at)

    assert result.task.status == "degraded"
    assert result.hits == []
    assert result.warning is not None
    assert "dropped_malformed=1" in result.warning
    assert result.run_events[-1].event_type == "retrieval_degraded"


def test_execute_retrieval_task_records_failed_state_for_provider_error():
    provider = _FakeProvider(error=RuntimeError("boom"))
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
        query_text="milton pinellas weather.gov",
    )

    completed_at = dt.datetime(2026, 3, 8, 12, 45, tzinfo=dt.UTC)
    result = execute_retrieval_task(provider, RetrievalSearchRequest(task=task), now=completed_at)

    assert result.task.status == "failed"
    assert result.task.review_required is True
    assert result.task.completed_at == completed_at
    assert "RuntimeError" in (result.warning or "")
    assert result.run_events[-1].event_type == "retrieval_failed"
    assert all(event.created_at == completed_at for event in result.run_events)


def test_execute_retrieval_task_normalizes_timeout_failure_metadata():
    provider = _FakeProvider(error=TimeoutError("request timed out"))
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
        query_text="milton pinellas weather.gov",
    )

    completed_at = dt.datetime(2026, 3, 8, 12, 50, tzinfo=dt.UTC)
    result = execute_retrieval_task(provider, RetrievalSearchRequest(task=task), now=completed_at)

    assert result.task.status == "failed"
    assert result.warning is not None
    assert "error_kind=timeout" in result.warning
    assert "exception=TimeoutError" in result.warning
    assert "retryable=true" in result.warning
    assert "attempts=1" in result.warning
    assert result.run_events[-1].message == result.warning


def test_execute_retrieval_task_rejects_malformed_provider_response():
    provider = _FakeProvider(results={"results": []})
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
        query_text="milton pinellas weather.gov",
    )

    completed_at = dt.datetime(2026, 3, 8, 13, 0, tzinfo=dt.UTC)
    result = execute_retrieval_task(provider, RetrievalSearchRequest(task=task), now=completed_at)

    assert result.task.status == "failed"
    assert result.warning is not None
    assert "error_kind=malformed_response" in result.warning
    assert "exception=RetrievalContractError" in result.warning
    assert "retryable=false" in result.warning
    assert result.run_events[-1].event_type == "retrieval_failed"


def test_execute_retrieval_task_rejects_none_provider_response_as_malformed_failure():
    provider = _FakeProvider(results=None)
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
        query_text="milton pinellas weather.gov",
    )

    completed_at = dt.datetime(2026, 3, 8, 13, 5, tzinfo=dt.UTC)
    result = execute_retrieval_task(provider, RetrievalSearchRequest(task=task), now=completed_at)

    assert result.task.status == "failed"
    assert result.task.review_required is True
    assert result.task.completed_at == completed_at
    assert result.warning is not None
    assert "error_kind=malformed_response" in result.warning
    assert "exception=RetrievalContractError" in result.warning
    assert "retryable=false" in result.warning
    assert "attempts=1" in result.warning
    assert result.run_events[-1].event_type == "retrieval_failed"
    assert result.run_events[-1].message == result.warning


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


def test_fetch_retrieval_contents_normalizes_rows_and_rejects_malformed_response():
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
        RetrievalContentsRequest(task=task, urls=["https://example.com/a"]),
    )

    assert results[0]["title"] == "Content"
    assert results[0]["text"] == ""
    assert results[0]["snippet"] == ""

    provider._results = {"results": []}
    provider.get_contents = lambda urls, **kwargs: provider._results
    try:
        fetch_retrieval_contents(
            provider,
            RetrievalContentsRequest(task=task, urls=["https://example.com/a"]),
        )
    except RetrievalContractError as exc:
        assert "expected list[dict]" in str(exc)
    else:
        raise AssertionError("Expected malformed content response to raise RetrievalContractError.")


def test_fetch_retrieval_contents_rejects_none_provider_response():
    provider = _FakeProvider(content_results=None)
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
        query_text="milton pinellas weather.gov",
    )

    try:
        fetch_retrieval_contents(
            provider,
            RetrievalContentsRequest(task=task, urls=["https://example.com/a"]),
        )
    except RetrievalContractError as exc:
        assert "expected list[dict]" in str(exc)
    else:
        raise AssertionError("Expected None content response to raise RetrievalContractError.")


def test_notebook_run_id_from_intake_is_deterministic():
    intake = CaseIntake(
        event_name="Hurricane Milton",
        event_date="2024-10-09",
        state="FL",
        county="Pinellas",
        carrier="Citizens Property Insurance",
        policy_type="HO-3 Dwelling",
    )

    run_id = notebook_run_id_from_intake(intake)

    assert run_id == "run-notebook-hurricane-milton-fl-pinellas-citizens-property-insurance"
