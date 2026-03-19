"""Tests for citation_verify module - no network calls."""

import tempfile
from unittest.mock import MagicMock

from war_room.citation_verify import MAX_CHECKS, _do_check, spot_check_citations
from war_room.exa_client import BudgetExhausted


def _mock_client_with_hits(hits_list):
    """Create a mock ExaClient that returns given hits."""
    client = MagicMock()
    client.provider_name = "exa"
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
        {
            "url": "https://scholar.google.com/case",
            "title": "Result",
            "text": "Real v. Case 123 So. 3d 456",
        },
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
        {"url": "https://example.com", "title": "Hit", "text": "Case result"},
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
            {
                "url": "https://random-blog.com/article",
                "title": "Blog",
                "text": "Smith v. Jones 123 So. 3d 456",
            },
            {
                "url": "https://www.flcourts.gov/case/123",
                "title": "FL Courts",
                "text": "Smith v. Jones 123 So. 3d 456",
            },
            {
                "url": "https://insurancejournal.com/article",
                "title": "Journal",
                "text": "Smith v. Jones 123 So. 3d 456",
            },
        ]
    )

    result = _do_check(
        "Smith v. Jones 123 So. 3d 456",
        client,
        case_name="Smith v. Jones",
        citation="123 So. 3d 456",
    )
    assert result["status"] == "verified"
    assert "flcourts.gov" in result["source_url"]
    assert result["confidence"] == "high"
    assert result["status_reason"] == "official_citation_match"
    assert result["alternate_candidate_count"] == 2


def test_prefers_citation_aligned_result_over_unrelated_official_hit():
    client = _mock_client_with_hits(
        [
            {
                "url": "https://www.flcourts.gov/general/news",
                "title": "Court News",
                "text": "Administrative order update with no matching citation.",
            },
            {
                "url": "https://casetext.com/case/sebo-v-american-home-assurance-co",
                "title": "Sebo v. American Home Assurance Co.",
                "text": "Sebo v. American Home Assurance Co., 208 So. 3d 694 (Fla. 2016).",
            },
        ]
    )

    result = _do_check(
        "Sebo v. American Home Assurance Co. 208 So. 3d 694",
        client,
        case_name="Sebo v. American Home Assurance Co.",
        citation="208 So. 3d 694",
    )

    assert result["status"] == "uncertain"
    assert "casetext.com" in result["source_url"]
    assert result["status_reason"] == "secondary_authority_match"


def test_normalized_citation_spacing_still_matches_primary_authority():
    client = _mock_client_with_hits(
        [
            {
                "url": "https://www.flcourts.gov/case/123",
                "title": "Doe v. Carrier",
                "text": "Doe v. Carrier 123 So. 3d 456",
            }
        ]
    )

    result = _do_check(
        "Doe v. Carrier 123 So.3d 456",
        client,
        case_name="Doe v. Carrier",
        citation="123 So.3d 456",
    )

    assert result["status"] == "verified"
    assert result["status_reason"] == "official_citation_match"


def test_professional_source_is_uncertain():
    """Professional-only hits -> uncertain."""
    client = _mock_client_with_hits(
        [{"url": "https://insurancejournal.com/article", "title": "Article", "text": "Doe v. Carrier 456 F.3d 789"}]
    )

    result = _do_check(
        "Doe v. Carrier 456 F.3d 789",
        client,
        case_name="Doe v. Carrier",
        citation="456 F.3d 789",
    )
    assert result["status"] == "uncertain"
    assert result["badge"] == "warning"
    assert result["status_reason"] == "non_authoritative_match"
    assert result["source_class"] == "news"


def test_irrelevant_hits_are_not_found():
    client = _mock_client_with_hits(
        [{"url": "https://insurancejournal.com/article", "title": "Article", "text": "General insurance litigation update."}]
    )

    result = _do_check(
        "Doe v. Carrier 456 F.3d 789",
        client,
        case_name="Doe v. Carrier",
        citation="456 F.3d 789",
    )
    assert result["status"] == "not_found"
    assert result["badge"] == "not_found"


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
    assert result["status_reason"] == "budget_exhausted"


def test_search_error_is_uncertain():
    """General exception -> uncertain with error note."""
    client = MagicMock()
    client.search.side_effect = ConnectionError("network down")

    result = _do_check("Smith v. Jones", client)
    assert result["status"] == "uncertain"
    assert "ConnectionError" in result["note"]
    assert result["status_reason"] == "search_error"


def test_name_only_match_stays_uncertain():
    client = _mock_client_with_hits(
        [
            {
                "url": "https://www.flcourts.gov/case/123",
                "title": "Doe v. Carrier",
                "text": "Opinion page for Doe v. Carrier with abbreviated header only.",
            }
        ]
    )

    result = _do_check(
        "Doe v. Carrier 456 F.3d 789",
        client,
        case_name="Doe v. Carrier",
        citation="456 F.3d 789",
    )

    assert result["status"] == "uncertain"
    assert result["confidence"] == "low"
    assert result["status_reason"] == "name_match_only"


def test_multiple_conflicting_aligned_hits_surface_ambiguity_reason():
    client = _mock_client_with_hits(
        [
            {
                "url": "https://www.flcourts.gov/general/search",
                "title": "Case lookup",
                "text": "Doe v. Carrier 456 F.3d 789",
            },
            {
                "url": "https://casetext.com/case/doe-v-carrier",
                "title": "Doe v. Carrier",
                "text": "Doe v. Carrier 456 F.3d 789",
            },
        ]
    )

    result = _do_check(
        "Doe v. Carrier 456 F.3d 789",
        client,
        case_name="Doe v. Carrier",
        citation="456 F.3d 789",
    )

    assert result["status"] == "uncertain"
    assert result["status_reason"] == "multiple_conflicting_hits"
    assert result["alternate_candidate_count"] == 1

def test_spot_check_citations_emits_retrieval_state_and_artifact_refs():
    pack = {
        "retrieval_tasks": [
            {
                "retrieval_task_id": "run-milton:caselaw:carrier_precedent:1",
                "run_id": "run-milton",
                "stage_id": "run-milton:caselaw",
                "provider": "exa",
                "query_text": "Doe v. Ins 123 So.3d 456",
                "status": "completed",
                "attempt_count": 1,
                "review_required": False,
                "raw_artifact_refs": [],
                "requested_at": None,
                "completed_at": None,
            }
        ],
        "issues": [
            {
                "issue": "Coverage",
                "cases": [
                    {"name": "Doe v. Ins", "citation": "123 So.3d 456"}
                ],
            }
        ],
    }
    client = _mock_client_with_hits([
        {
            "url": "https://www.flcourts.gov/case/123",
            "title": "FL Courts",
            "text": "Doe v. Ins 123 So.3d 456",
        }
    ])

    with tempfile.TemporaryDirectory() as tmpdir:
        result = spot_check_citations(
            pack,
            client,
            use_cache=False,
            cache_dir=tmpdir,
            cache_samples_dir=tmpdir,
        )

    assert result["retrieval_tasks"]
    assert result["retrieval_tasks"][0]["stage_id"] == "run-milton:citation_verify"
    assert result["retrieval_tasks"][0]["raw_artifact_refs"] == ["https://www.flcourts.gov/case/123"]
    assert {event["event_type"] for event in result["run_events"]} == {"retrieval_started", "retrieval_completed"}

