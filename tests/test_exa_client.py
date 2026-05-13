"""Tests for exa_client module — no network calls."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from war_room.exa_client import BudgetExhausted, ExaClient, ExaResponseError, _build_contents_options


def _mock_result(url="https://example.com", title="Test", text="body"):
    r = MagicMock()
    r.url = url
    r.title = title
    r.text = text
    r.published_date = "2024-01-01"
    r.score = 0.9
    r.summary = None
    r.highlights = None
    return r


def _mock_search_response(results):
    resp = MagicMock()
    resp.results = results
    return resp


@patch("war_room.exa_client.Exa")
def test_search_normalizes_results(MockExa):
    instance = MockExa.return_value
    instance.search.return_value = _mock_search_response([
        _mock_result("https://noaa.gov/report", "NOAA Report", "wind 120 mph"),
    ])

    client = ExaClient(api_key="test-key")
    results = client.search("test query")

    assert len(results) == 1
    assert results[0]["url"] == "https://noaa.gov/report"
    assert results[0]["title"] == "NOAA Report"
    assert "text" in results[0]
    assert "snippet" in results[0]


@patch("war_room.exa_client.Exa")
def test_budget_guard(MockExa):
    instance = MockExa.return_value
    instance.search.return_value = _mock_search_response([])

    client = ExaClient(api_key="test-key", max_search_calls=2)

    client.search("q1")
    client.search("q2")

    with pytest.raises(BudgetExhausted):
        client.search("q3")


@patch("war_room.exa_client.Exa")
def test_budget_remaining(MockExa):
    instance = MockExa.return_value
    instance.search.return_value = _mock_search_response([])

    client = ExaClient(api_key="test-key", max_search_calls=5)
    assert client.budget_remaining == 5

    client.search("q1")
    assert client.budget_remaining == 4


@patch("war_room.exa_client.Exa")
def test_retry_on_failure(MockExa):
    instance = MockExa.return_value
    # Fail twice, succeed on third
    instance.search.side_effect = [
        Exception("rate limit"),
        Exception("rate limit"),
        _mock_search_response([_mock_result()]),
    ]

    client = ExaClient(api_key="test-key")
    results = client.search("test")
    assert len(results) == 1
    assert instance.search.call_count == 3


@patch("war_room.exa_client.Exa")
def test_search_malformed_response_raises_normalized_error_and_counts_budget(MockExa):
    instance = MockExa.return_value
    instance.search.return_value = object()

    client = ExaClient(api_key="test-key")

    with pytest.raises(ExaResponseError, match="missing results"):
        client.search("test")

    assert client.search_count == 1
    assert client.budget_remaining == client.max_search_calls - 1


@patch("war_room.exa_client.Exa")
def test_include_domains_takes_priority_over_exclude(MockExa):
    instance = MockExa.return_value
    instance.search.return_value = _mock_search_response([])

    client = ExaClient(api_key="test-key")
    client.search(
        "query",
        include_domains=["weather.gov"],
        exclude_domains=["example.com"],
    )

    kwargs = instance.search.call_args.kwargs
    assert kwargs["include_domains"] == ["weather.gov"]
    assert "exclude_domains" not in kwargs


@patch("war_room.exa_client.Exa")
def test_contents_payload_respects_max_chars(MockExa):
    instance = MockExa.return_value
    instance.search.return_value = _mock_search_response([])

    client = ExaClient(api_key="test-key")
    client.search("query", max_chars=1234)

    contents = instance.search.call_args.kwargs["contents"]
    assert contents["text"]["max_characters"] == 1234


def test_build_contents_options_shape():
    payload = _build_contents_options(2048)
    assert payload["text"]["max_characters"] == 2048


@patch("war_room.exa_client.load_settings")
@patch("war_room.exa_client.discover_repo_root")
@patch("war_room.exa_client.Exa")
def test_exa_client_falls_back_to_shared_settings(MockExa, mock_discover_root, mock_load_settings):
    mock_discover_root.return_value = Path.cwd()
    mock_load_settings.return_value = MagicMock(exa_api_key_value="settings-key")

    client = ExaClient()

    MockExa.assert_called_once_with("settings-key")
    assert client.budget_remaining == client.max_search_calls
