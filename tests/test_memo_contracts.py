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
    assert payload["evidence_items"][0]["evidence_id"] == "weather-source-1"
    assert payload["evidence_clusters"][0]["cluster_id"] == "cluster-1"
    assert payload["evidence_clusters"][2]["cluster_type"] == "citation"
    assert snapshot.memo_claims[0].cluster_ids == ["cluster-1"]
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

    citation_event = next(event for event in snapshot.review_events if event.event_id == "citation-uncertain")

    assert citation_event.related_evidence_ids == ["citation-check-2"]
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
