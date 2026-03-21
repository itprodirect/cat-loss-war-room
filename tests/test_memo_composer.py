"""Tests for memo-composer read model helpers."""

from __future__ import annotations

from war_room.memo_composer import (
    build_memo_composer,
    build_memo_composer_from_parts,
    format_memo_composer,
)
from war_room.models import CaseIntake, QuerySpec, run_audit_snapshot_from_parts


def _sample_parts():
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
        "warnings": ["County-specific weather corroboration is limited."],
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
                "doc_type": "Claims Manual",
                "title": "Manual",
                "url": "https://example.com/manual",
                "badge": "professional",
                "why_it_matters": "Relevant",
            }
        ],
        "common_defenses": ["Pre-existing damage"],
        "rebuttal_angles": ["Timeline contradicts carrier position"],
        "sources": [
            {
                "title": "Manual",
                "url": "https://example.com/manual",
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
                "badge": "uncertain",
                "case_name": "Doe v. Ins",
                "citation": "123 So.3d 456",
                "status": "uncertain",
                "note": "Found on reviewable source",
                "source_url": "https://example.com/case",
            }
        ],
        "summary": {"total": 1, "verified": 0, "uncertain": 1, "not_found": 0},
    }
    query_plan = [QuerySpec(module="weather", query="test query", category="test")]
    return intake, weather, carrier, caselaw, citecheck, query_plan


def test_build_memo_composer_links_claims_to_sections_and_export_state():
    intake, weather, carrier, caselaw, citecheck, query_plan = _sample_parts()
    snapshot = run_audit_snapshot_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        query_plan,
    )

    composer = build_memo_composer(snapshot)

    assert composer.export_eligibility == "review_required_export"
    assert composer.review_required_section_count > 0
    weather_section = next(card for card in composer.section_cards if card.title == "Weather Corroboration")
    assert weather_section.review_required is True
    assert weather_section.claim_links
    assert weather_section.review_event_ids


def test_build_memo_composer_from_parts_matches_snapshot_builder():
    intake, weather, carrier, caselaw, citecheck, query_plan = _sample_parts()

    from_parts = build_memo_composer_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        query_plan,
    )
    from_snapshot = build_memo_composer(
        run_audit_snapshot_from_parts(
            intake,
            weather,
            carrier,
            caselaw,
            citecheck,
            query_plan,
        )
    )

    assert len(from_parts.section_cards) == len(from_snapshot.section_cards)
    assert from_parts.export_eligibility == from_snapshot.export_eligibility
    assert from_parts.review_required_section_count == from_snapshot.review_required_section_count


def test_format_memo_composer_surfaces_section_status_and_export_eligibility():
    composer = build_memo_composer_from_parts(*_sample_parts())

    rendered = format_memo_composer(composer)

    assert "MEMO COMPOSER" in rendered
    assert "Export Eligibility: review_required_export" in rendered
    assert "[review_required] Weather Corroboration" in rendered
    assert "Claims:" in rendered
