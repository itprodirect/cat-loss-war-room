"""Tests for carrier_module - no network calls."""

import tempfile

from war_room.models import CaseIntake
from war_room.query_plan import generate_query_plan
from war_room.carrier_module import (
    _assemble_pack,
    _build_rebuttals,
    _extract_defenses,
    _normalize_carrier_pack,
    build_carrier_doc_pack,
)


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


def test_normalize_carrier_pack_filters_low_value_sources_and_boilerplate_notes() -> None:
    intake = _sample_intake()
    payload = {
        "module": "carrier",
        "carrier_snapshot": {
            "name": intake.carrier,
            "state": intake.state,
            "event": intake.event_name,
            "policy_type": intake.policy_type,
        },
        "document_pack": [
            {
                "doc_type": "Claims Handling Guideline",
                "title": "What to Expect After Reporting Your Claim",
                "url": "https://www.citizensfla.com/documents/claim-brochure.pdf",
                "badge": "professional",
                "why_it_matters": "CONTINUE TO SITE\n\nWhat to expect",
            },
            {
                "doc_type": "DOI/Regulatory Complaint",
                "title": "Citizens Market Conduct Exam Report",
                "url": "https://floir.com/reports/citizens-market-conduct-exam.pdf",
                "badge": "official",
                "why_it_matters": "Complaint handling findings",
            },
        ],
        "common_defenses": [],
        "rebuttal_angles": [],
        "sources": [
            {
                "title": "Consumers - floir",
                "url": "https://floir.com/consumers",
                "badge": "official",
                "reason": "Official source",
            },
            {
                "title": "What to Expect After Reporting Your Claim",
                "url": "https://www.citizensfla.com/documents/claim-brochure.pdf",
                "badge": "professional",
                "reason": "Professional source",
            },
            {
                "title": "Citizens Market Conduct Exam Report",
                "url": "https://floir.com/reports/citizens-market-conduct-exam.pdf",
                "badge": "official",
                "reason": "Official source",
            },
        ],
    }

    pack = _normalize_carrier_pack(payload, intake)

    assert [document["title"] for document in pack["document_pack"]] == [
        "Citizens Market Conduct Exam Report"
    ]
    assert [source["title"] for source in pack["sources"]] == [
        "Citizens Market Conduct Exam Report"
    ]


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


def test_normalize_carrier_pack_prioritizes_official_regulatory_material_over_news() -> None:
    intake = _sample_intake()
    payload = {
        "module": "carrier",
        "carrier_snapshot": {
            "name": intake.carrier,
            "state": intake.state,
            "event": intake.event_name,
            "policy_type": intake.policy_type,
        },
        "document_pack": [
            {
                "doc_type": "Denial Pattern Analysis",
                "title": "Citizens sued over alleged mishandling of Hurricane Milton claim | Insurance Business",
                "url": "https://www.insurancebusinessmag.com/us/news/legal-insights/citizens-sued-over-alleged-mishandling-of-hurricane-milton-claim-550172.aspx",
                "badge": "unvetted",
                "why_it_matters": "News article",
            },
            {
                "doc_type": "DOI/Regulatory Complaint",
                "title": "[PDF] CITIZENS PROPERTY INSURANCE CORPORATION",
                "url": "https://floir.com/docs-sf/default-source/property-and-casualty/citizens-market-conduct-exam-reports/citizens-property-insurance-corporation-final-exam-report_1-18-2023.pdf",
                "badge": "official",
                "why_it_matters": "Exam report",
            },
            {
                "doc_type": "Regulatory Action",
                "title": "Orders and Memoranda - Florida Office of Insurance Regulation",
                "url": "https://www.floir.com/resources-and-reports/orders-and-memoranda",
                "badge": "official",
                "why_it_matters": "Orders",
            },
        ],
        "common_defenses": [],
        "rebuttal_angles": [],
        "sources": [
            {
                "title": "Citizens sued over alleged mishandling of Hurricane Milton claim | Insurance Business",
                "url": "https://www.insurancebusinessmag.com/us/news/legal-insights/citizens-sued-over-alleged-mishandling-of-hurricane-milton-claim-550172.aspx",
                "badge": "unvetted",
                "reason": "Unvetted source",
            },
            {
                "title": "[PDF] CITIZENS PROPERTY INSURANCE CORPORATION",
                "url": "https://floir.com/docs-sf/default-source/property-and-casualty/citizens-market-conduct-exam-reports/citizens-property-insurance-corporation-final-exam-report_1-18-2023.pdf",
                "badge": "official",
                "reason": "Official source",
            },
        ],
    }

    pack = _normalize_carrier_pack(payload, intake)

    assert pack["document_pack"][0]["title"] == "[PDF] CITIZENS PROPERTY INSURANCE CORPORATION"
    assert pack["document_pack"][1]["title"] == "Orders and Memoranda - Florida Office of Insurance Regulation"
    assert pack["sources"][0]["title"] == "[PDF] CITIZENS PROPERTY INSURANCE CORPORATION"


def test_normalize_carrier_pack_drops_unvetted_rows_when_strong_evidence_is_present() -> None:
    intake = _sample_intake()
    payload = {
        "module": "carrier",
        "carrier_snapshot": {
            "name": intake.carrier,
            "state": intake.state,
            "event": intake.event_name,
            "policy_type": intake.policy_type,
        },
        "document_pack": [
            {
                "doc_type": "DOI/Regulatory Complaint",
                "title": "[PDF] CITIZENS PROPERTY INSURANCE CORPORATION",
                "url": "https://floir.com/docs-sf/default-source/property-and-casualty/citizens-market-conduct-exam-reports/citizens-property-insurance-corporation-final-exam-report_1-18-2023.pdf",
                "badge": "official",
                "why_it_matters": "Exam report",
            },
            {
                "doc_type": "DOI/Regulatory Complaint",
                "title": "Orders and Memoranda - Florida Office of Insurance Regulation",
                "url": "https://www.floir.com/resources-and-reports/orders-and-memoranda",
                "badge": "official",
                "why_it_matters": "Orders",
            },
            {
                "doc_type": "Denial Pattern Analysis",
                "title": "Commissioner Yaworsky Fights for Consumers and Brings More ...",
                "url": "https://floir.gov/home/2025/04/09/commissioner-yaworsky-fights-for-consumers-and-brings-more-transparency-and-accountability-for-hurricane-claim-denials",
                "badge": "official",
                "why_it_matters": "Commissioner statement",
            },
            {
                "doc_type": "Denial Pattern Analysis",
                "title": "Citizens sued over alleged mishandling of Hurricane Milton claim | Insurance Business",
                "url": "https://www.insurancebusinessmag.com/us/news/legal-insights/citizens-sued-over-alleged-mishandling-of-hurricane-milton-claim-550172.aspx",
                "badge": "unvetted",
                "why_it_matters": "News article",
            },
        ],
        "common_defenses": [],
        "rebuttal_angles": [],
        "sources": [
            {
                "title": "[PDF] CITIZENS PROPERTY INSURANCE CORPORATION",
                "url": "https://floir.com/docs-sf/default-source/property-and-casualty/citizens-market-conduct-exam-reports/citizens-property-insurance-corporation-final-exam-report_1-18-2023.pdf",
                "badge": "official",
                "reason": "Official source",
            },
            {
                "title": "Orders and Memoranda - Florida Office of Insurance Regulation",
                "url": "https://www.floir.com/resources-and-reports/orders-and-memoranda",
                "badge": "official",
                "reason": "Official source",
            },
            {
                "title": "Commissioner Yaworsky Fights for Consumers and Brings More ...",
                "url": "https://floir.gov/home/2025/04/09/commissioner-yaworsky-fights-for-consumers-and-brings-more-transparency-and-accountability-for-hurricane-claim-denials",
                "badge": "official",
                "reason": "Official source",
            },
            {
                "title": "Citizens sued over alleged mishandling of Hurricane Milton claim | Insurance Business",
                "url": "https://www.insurancebusinessmag.com/us/news/legal-insights/citizens-sued-over-alleged-mishandling-of-hurricane-milton-claim-550172.aspx",
                "badge": "unvetted",
                "reason": "Unvetted source",
            },
        ],
    }

    pack = _normalize_carrier_pack(payload, intake)

    assert all("Insurance Business" not in document["title"] for document in pack["document_pack"])
    assert all("Insurance Business" not in source["title"] for source in pack["sources"])


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


def test_build_carrier_pack_uses_shared_query_plan(monkeypatch) -> None:
    shared_plan = generate_query_plan(_sample_intake())

    def _unexpected_regeneration(*args: object, **kwargs: object) -> list[object]:
        raise AssertionError("carrier module regenerated the query plan")

    monkeypatch.setattr("war_room.carrier_module.generate_query_plan", _unexpected_regeneration)

    provider = _CarrierProvider()
    pack = build_carrier_doc_pack(
        _sample_intake(),
        client=provider,
        use_cache=False,
        query_plan=shared_plan,
    )

    expected_queries = [query for query in shared_plan if query.module == "carrier_docs"]
    assert provider.calls == len(expected_queries)
    assert len(pack["retrieval_tasks"]) == len(expected_queries)
    assert all(task["query_text"] in {query.query for query in expected_queries} for task in pack["retrieval_tasks"])

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
