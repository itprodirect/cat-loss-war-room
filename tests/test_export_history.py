"""Tests for export-history read model helpers."""

from __future__ import annotations

from war_room.export_history import (
    build_export_history,
    build_export_history_from_parts,
    format_export_history,
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


def test_build_export_history_tracks_delivery_state_and_run_status():
    intake, weather, carrier, caselaw, citecheck, query_plan = _sample_parts()
    snapshot = run_audit_snapshot_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        query_plan,
    )

    history = build_export_history(
        snapshot,
        run_status="completed",
        export_written=False,
    )

    assert len(history.entries) == 1
    assert history.review_required_export_count == 1
    assert history.entries[0].delivery_state == "not_written"
    assert history.entries[0].run_status == "completed"
    assert history.entries[0].disclaimer_present is True


def test_build_export_history_from_parts_honors_written_uri_override():
    history = build_export_history_from_parts(
        *_sample_parts(),
        run_status="completed",
        export_written=True,
        artifact_uri="output/demo.md",
    )

    assert history.entries[0].delivery_state == "written"
    assert history.entries[0].artifact_uri == "output/demo.md"


def test_format_export_history_surfaces_artifact_and_audit_pointer():
    history = build_export_history_from_parts(
        *_sample_parts(),
        run_status="completed",
        export_written=True,
        artifact_uri="output/demo.md",
    )

    rendered = format_export_history(history)

    assert "EXPORT HISTORY" in rendered
    assert "[written] markdown_memo | review_required" in rendered
    assert "Run status: completed" in rendered
    assert "Audit ref:" in rendered
