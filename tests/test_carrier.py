"""Tests for carrier_module - no network calls."""

import tempfile

from war_room.carrier_module import (
    _assemble_pack,
    _build_rebuttals,
    _extract_defenses,
    build_carrier_doc_pack,
)
from war_room.models import CaseIntake


def _sample_intake() -> CaseIntake:
    return CaseIntake(
        event_name="Hurricane Milton",
        event_date="2024-10-09",
        state="FL",
        county="Pinellas",
        carrier="Citizens Property Insurance",
        policy_type="HO-3 Dwelling",
        posture=["denial", "bad_faith"],
        key_facts=["Roof damage reported within 48 hours"],
    )


def test_assemble_pack_structure() -> None:
    results = [
        {
            "url": "https://floir.com/complaint/123",
            "title": "DOI Complaint",
            "snippet": "Citizens Property Insurance complaint filed",
            "text": "Complaint regarding pre-existing damage denial",
            "category": "doi_complaints",
        },
        {
            "url": "https://insurancejournal.com/article",
            "title": "Citizens Denial Patterns",
            "snippet": "Pattern of claim denials after Milton",
            "text": "Citizens has denied claims citing pre-existing conditions and wear and tear",
            "category": "denial_patterns",
        },
    ]
    pack = _assemble_pack(_sample_intake(), results)
    assert pack["module"] == "carrier"
    assert "carrier_snapshot" in pack
    assert isinstance(pack["document_pack"], list)
    assert isinstance(pack["common_defenses"], list)
    assert isinstance(pack["rebuttal_angles"], list)
    assert isinstance(pack["sources"], list)


def test_generic_regulatory_pages_are_excluded() -> None:
    results = [
        {
            "url": "https://floir.com/consumers",
            "title": "Consumers - floir",
            "snippet": "Generic consumer landing page",
            "text": "Consumers page",
            "category": "doi_complaints",
        },
        {
            "url": "https://floir.com/reports/citizens-market-conduct-exam.pdf",
            "title": "Citizens Market Conduct Exam Report",
            "snippet": "Exam report for Citizens",
            "text": "Complaint handling and claims findings",
            "category": "doi_complaints",
        },
    ]

    pack = _assemble_pack(_sample_intake(), results)

    titles = [document["title"] for document in pack["document_pack"]]
    assert "Consumers - floir" not in titles
    assert "Citizens Market Conduct Exam Report" in titles


def test_high_value_documents_rank_ahead_of_generic_articles() -> None:
    results = [
        {
            "url": "https://news.example.com/citizens-story",
            "title": "Citizens Faces Questions After Milton",
            "snippet": "News story",
            "text": "General coverage",
            "category": "regulatory_action",
        },
        {
            "url": "https://floir.com/docs/final-order.pdf",
            "title": "Final Order on Citizens Claims Practices",
            "snippet": "Official order",
            "text": "Order regarding claims practices",
            "category": "regulatory_action",
        },
    ]

    pack = _assemble_pack(_sample_intake(), results)

    assert pack["document_pack"][0]["title"] == "Final Order on Citizens Claims Practices"


def test_extract_defenses() -> None:
    intake = _sample_intake()
    results = [
        {"text": "The carrier argued pre-existing damage and wear and tear exclusion"},
    ]
    defenses = _extract_defenses(results, intake)
    assert any("pre-existing" in defense.lower() for defense in defenses)
    assert any("wear and tear" in defense.lower() for defense in defenses)


def test_build_rebuttals_includes_key_facts() -> None:
    intake = _sample_intake()
    rebuttals = _build_rebuttals(intake, [], [])
    assert any("Roof damage" in rebuttal for rebuttal in rebuttals)


def test_build_rebuttals_bad_faith() -> None:
    intake = _sample_intake()
    rebuttals = _build_rebuttals(intake, [], [])
    assert any("bad-faith" in rebuttal.lower() for rebuttal in rebuttals)




class _CarrierProvider:
    provider_name = "exa"

    def __init__(self) -> None:
        self.calls = 0

    def search(self, query: str, **kwargs: object) -> list[dict[str, object]]:
        self.calls += 1
        return [{
            "url": f"https://example.com/carrier/{self.calls}",
            "title": "Claims Manual",
            "snippet": "Citizens denial pattern context.",
            "text": "Citizens has denied claims citing pre-existing damage.",
        }]

    def get_contents(self, urls: list[str], **kwargs: object) -> list[dict[str, object]]:
        return []


def test_build_carrier_pack_emits_retrieval_state() -> None:
    pack = build_carrier_doc_pack(
        _sample_intake(),
        client=_CarrierProvider(),
        use_cache=False,
    )

    assert pack["retrieval_tasks"]
    assert all(task["status"] == "completed" for task in pack["retrieval_tasks"])
    assert all(task["stage_id"].endswith(":carrier") for task in pack["retrieval_tasks"])
    assert len(pack["run_events"]) == len(pack["retrieval_tasks"]) * 2
    assert {event["event_type"] for event in pack["run_events"]} == {"retrieval_started", "retrieval_completed"}

def test_build_carrier_pack_without_client_returns_structured_fallback() -> None:
    intake = _sample_intake()
    with tempfile.TemporaryDirectory() as cache_dir, tempfile.TemporaryDirectory() as samples_dir:
        pack = build_carrier_doc_pack(
            intake,
            client=None,
            use_cache=False,
            cache_dir=cache_dir,
            cache_samples_dir=samples_dir,
        )

    assert pack["module"] == "carrier"
    assert pack["document_pack"] == []
    assert pack["common_defenses"] == []
    assert pack["rebuttal_angles"] == []
    assert "warnings" in pack
    assert any("No Exa client available" in warning for warning in pack["warnings"])
