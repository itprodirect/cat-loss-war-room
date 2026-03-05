"""Tests for typed citation/export contracts (issue #6 slice 3)."""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from war_room.export_md import render_markdown_memo
from war_room.models import (
    CaseIntake,
    QuerySpec,
    adapt_citation_verify_pack,
    citation_verify_pack_to_payload,
    memo_render_input_from_parts,
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

    query_plan = [
        QuerySpec(module="weather", query="test query", category="test"),
    ]

    return intake, weather, carrier, caselaw, citecheck, query_plan


def test_citation_verify_pack_adapter_round_trip():
    _, _, _, _, citecheck, _ = _sample_payloads()

    typed = adapt_citation_verify_pack(citecheck)
    dumped = citation_verify_pack_to_payload(typed)

    assert typed.module == "citation_verify"
    assert dumped["summary"]["total"] == 1


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

    assert memo_input.intake.event_name == "Hurricane Milton"
    assert memo_input.citecheck.summary.verified == 1
    assert memo_input.query_plan[0].module == "weather"


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
    assert "Summary:" in markdown
