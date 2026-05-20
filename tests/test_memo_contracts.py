"""Tests for typed citation/export contracts (issue #6 slice 3)."""

import copy

import pytest
from pydantic import ValidationError

from war_room.export_md import render_markdown_memo
from war_room.models import (
    CaseIntake,
    QuerySpec,
    adapt_citation_verify_pack,
    carrier_doc_pack_to_evidence_items,
    caselaw_pack_to_evidence_items,
    citation_verify_pack_to_evidence_items,
    citation_verify_pack_to_payload,
    dedupe_evidence_items,
    memo_render_input_from_parts,
    run_audit_snapshot_from_parts,
    run_audit_snapshot_to_payload,
    weather_brief_to_evidence_items,
)


def _sample_payloads():
    intake = CaseIntake(
        event_name="Hurricane Milton",
        event_date="2024-10-09",
        state="FL",
        county="Pinellas",
        carrier="Citizens Property Insurance",
        policy_type="HO-3 Dwelling",
        posture=["denial"],
    )

    weather = {
        "module": "weather",
        "event_summary": "Hurricane Milton - Pinellas County, FL",
        "key_observations": ["Winds of 120 mph"],
        "metrics": {"max_wind_mph": 120, "storm_surge_ft": None, "rain_in": None},
        "sources": [
            {
                "title": "NWS report",
                "url": "https://weather.gov/r",
                "badge": "official",
                "reason": "Official source",
            }
        ],
    }

    carrier = {
        "module": "carrier",
        "carrier_snapshot": {
            "name": "Citizens",
            "state": "FL",
            "event": "Milton",
            "policy_type": "HO-3",
        },
        "document_pack": [
            {
                "doc_type": "Denial",
                "title": "Doc",
                "url": "https://example.com/doc",
                "badge": "professional",
                "why_it_matters": "Relevant",
            }
        ],
        "common_defenses": ["Pre-existing damage"],
        "rebuttal_angles": ["Timeline contradicts carrier position"],
        "sources": [
            {
                "title": "Article",
                "url": "https://example.com/article",
                "badge": "professional",
                "reason": "Professional source",
            }
        ],
    }

    caselaw = {
        "module": "caselaw",
        "issues": [
            {
                "issue": "Coverage",
                "cases": [
                    {
                        "name": "Doe v. Ins",
                        "citation": "123 So.3d 456",
                        "court": "Fla. App.",
                        "year": "2023",
                        "one_liner": "Coverage upheld",
                        "url": "https://example.com/case",
                        "badge": "professional",
                    }
                ],
                "notes": ["Relevant"],
            }
        ],
        "sources": [
            {
                "title": "Case",
                "url": "https://example.com/case",
                "badge": "professional",
                "reason": "Professional source",
            }
        ],
    }

    citecheck = {
        "module": "citation_verify",
        "disclaimer": "SPOT-CHECK ONLY",
        "checks": [
            {
                "badge": "verified",
                "case_name": "Doe v. Ins",
                "citation": "123 So.3d 456",
                "status": "verified",
                "note": "Found on official source",
                "source_url": "https://example.com/case",
            }
        ],
        "summary": {"total": 1, "verified": 1, "uncertain": 0, "not_found": 0},
    }

    query_plan = [QuerySpec(module="weather", query="test query", category="test")]

    return intake, weather, carrier, caselaw, citecheck, query_plan


def test_weather_evidence_adapter_returns_stable_ids_for_repeated_payloads():
    _, weather, _, _, _, _ = _sample_payloads()

    first_ids = [item.evidence_id for item in weather_brief_to_evidence_items(weather)]
    second_ids = [item.evidence_id for item in weather_brief_to_evidence_items(weather)]

    assert first_ids == second_ids
    assert first_ids[0].startswith("weather-source-nws-report-")
    assert first_ids[0] != "weather-source-1"


def test_weather_evidence_adapter_does_not_collapse_distinct_source_rows():
    _, weather, _, _, _, _ = _sample_payloads()
    weather["key_observations"].append("Storm surge was reported near the county shoreline.")
    weather["sources"].append(
        {
            "title": "NWS follow-up report",
            "url": "https://weather.gov/r",
            "badge": "official",
            "reason": "Second county-specific weather source row.",
        }
    )

    evidence_ids = [item.evidence_id for item in weather_brief_to_evidence_items(weather)]

    assert len(evidence_ids) == 2
    assert len(set(evidence_ids)) == 2


def test_weather_evidence_adapter_suffixes_duplicate_source_rows():
    _, weather, _, _, _, _ = _sample_payloads()
    weather["key_observations"].append("Winds of 120 mph")
    weather["sources"].append(dict(weather["sources"][0]))

    evidence_ids = [item.evidence_id for item in weather_brief_to_evidence_items(weather)]
    base_id = evidence_ids[0]

    assert evidence_ids == [base_id, f"{base_id}-2"]


def test_weather_evidence_adapter_preserves_source_metadata():
    _, weather, _, _, _, _ = _sample_payloads()
    weather["key_observations"][0] = "Observed 120 mph gusts in Pinellas County."
    weather["sources"][0].update(
        {
            "title": "NWS Local Storm Report",
            "url": "https://weather.gov/milton/local",
            "badge": "official",
            "reason": "County-specific official weather corroboration.",
            "source_class": "government_guidance",
            "is_primary_authority": True,
        }
    )

    item = weather_brief_to_evidence_items(weather)[0]

    assert item.module == "weather"
    assert item.evidence_type == "weather_source"
    assert item.title == "NWS Local Storm Report"
    assert item.summary == "Observed 120 mph gusts in Pinellas County."
    assert item.url == "https://weather.gov/milton/local"
    assert item.badge == "official"
    assert item.source_reason == "County-specific official weather corroboration."
    assert item.source_class == "government_guidance"
    assert item.source_tier == "official"
    assert item.is_primary_authority is True
    assert item.authority_key == "authority:nws local storm report"


def test_weather_evidence_adapter_infers_primary_authority_when_field_missing():
    _, weather, _, _, _, _ = _sample_payloads()
    source = weather["sources"][0]
    source.update(
        {
            "title": "Sebo v. American Home Assurance Co.",
            "url": "https://www.courtlistener.com/opinion/12345/sebo-v-american-home/",
            "badge": "official",
        }
    )

    assert "is_primary_authority" not in source

    item = weather_brief_to_evidence_items(weather)[0]

    assert item.source_class == "court_opinion"
    assert item.source_tier == "official"
    assert item.is_primary_authority is True

    source["is_primary_authority"] = False

    explicit_item = weather_brief_to_evidence_items(weather)[0]

    assert explicit_item.is_primary_authority is False


def test_carrier_evidence_adapter_returns_stable_ids_for_repeated_payloads():
    _, _, carrier, _, _, _ = _sample_payloads()

    first_ids = [item.evidence_id for item in carrier_doc_pack_to_evidence_items(carrier)]
    second_ids = [item.evidence_id for item in carrier_doc_pack_to_evidence_items(carrier)]

    assert first_ids == second_ids
    assert first_ids[0].startswith("carrier-document-denial-")
    assert first_ids[0] != "carrier-document-1"


def test_carrier_evidence_adapter_does_not_collapse_distinct_document_rows():
    _, _, carrier, _, _, _ = _sample_payloads()
    carrier["document_pack"].append(
        {
            "doc_type": "Regulatory Action",
            "title": "Doc follow-up",
            "url": "https://example.com/doc",
            "badge": "professional",
            "why_it_matters": "Same URL, distinct document row.",
        }
    )

    evidence_ids = [item.evidence_id for item in carrier_doc_pack_to_evidence_items(carrier)]

    assert len(evidence_ids) == 2
    assert len(set(evidence_ids)) == 2


def test_carrier_evidence_adapter_uses_scored_source_profile_over_document_metadata():
    _, _, carrier, _, _, _ = _sample_payloads()
    document = carrier["document_pack"][0]
    document.update(
        {
            "badge": "official",
            "source_class": "government_guidance",
            "source_tier": "official",
            "is_primary_authority": True,
        }
    )
    carrier["sources"][0]["url"] = document["url"]
    carrier["sources"][0]["source_class"] = "professional"

    item = carrier_doc_pack_to_evidence_items(carrier)[0]

    assert item.module == "carrier"
    assert item.evidence_type == "denial"
    assert item.title == "Doc"
    assert item.summary == "Relevant"
    assert item.url == "https://example.com/doc"
    assert item.badge == "official"
    assert item.source_reason == "Professional source"
    assert item.source_class == "professional"
    assert item.source_tier == "unvetted"
    assert item.is_primary_authority is False
    assert item.authority_key == "authority:doc"


def test_carrier_evidence_adapter_ignores_explicit_primary_authority_override():
    _, _, carrier, _, _, _ = _sample_payloads()
    document = carrier["document_pack"][0]
    document.update(
        {
            "doc_type": "Regulatory Action",
            "title": "Sebo v. American Home Assurance Co.",
            "url": "https://www.courtlistener.com/opinion/12345/sebo-v-american-home/",
            "badge": "official",
        }
    )

    # The spoofed false flag must not demote deterministic primary authority
    # from a CourtListener opinion URL.
    document["is_primary_authority"] = False

    explicit_item = carrier_doc_pack_to_evidence_items(carrier)[0]

    assert explicit_item.source_class == "court_opinion"
    assert explicit_item.source_tier == "official"
    assert explicit_item.is_primary_authority is True


def test_caselaw_evidence_adapter_returns_stable_ids_for_repeated_payloads():
    _, _, _, caselaw, _, _ = _sample_payloads()

    first_ids = [item.evidence_id for item in caselaw_pack_to_evidence_items(caselaw)]
    second_ids = [item.evidence_id for item in caselaw_pack_to_evidence_items(caselaw)]

    assert first_ids == second_ids
    assert first_ids[0].startswith("caselaw-case-123-so-3d-456-")
    assert first_ids[0] != "caselaw-case-1-1"


def test_caselaw_evidence_adapter_does_not_collapse_distinct_case_rows():
    _, _, _, caselaw, _, _ = _sample_payloads()
    caselaw["issues"][0]["cases"].append(
        {
            "name": "Roe v. Ins",
            "citation": "123 So.3d 456",
            "court": "Fla. App.",
            "year": "2023",
            "one_liner": "Same reporter cite, different authority row.",
            "url": "https://example.com/roe-case",
            "badge": "professional",
        }
    )

    evidence_ids = [item.evidence_id for item in caselaw_pack_to_evidence_items(caselaw)]

    assert len(evidence_ids) == 2
    assert len(set(evidence_ids)) == 2


def test_caselaw_evidence_adapter_preserves_case_metadata():
    _, _, _, caselaw, _, _ = _sample_payloads()
    caselaw["issues"][0]["cases"][0].update(
        {
            "badge": "official",
            "source_class": "court_opinion",
            "source_tier": "official",
            "is_primary_authority": True,
        }
    )

    item = caselaw_pack_to_evidence_items(caselaw)[0]

    assert item.module == "caselaw"
    assert item.evidence_type == "case_authority"
    assert item.title == "Doe v. Ins"
    assert item.summary == "Coverage upheld"
    assert item.url == "https://example.com/case"
    assert item.badge == "official"
    assert item.source_reason == "Professional source"
    assert item.source_class == "court_opinion"
    assert item.source_tier == "official"
    assert item.is_primary_authority is True
    assert item.issue == "Coverage"
    assert item.citation == "123 so. 3d 456"
    assert item.authority_key == "citation:123 so. 3d 456"


def test_caselaw_evidence_adapter_infers_primary_authority_when_field_missing():
    _, _, _, caselaw, _, _ = _sample_payloads()
    case = caselaw["issues"][0]["cases"][0]
    case.update(
        {
            "name": "Sebo v. American Home Assurance Co.",
            "url": "https://www.courtlistener.com/opinion/12345/sebo-v-american-home/",
            "badge": "official",
        }
    )

    assert "is_primary_authority" not in case

    item = caselaw_pack_to_evidence_items(caselaw)[0]

    assert item.source_class == "court_opinion"
    assert item.source_tier == "official"
    assert item.is_primary_authority is True

    case["is_primary_authority"] = False

    explicit_item = caselaw_pack_to_evidence_items(caselaw)[0]

    assert explicit_item.is_primary_authority is False


def test_citation_verify_pack_adapter_round_trip():
    _, _, _, _, citecheck, _ = _sample_payloads()

    typed = adapt_citation_verify_pack(citecheck)
    dumped = citation_verify_pack_to_payload(typed)

    assert typed.module == "citation_verify"
    assert dumped["summary"]["total"] == 1


def test_citation_verify_pack_adapter_backfills_sparse_trust_metadata():
    _, _, _, _, citecheck, _ = _sample_payloads()
    citecheck["checks"][0].pop("source_url", None)
    citecheck["checks"][0]["source_url"] = "https://casetext.com/case/doe-v-ins"
    citecheck["checks"][0]["status"] = "uncertain"
    citecheck["checks"][0]["note"] = "Found on professional source: casetext.com - verify independently"
    citecheck["summary"] = {"total": 1, "verified": 0, "uncertain": 1, "not_found": 0}

    typed = adapt_citation_verify_pack(citecheck)
    check = typed.checks[0]

    assert check.status_reason == "secondary_authority_match"
    assert check.trust_explanation
    assert check.source_tier == "professional"
    assert check.source_class == "court_opinion"
    assert check.is_primary_authority is True
    assert check.confidence == "medium"


def test_citation_verify_evidence_adapter_returns_stable_provenance_ids():
    _, _, _, _, citecheck, _ = _sample_payloads()

    first_ids = [
        item.evidence_id for item in citation_verify_pack_to_evidence_items(citecheck)
    ]
    second_ids = [
        item.evidence_id for item in citation_verify_pack_to_evidence_items(citecheck)
    ]

    assert first_ids == second_ids
    assert first_ids[0].startswith("citation-check-123-so-3d-456-")
    assert first_ids[0] != "citation-check-1"


def test_citation_verify_evidence_adapter_ids_ignore_note_copy_edits():
    _, _, _, _, citecheck, _ = _sample_payloads()
    edited_citecheck = copy.deepcopy(citecheck)
    edited_citecheck["checks"][0]["note"] = (
        "Found on official source; attorney should verify before relying on it."
    )

    original_id = citation_verify_pack_to_evidence_items(citecheck)[0].evidence_id
    edited_id = citation_verify_pack_to_evidence_items(edited_citecheck)[0].evidence_id

    assert edited_id == original_id


def test_citation_verify_evidence_adapter_does_not_collapse_distinct_check_rows():
    _, _, _, _, citecheck, _ = _sample_payloads()
    citecheck["checks"].append(
        {
            "badge": "warning",
            "case_name": "Roe v. Ins",
            "citation": "123 So.3d 456",
            "status": "uncertain",
            "note": "Same citation, distinct citation-check row.",
            "source_url": "https://example.com/roe-case",
        }
    )
    citecheck["summary"] = {"total": 2, "verified": 1, "uncertain": 1, "not_found": 0}

    evidence_ids = [
        item.evidence_id for item in citation_verify_pack_to_evidence_items(citecheck)
    ]

    assert len(evidence_ids) == 2
    assert len(set(evidence_ids)) == 2


def test_citation_verify_evidence_adapter_suffixes_duplicate_check_rows():
    _, _, _, _, citecheck, _ = _sample_payloads()
    citecheck["checks"].append(dict(citecheck["checks"][0]))
    citecheck["summary"] = {"total": 2, "verified": 2, "uncertain": 0, "not_found": 0}

    evidence_ids = [
        item.evidence_id for item in citation_verify_pack_to_evidence_items(citecheck)
    ]
    base_id = evidence_ids[0]

    assert evidence_ids == [base_id, f"{base_id}-2"]


def test_citation_verify_evidence_adapter_preserves_existing_metadata_fields():
    _, _, _, _, citecheck, _ = _sample_payloads()
    citecheck["checks"][0].update(
        {
            "badge": "official",
            "source_url": "https://www.flcourts.gov/case/123",
            "source_class": "court_opinion",
            "source_tier": "official",
            "is_primary_authority": True,
            "status_reason": "official_citation_match",
            "trust_explanation": "Not an EvidenceItem field.",
            "confidence": "high",
        }
    )

    item = citation_verify_pack_to_evidence_items(citecheck)[0]

    assert item.module == "citation_verify"
    assert item.evidence_type == "citation_check"
    assert item.title == "Doe v. Ins"
    assert item.summary == "Found on official source"
    assert item.url == "https://www.flcourts.gov/case/123"
    assert item.badge == "official"
    assert item.source_reason == "verified"
    assert item.source_class == "court_opinion"
    assert item.source_tier == "official"
    assert item.is_primary_authority is True
    assert item.citation == "123 so. 3d 456"
    assert item.authority_key == "citation:123 so. 3d 456"
    assert item.review_required is False
    assert "status_reason" not in item.model_dump()
    assert "trust_explanation" not in item.model_dump()
    assert "confidence" not in item.model_dump()


def test_citation_verify_evidence_adapter_handles_sparse_metadata_safely():
    _, _, _, _, citecheck, _ = _sample_payloads()
    citecheck["checks"] = [
        {
            "badge": "not_found",
            "status": "not_found",
            "note": "No results found.",
        }
    ]
    citecheck["summary"] = {"total": 1, "verified": 0, "uncertain": 0, "not_found": 1}

    item = citation_verify_pack_to_evidence_items(citecheck)[0]

    assert item.evidence_id.startswith("citation-check-not-found-")
    assert item.title == "Citation Check 1"
    assert item.summary == "No results found."
    assert item.url is None
    assert item.source_reason == "not_found"
    assert item.source_class is None
    assert item.source_tier is None
    assert item.is_primary_authority is False
    assert item.authority_key is None
    assert item.citation is None
    assert item.review_required is True


def test_dedupe_evidence_items_collapses_normalized_url_duplicates():
    _, weather, _, _, _, _ = _sample_payloads()
    weather["sources"][0]["url"] = "https://www.weather.gov/r/?utm_source=newsletter"
    weather["sources"].append(
        {
            **weather["sources"][0],
            "url": "https://weather.gov/r",
        }
    )
    weather["key_observations"].append(
        "Candidate-only summary should not be merged into the retained row."
    )

    items = weather_brief_to_evidence_items(weather)
    deduped = dedupe_evidence_items(items)

    assert len(items) == 2
    assert items[0].summary != items[1].summary
    assert [item.evidence_id for item in deduped] == [items[0].evidence_id]
    assert deduped[0].url == "https://www.weather.gov/r/?utm_source=newsletter"
    assert deduped[0].summary == "Winds of 120 mph"
    assert deduped[0].badge == items[0].badge
    assert deduped[0].review_required is items[0].review_required


def test_dedupe_evidence_items_uses_citation_key_when_url_is_absent():
    _, _, _, _, citecheck, _ = _sample_payloads()
    citecheck["checks"][0].pop("source_url", None)
    citecheck["checks"][0]["status"] = "uncertain"
    citecheck["checks"][0]["badge"] = "warning"
    citecheck["checks"][0]["note"] = "Citation text needs manual review."
    citecheck["checks"].append(dict(citecheck["checks"][0]))
    citecheck["summary"] = {"total": 2, "verified": 0, "uncertain": 2, "not_found": 0}

    items = citation_verify_pack_to_evidence_items(citecheck)
    deduped = dedupe_evidence_items(items)

    assert len(items) == 2
    assert [item.evidence_id for item in deduped] == [items[0].evidence_id]
    assert deduped[0].citation == "123 so. 3d 456"
    assert deduped[0].source_reason == "uncertain"
    assert deduped[0].review_required is True


def test_dedupe_evidence_items_uses_module_scoped_title_fallback():
    _, weather, _, _, _, _ = _sample_payloads()
    item = weather_brief_to_evidence_items(weather)[0].model_copy(
        update={
            "evidence_id": "weather-title-fallback-1",
            "url": None,
            "authority_key": None,
            "citation": None,
        }
    )
    duplicate = item.model_copy(
        update={
            "evidence_id": "weather-title-fallback-2",
            "summary": "Same title from a later row.",
        }
    )

    deduped = dedupe_evidence_items([item, duplicate])

    assert [row.evidence_id for row in deduped] == ["weather-title-fallback-1"]
    assert deduped[0].summary == item.summary


def test_dedupe_evidence_items_keeps_sparse_rows_without_clear_key():
    _, _, _, _, citecheck, _ = _sample_payloads()
    citecheck["checks"] = [
        {
            "badge": "not_found",
            "status": "not_found",
            "note": "No results found.",
        }
    ]
    citecheck["summary"] = {"total": 1, "verified": 0, "uncertain": 0, "not_found": 1}
    item = citation_verify_pack_to_evidence_items(citecheck)[0].model_copy(
        update={
            "evidence_id": "sparse-citation-row-1",
            "title": "",
            "url": None,
            "authority_key": None,
            "citation": None,
        }
    )
    duplicate = item.model_copy(update={"evidence_id": "sparse-citation-row-2"})

    deduped = dedupe_evidence_items([item, duplicate])

    assert [row.evidence_id for row in deduped] == [
        "sparse-citation-row-1",
        "sparse-citation-row-2",
    ]


def test_dedupe_evidence_items_allows_conservative_cross_module_url_dedupe():
    _, _, _, caselaw, citecheck, _ = _sample_payloads()
    case_item = caselaw_pack_to_evidence_items(caselaw)[0].model_copy(
        update={
            "url": "https://www.flcourts.gov/case/123?utm_source=alert",
            "badge": "official",
            "source_reason": "official source",
            "source_class": "court_opinion",
            "source_tier": "official",
            "is_primary_authority": True,
            "issue": None,
        }
    )
    citation_item = citation_verify_pack_to_evidence_items(citecheck)[0].model_copy(
        update={
            "url": "https://flcourts.gov/case/123",
            "badge": "official",
            "source_reason": "official source",
            "source_class": "court_opinion",
            "source_tier": "official",
            "is_primary_authority": True,
        }
    )

    deduped = dedupe_evidence_items([case_item, citation_item])

    assert [row.evidence_id for row in deduped] == [case_item.evidence_id]


def test_dedupe_evidence_items_does_not_cross_module_dedupe_title_fallback():
    _, weather, carrier, _, _, _ = _sample_payloads()
    weather_item = weather_brief_to_evidence_items(weather)[0].model_copy(
        update={
            "evidence_id": "weather-shared-title",
            "title": "Shared evidence title",
            "url": None,
            "authority_key": None,
            "citation": None,
        }
    )
    carrier_item = carrier_doc_pack_to_evidence_items(carrier)[0].model_copy(
        update={
            "evidence_id": "carrier-shared-title",
            "title": "Shared evidence title",
            "url": None,
            "authority_key": None,
            "citation": None,
        }
    )

    deduped = dedupe_evidence_items([weather_item, carrier_item])

    assert [row.evidence_id for row in deduped] == [
        "weather-shared-title",
        "carrier-shared-title",
    ]


def test_dedupe_evidence_items_keeps_distinct_urls_and_review_conflicts():
    _, _, carrier, _, _, _ = _sample_payloads()
    base_item = carrier_doc_pack_to_evidence_items(carrier)[0]
    first_url = base_item.model_copy(
        update={
            "evidence_id": "carrier-doc-id-1",
            "url": "https://example.com/doc?id=1",
        }
    )
    second_url = base_item.model_copy(
        update={
            "evidence_id": "carrier-doc-id-2",
            "url": "https://example.com/doc?id=2",
        }
    )
    review_required_duplicate = first_url.model_copy(
        update={
            "evidence_id": "carrier-doc-review-required",
            "review_required": True,
        }
    )

    deduped = dedupe_evidence_items(
        [first_url, second_url, review_required_duplicate]
    )

    assert [row.evidence_id for row in deduped] == [
        "carrier-doc-id-1",
        "carrier-doc-id-2",
        "carrier-doc-review-required",
    ]


def test_citation_verify_summary_validation_rejects_bad_totals():
    _, _, _, _, citecheck, _ = _sample_payloads()
    citecheck["summary"] = {"total": 99, "verified": 1, "uncertain": 0, "not_found": 0}

    with pytest.raises(ValidationError, match="summary total"):
        adapt_citation_verify_pack(citecheck)


def test_memo_render_input_from_parts_accepts_mixed_shapes():
    intake, weather, carrier, caselaw, citecheck, query_plan = _sample_payloads()

    memo_input = memo_render_input_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        [query_plan[0].model_dump()],
    )

    assert memo_input.schema_version == "v2alpha1"
    assert memo_input.intake.event_name == "Hurricane Milton"
    assert memo_input.citecheck.summary.verified == 1
    assert memo_input.query_plan[0].module == "weather"


def test_run_audit_snapshot_builds_canonical_entities():
    intake, weather, carrier, caselaw, citecheck, query_plan = _sample_payloads()
    weather_evidence_id = weather_brief_to_evidence_items(weather)[0].evidence_id
    carrier_evidence_id = carrier_doc_pack_to_evidence_items(carrier)[0].evidence_id
    caselaw_evidence_id = caselaw_pack_to_evidence_items(caselaw)[0].evidence_id
    citation_evidence_id = citation_verify_pack_to_evidence_items(citecheck)[0].evidence_id

    snapshot = run_audit_snapshot_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        [query_plan[0].model_dump()],
    )
    payload = run_audit_snapshot_to_payload(snapshot)

    assert len(snapshot.evidence_items) == 4
    assert len(snapshot.evidence_clusters) == 3
    assert len(snapshot.memo_claims) == 4
    assert snapshot.review_events == []
    assert snapshot.schema_version == "v2alpha1"
    assert snapshot.export_artifact.artifact_type == "markdown_memo"
    assert snapshot.export_artifact.run_id == "run-notebook-hurricane-milton-fl-pinellas-citizens-property-insurance"
    assert (
        snapshot.export_artifact.artifact_id
        == "run-notebook-hurricane-milton-fl-pinellas-citizens-property-insurance:artifact:markdown-memo"
    )
    assert snapshot.export_artifact.review_required is False
    assert snapshot.export_artifact.uri == "runs/run-notebook-hurricane-milton-fl-pinellas-citizens-property-insurance/research-memo.md"
    assert "Appendix: Quality Snapshot" in snapshot.export_artifact.section_titles
    assert "Appendix: Evidence Clusters" in snapshot.export_artifact.section_titles
    assert "Appendix: Evidence Index" in snapshot.export_artifact.section_titles
    assert snapshot.export_artifact.section_ids[:3] == ["trust-snapshot", "case-intake", "weather-corroboration"]
    assert payload["schema_version"] == "v2alpha1"
    assert payload["evidence_items"][0]["evidence_id"] == weather_evidence_id
    assert any(
        item.evidence_id == weather_evidence_id and item.module == "weather"
        for item in snapshot.evidence_items
    )
    assert any(
        item.evidence_id == carrier_evidence_id and item.module == "carrier"
        for item in snapshot.evidence_items
    )
    assert any(
        item.evidence_id == caselaw_evidence_id and item.module == "caselaw"
        for item in snapshot.evidence_items
    )
    assert any(
        item.evidence_id == citation_evidence_id and item.module == "citation_verify"
        for item in snapshot.evidence_items
    )
    assert citation_evidence_id in snapshot.memo_claims[3].evidence_ids
    assert payload["evidence_clusters"][0]["cluster_id"] == "cluster-1"
    assert payload["evidence_clusters"][2]["cluster_type"] == "citation"
    assert snapshot.memo_claims[0].cluster_ids == ["cluster-1"]
    assert weather_evidence_id in snapshot.memo_claims[0].evidence_ids
    assert carrier_evidence_id in snapshot.memo_claims[1].evidence_ids
    assert caselaw_evidence_id in snapshot.memo_claims[2].evidence_ids
    assert snapshot.memo_claims[2].cluster_ids == ["cluster-3"]
    assert snapshot.quality_snapshot.source_class_counts["government_guidance"] == 1
    assert snapshot.quality_snapshot.grouped_evidence_count == 1
    assert snapshot.quality_snapshot.normalized_authority_count == 3
    assert snapshot.quality_snapshot.duplicate_authority_count == 1
    assert snapshot.evidence_clusters[2].authority_key == "citation:123 so. 3d 456"
    assert snapshot.evidence_clusters[2].provenance_urls == ["https://example.com/case"]
    assert payload["memo_claims"][3]["cluster_ids"] == ["cluster-3"]
    assert payload["export_artifact"]["artifact_id"].endswith(":artifact:markdown-memo")


def test_run_audit_snapshot_tracks_review_events_and_claim_status():
    intake, weather, carrier, caselaw, citecheck, query_plan = _sample_payloads()
    weather["warnings"] = ["County-specific weather corroboration is limited."]
    citecheck["checks"][0]["status"] = "uncertain"
    citecheck["summary"] = {"total": 1, "verified": 0, "uncertain": 1, "not_found": 0}

    snapshot = run_audit_snapshot_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        query_plan,
    )

    assert {event.event_type for event in snapshot.review_events} == {"warning", "citation_uncertain"}
    assert any(
        claim.claim_id == "weather-corroboration" and claim.status == "review_required"
        for claim in snapshot.memo_claims
    )
    assert any(
        claim.claim_id == "citation-check-status" and claim.status == "review_required"
        for claim in snapshot.memo_claims
    )
    assert any(
        claim.claim_id == "citation-check-status" and claim.cluster_ids == ["cluster-3"]
        for claim in snapshot.memo_claims
    )
    assert any(
        event.event_id == "weather-warning-1" and event.related_cluster_ids == ["cluster-1"]
        for event in snapshot.review_events
    )
    assert all(
        event.run_id == "run-notebook-hurricane-milton-fl-pinellas-citizens-property-insurance"
        for event in snapshot.review_events
    )
    assert all(event.target_type == "memo_claim" for event in snapshot.review_events)
    assert any(event.related_claim_ids == ["weather-corroboration"] for event in snapshot.review_events)
    assert any(
        event.event_id == "citation-uncertain" and event.related_cluster_ids == ["cluster-3"]
        for event in snapshot.review_events
    )
    assert snapshot.export_artifact.review_required is True
    assert snapshot.export_artifact.section_ids[9] == "appendix-review-log"


def test_run_audit_snapshot_scopes_citation_review_events_to_non_verified_checks():
    intake, weather, carrier, caselaw, _, query_plan = _sample_payloads()
    caselaw["issues"][0]["cases"].append(
        {
            "name": "Roe v. Ins",
            "citation": "999 So.3d 111",
            "court": "Fla. App.",
            "year": "2024",
            "one_liner": "Secondary authority only.",
            "url": "https://example.com/other-case",
            "badge": "professional",
        }
    )
    citecheck = {
        "module": "citation_verify",
        "disclaimer": "SPOT-CHECK ONLY",
        "checks": [
            {
                "badge": "verified",
                "case_name": "Doe v. Ins",
                "citation": "123 So.3d 456",
                "status": "verified",
                "note": "Found on official source",
                "source_url": "https://www.flcourts.gov/case/123",
            },
            {
                "badge": "warning",
                "case_name": "Roe v. Ins",
                "citation": "999 So.3d 111",
                "status": "uncertain",
                "note": "Found on professional source",
                "source_url": "https://casetext.com/case/roe-v-ins",
            },
        ],
        "summary": {"total": 2, "verified": 1, "uncertain": 1, "not_found": 0},
    }

    snapshot = run_audit_snapshot_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        query_plan,
    )

    citation_event = next(
        event
        for event in snapshot.review_events
        if event.event_id == "citation-uncertain"
    )
    citation_evidence_id = citation_verify_pack_to_evidence_items(citecheck)[1].evidence_id

    assert citation_event.related_evidence_ids == [citation_evidence_id]
    assert citation_event.related_cluster_ids == ["cluster-4"]
    verified_cluster = next(cluster for cluster in snapshot.evidence_clusters if cluster.cluster_id == "cluster-3")
    uncertain_cluster = next(cluster for cluster in snapshot.evidence_clusters if cluster.cluster_id == "cluster-4")
    assert verified_cluster.review_required is False
    assert uncertain_cluster.review_required is True


def test_render_markdown_memo_accepts_mixed_typed_and_dict_inputs():
    intake, weather, carrier, caselaw, citecheck, query_plan = _sample_payloads()

    markdown = render_markdown_memo(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        [query_plan[0].model_dump()],
    )

    assert "Case Intake" in markdown
    assert "Citation Spot-Check" in markdown
    assert "Citation Confidence" in markdown
    assert "Trust Snapshot" in markdown
    assert "Evidence Clusters" in markdown
    assert "Evidence Index" in markdown



def test_run_audit_snapshot_preserves_schema_version_override():
    intake, weather, carrier, caselaw, citecheck, query_plan = _sample_payloads()

    snapshot = run_audit_snapshot_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        query_plan,
        schema_version="v2alpha2",
    )

    payload = run_audit_snapshot_to_payload(snapshot)

    assert snapshot.schema_version == "v2alpha2"
    assert payload["schema_version"] == "v2alpha2"

def test_run_audit_snapshot_aggregates_retrieval_state_from_module_payloads():
    intake, weather, carrier, caselaw, citecheck, query_plan = _sample_payloads()
    weather["retrieval_tasks"] = [
        {
            "retrieval_task_id": "run-weather-1",
            "run_id": "run-milton",
            "stage_id": "run-milton:weather",
            "provider": "exa",
            "query_text": "milton weather",
            "status": "completed",
            "attempt_count": 1,
            "review_required": False,
            "raw_artifact_refs": [],
            "requested_at": None,
            "completed_at": None,
        }
    ]
    weather["run_events"] = [
        {
            "run_event_id": "run-weather-1:completed",
            "run_id": "run-milton",
            "stage_id": "run-milton:weather",
            "event_type": "retrieval_completed",
            "severity": "info",
            "message": "exa returned 1 hit.",
            "created_at": None,
            "artifact_refs": [],
        }
    ]
    carrier["retrieval_tasks"] = [
        {
            "retrieval_task_id": "run-carrier-1",
            "run_id": "run-milton",
            "stage_id": "run-milton:carrier",
            "provider": "exa",
            "query_text": "citizens claims manual",
            "status": "completed",
            "attempt_count": 1,
            "review_required": False,
            "raw_artifact_refs": [],
            "requested_at": None,
            "completed_at": None,
        }
    ]
    carrier["run_events"] = [
        {
            "run_event_id": "run-carrier-1:completed",
            "run_id": "run-milton",
            "stage_id": "run-milton:carrier",
            "event_type": "retrieval_completed",
            "severity": "info",
            "message": "exa returned 1 hit.",
            "created_at": None,
            "artifact_refs": [],
        }
    ]

    citecheck["retrieval_tasks"] = [
        {
            "retrieval_task_id": "run-cite-1",
            "run_id": "run-milton",
            "stage_id": "run-milton:citation_verify",
            "provider": "exa",
            "query_text": "Doe v. Ins 123 So.3d 456",
            "status": "completed",
            "attempt_count": 1,
            "review_required": False,
            "raw_artifact_refs": ["https://example.com/case"],
            "requested_at": None,
            "completed_at": None,
        }
    ]
    citecheck["run_events"] = [
        {
            "run_event_id": "run-cite-1:completed",
            "run_id": "run-milton",
            "stage_id": "run-milton:citation_verify",
            "event_type": "retrieval_completed",
            "severity": "info",
            "message": "exa returned 1 hit.",
            "created_at": None,
            "artifact_refs": ["https://example.com/case"],
        }
    ]

    snapshot = run_audit_snapshot_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        query_plan,
    )

    payload = run_audit_snapshot_to_payload(snapshot)

    assert len(snapshot.retrieval_tasks) == 3
    assert len(snapshot.run_events) == 3
    assert payload["retrieval_tasks"][0]["retrieval_task_id"] == "run-weather-1"
    assert payload["run_events"][2]["stage_id"] == "run-milton:citation_verify"


def test_run_audit_snapshot_tracks_duplicate_authority_counts_when_case_and_check_share_citation():
    intake, weather, carrier, caselaw, citecheck, query_plan = _sample_payloads()
    citecheck["checks"][0]["source_url"] = "https://alt.example.com/case"

    snapshot = run_audit_snapshot_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        query_plan,
    )

    assert snapshot.quality_snapshot.raw_evidence_count == 4
    assert snapshot.quality_snapshot.normalized_authority_count == 3
    assert snapshot.quality_snapshot.duplicate_authority_count == 1
    assert snapshot.quality_snapshot.provenance_link_count == 4
    assert snapshot.evidence_clusters[2].provenance_urls == ["https://example.com/case", "https://alt.example.com/case"]
