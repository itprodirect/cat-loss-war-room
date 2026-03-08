"""Tests for typed citation/export contracts (issue #6 slice 3)."""

import pytest
from pydantic import ValidationError

from war_room.export_md import render_markdown_memo
from war_room.models import (
    CaseIntake,
    QuerySpec,
    adapt_citation_verify_pack,
    citation_verify_pack_to_payload,
    memo_render_input_from_parts,
    run_audit_snapshot_from_parts,
    run_audit_snapshot_to_payload,
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

    assert memo_input.schema_version == "v2alpha1"
    assert memo_input.intake.event_name == "Hurricane Milton"
    assert memo_input.citecheck.summary.verified == 1
    assert memo_input.query_plan[0].module == "weather"


def test_run_audit_snapshot_builds_canonical_entities():
    intake, weather, carrier, caselaw, citecheck, query_plan = _sample_payloads()

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
    assert snapshot.schema_version == "v2alpha1"
    assert snapshot.export_artifact.artifact_type == "markdown_memo"
    assert "Appendix: Evidence Clusters" in snapshot.export_artifact.section_titles
    assert "Appendix: Evidence Index" in snapshot.export_artifact.section_titles
    assert payload["schema_version"] == "v2alpha1"
    assert payload["evidence_items"][0]["evidence_id"] == "weather-source-1"
    assert payload["evidence_clusters"][0]["cluster_id"] == "cluster-1"
    assert payload["evidence_clusters"][2]["cluster_type"] == "citation"
    assert snapshot.memo_claims[0].cluster_ids == ["cluster-1"]
    assert snapshot.memo_claims[2].cluster_ids == ["cluster-3"]
    assert payload["memo_claims"][3]["cluster_ids"] == ["cluster-3"]


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
    assert any(
        event.event_id == "citation-uncertain" and event.related_cluster_ids == ["cluster-3"]
        for event in snapshot.review_events
    )


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
