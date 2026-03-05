"""Tests for typed Weather/Carrier/CaseLaw pack adapters."""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from war_room.models import (
    adapt_caselaw_pack,
    adapt_carrier_doc_pack,
    adapt_weather_brief,
    caselaw_pack_to_payload,
    carrier_doc_pack_to_payload,
    weather_brief_to_payload,
)


def test_weather_brief_adapter_round_trip_without_warnings_key():
    payload = {
        "module": "weather",
        "event_summary": "Hurricane Milton - Pinellas County, FL (2024-10-09)",
        "key_observations": ["Winds reached 120 mph"],
        "metrics": {"max_wind_mph": 120, "storm_surge_ft": None, "rain_in": None},
        "sources": [
            {
                "title": "NWS report",
                "url": "https://weather.gov/report",
                "badge": "official",
                "reason": "Official source",
            }
        ],
    }

    typed = adapt_weather_brief(payload)
    out = weather_brief_to_payload(typed)

    assert typed.module == "weather"
    assert "warnings" not in out
    assert out["metrics"]["storm_surge_ft"] is None


def test_weather_brief_adapter_keeps_warnings_when_present():
    payload = {
        "module": "weather",
        "event_summary": "Hurricane Milton - Pinellas County, FL (2024-10-09)",
        "key_observations": [],
        "metrics": {"max_wind_mph": None, "storm_surge_ft": None, "rain_in": None},
        "sources": [],
        "warnings": ["No Exa client available."],
    }

    out = weather_brief_to_payload(payload)

    assert out["warnings"] == ["No Exa client available."]


def test_carrier_doc_pack_adapter_round_trip():
    payload = {
        "module": "carrier",
        "carrier_snapshot": {
            "name": "Citizens Property Insurance",
            "state": "FL",
            "event": "Hurricane Milton",
            "policy_type": "HO-3 Dwelling",
        },
        "document_pack": [
            {
                "doc_type": "Denial Pattern Analysis",
                "title": "Milton denial trends",
                "url": "https://example.com/denials",
                "badge": "professional",
                "why_it_matters": "Supports denial-pattern context.",
            }
        ],
        "common_defenses": ["Wear and tear / maintenance exclusion defense"],
        "rebuttal_angles": ["Damage timeline tracks event date."],
        "sources": [
            {
                "title": "Article",
                "url": "https://example.com/article",
                "badge": "professional",
                "reason": "Professional source",
            }
        ],
    }

    typed = adapt_carrier_doc_pack(payload)
    out = carrier_doc_pack_to_payload(typed)

    assert typed.module == "carrier"
    assert out["carrier_snapshot"]["name"] == "Citizens Property Insurance"


def test_caselaw_pack_adapter_round_trip():
    payload = {
        "module": "caselaw",
        "issues": [
            {
                "issue": "Coverage / Denial Law",
                "cases": [
                    {
                        "name": "Smith v. Carrier",
                        "citation": "123 So. 3d 456",
                        "court": "Fla. App.",
                        "year": "2023",
                        "one_liner": "Coverage found for wind-driven loss.",
                        "url": "https://scholar.google.com/case1",
                        "badge": "professional",
                    }
                ],
                "notes": ["Review applicability to intake posture."],
            }
        ],
        "sources": [
            {
                "title": "Case",
                "url": "https://scholar.google.com/case1",
                "badge": "professional",
                "reason": "Legal source",
            }
        ],
    }

    typed = adapt_caselaw_pack(payload)
    out = caselaw_pack_to_payload(typed)

    assert typed.module == "caselaw"
    assert out["issues"][0]["cases"][0]["name"] == "Smith v. Carrier"


def test_adapter_rejects_missing_required_source_fields():
    payload = {
        "module": "weather",
        "event_summary": "Summary",
        "key_observations": [],
        "metrics": {"max_wind_mph": None, "storm_surge_ft": None, "rain_in": None},
        "sources": [{"title": "No badge", "url": "https://example.com"}],
    }

    with pytest.raises(ValidationError):
        adapt_weather_brief(payload)
