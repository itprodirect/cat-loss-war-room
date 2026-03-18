"""Smoke contract tests for Exa adapter kwargs forwarding."""

import re
from unittest.mock import MagicMock, patch

from war_room.exa_client import ExaClient
from war_room.models import RetrievalTask
from war_room.retrieval import RetrievalSearchRequest, execute_retrieval_search


def _mock_result(url="https://example.com", title="Test", text="body"):
    result = MagicMock()
    result.url = url
    result.title = title
    result.text = text
    result.published_date = "2024-01-01"
    result.score = 0.9
    return result


def _mock_response(results):
    response = MagicMock()
    response.results = results
    return response


@patch("war_room.exa_client.Exa")
def test_search_contract_forwards_expected_kwargs(MockExa):
    instance = MockExa.return_value
    instance.search.return_value = _mock_response([_mock_result()])

    client = ExaClient(api_key="test-key")
    client.search(
        "hurricane report",
        k=7,
        recency_days=30,
        include_domains=["weather.gov", "noaa.gov"],
        max_chars=4321,
    )

    args, kwargs = instance.search.call_args
    assert args[0] == "hurricane report"
    assert kwargs["num_results"] == 7
    assert kwargs["include_domains"] == ["weather.gov", "noaa.gov"]
    assert "exclude_domains" not in kwargs
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", kwargs["start_published_date"])
    assert kwargs["contents"]["text"]["max_characters"] == 4321


@patch("war_room.exa_client.Exa")
def test_search_contract_uses_exclude_domains_when_include_is_empty(MockExa):
    instance = MockExa.return_value
    instance.search.return_value = _mock_response([_mock_result()])

    client = ExaClient(api_key="test-key")
    client.search(
        "coverage law",
        exclude_domains=["westlaw.com", "lexisnexis.com"],
    )

    _, kwargs = instance.search.call_args
    assert kwargs["exclude_domains"] == ["westlaw.com", "lexisnexis.com"]
    assert "include_domains" not in kwargs


@patch("war_room.exa_client.Exa")
def test_get_contents_contract_forwards_urls_and_max_chars(MockExa):
    instance = MockExa.return_value
    instance.get_contents.return_value = _mock_response([_mock_result(text="full body")])

    client = ExaClient(api_key="test-key")
    client.get_contents(
        ["https://example.com/a", "https://example.com/b"],
        max_chars=9000,
    )

    args, kwargs = instance.get_contents.call_args
    assert args[0] == ["https://example.com/a", "https://example.com/b"]
    assert kwargs["text"]["max_characters"] == 9000

@patch("war_room.exa_client.Exa")
def test_exa_client_executes_retrieval_task_search_contract(MockExa):
    instance = MockExa.return_value
    instance.search.return_value = _mock_response([_mock_result()])

    client = ExaClient(api_key="test-key")
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
        query_text="hurricane report",
    )

    execute_retrieval_search(
        client,
        RetrievalSearchRequest(
            task=task,
            k=7,
            include_domains=["weather.gov", "noaa.gov"],
            max_chars=4321,
        ),
    )

    args, kwargs = instance.search.call_args
    assert client.provider_name == "exa"
    assert args[0] == "hurricane report"
    assert kwargs["num_results"] == 7
    assert kwargs["include_domains"] == ["weather.gov", "noaa.gov"]
    assert kwargs["contents"]["text"]["max_characters"] == 4321

