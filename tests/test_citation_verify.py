"""Tests for citation_verify module - no network calls."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from war_room.citation_verify import MAX_CHECKS, _do_check, spot_check_citations
from war_room.exa_client import BudgetExhausted


def _mock_client_with_hits(hits_list):
    """Create a mock ExaClient that returns given hits."""
    client = MagicMock()
    client.search.return_value = hits_list
    return client


def test_skips_blank_citations():
    """Cases with blank citations should not be checked."""
    pack = {
        "issues": [
            {
                "issue": "Coverage",
                "cases": [
                    {"name": "Smith v. Jones", "citation": ""},
                    {"name": "Doe v. Ins Co", "citation": "   "},
                    {"name": "Real v. Case", "citation": "123 So. 3d 456"},
                ],
            }
        ],
    }
    client = _mock_client_with_hits([
        {"url": "https://scholar.google.com/case", "title": "Result"},
    ])

    with tempfile.TemporaryDirectory() as tmpdir:
        result = spot_check_citations(
            pack,
            client,
            use_cache=False,
            cache_dir=tmpdir,
            cache_samples_dir=tmpdir,
        )

    assert result["summary"]["total"] == 1
    assert len(result["checks"]) == 1
    assert result["checks"][0]["case_name"] == "Real v. Case"


def test_max_checks_cap():
    """Should check at most MAX_CHECKS citations."""
    cases = [
        {"name": f"Case {i} v. Defendant", "citation": f"{100+i} So. 3d {200+i}"}
        for i in range(20)
    ]
    pack = {"issues": [{"issue": "Test", "cases": cases}]}
    client = _mock_client_with_hits([
        {"url": "https://example.com", "title": "Hit"},
    ])

    with tempfile.TemporaryDirectory() as tmpdir:
        result = spot_check_citations(
            pack,
            client,
            use_cache=False,
            cache_dir=tmpdir,
            cache_samples_dir=tmpdir,
        )

    assert result["summary"]["total"] <= MAX_CHECKS


def test_prefers_official_source_among_hits():
    """When multiple hits exist, pick the best-tier one."""
    client = _mock_client_with_hits(
        [
            {"url": "https://random-blog.com/article", "title": "Blog"},
            {"url": "https://www.flcourts.gov/case/123", "title": "FL Courts"},
            {"url": "https://insurancejournal.com/article", "title": "Journal"},
        ]
    )

    result = _do_check("Smith v. Jones 123 So. 3d 456", client)
    assert result["status"] == "verified"
    assert "flcourts.gov" in result["source_url"]


def test_professional_source_is_uncertain():
    """Professional-only hits -> uncertain."""
    client = _mock_client_with_hits(
        [{"url": "https://insurancejournal.com/article", "title": "Article"}]
    )

    result = _do_check("Doe v. Carrier 456 F.3d 789", client)
    assert result["status"] == "uncertain"
    assert result["badge"] == "warning"


def test_no_hits_is_not_found():
    """Zero hits -> not_found."""
    client = _mock_client_with_hits([])
    result = _do_check("Nonexistent v. Case", client)
    assert result["status"] == "not_found"
    assert result["badge"] == "not_found"


def test_budget_exhausted_is_uncertain():
    """Budget exhaustion -> uncertain, not not_found."""
    client = MagicMock()
    client.search.side_effect = BudgetExhausted("out of budget")

    result = _do_check("Smith v. Jones", client)
    assert result["status"] == "uncertain"
    assert "Budget" in result["note"]


def test_search_error_is_uncertain():
    """General exception -> uncertain with error note."""
    client = MagicMock()
    client.search.side_effect = ConnectionError("network down")

    result = _do_check("Smith v. Jones", client)
    assert result["status"] == "uncertain"
    assert "ConnectionError" in result["note"]
