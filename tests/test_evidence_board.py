"""Tests for evidence-board read model helpers."""

from __future__ import annotations

from war_room.models import CaseIntake, QuerySpec, run_audit_snapshot_from_parts
from war_room.evidence_board import (
    build_evidence_board,
    build_evidence_board_from_parts,
    format_evidence_board,
)


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


def test_build_evidence_board_links_claims_and_review_events_to_clusters():
    intake, weather, carrier, caselaw, citecheck, query_plan = _sample_parts()
    snapshot = run_audit_snapshot_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        query_plan,
    )

    board = build_evidence_board(snapshot)

    assert board.total_clusters == 3
    assert board.review_required_clusters == 2
    first_card = board.cluster_cards[0]
    assert first_card.review_required is True
    assert first_card.review_event_ids
    assert first_card.claim_ids
    assert first_card.evidence_previews


def test_build_evidence_board_from_parts_matches_snapshot_builder():
    intake, weather, carrier, caselaw, citecheck, query_plan = _sample_parts()

    from_parts = build_evidence_board_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        query_plan,
    )
    from_snapshot = build_evidence_board(
        run_audit_snapshot_from_parts(
            intake,
            weather,
            carrier,
            caselaw,
            citecheck,
            query_plan,
        )
    )

    assert from_parts.total_clusters == from_snapshot.total_clusters
    assert from_parts.review_required_clusters == from_snapshot.review_required_clusters
    assert from_parts.cluster_cards[0].cluster_id == from_snapshot.cluster_cards[0].cluster_id


def test_format_evidence_board_surfaces_review_required_clusters():
    board = build_evidence_board_from_parts(*_sample_parts())

    rendered = format_evidence_board(board)

    assert "EVIDENCE BOARD" in rendered
    assert "Review Required:   2 clusters" in rendered
    assert "[review_required]" in rendered
    assert "Claims:" in rendered
    assert "Review events:" in rendered


def test_build_evidence_board_keeps_verified_citation_cluster_ready_when_only_peer_citations_are_uncertain():
    intake, weather, carrier, caselaw, _, query_plan = _sample_parts()
    weather.pop("warnings")
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

    board = build_evidence_board_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        query_plan,
    )

    verified_card = next(card for card in board.cluster_cards if card.label == "123 so. 3d 456")
    uncertain_card = next(card for card in board.cluster_cards if card.label == "999 so. 3d 111")

    assert verified_card.review_required is False
    assert verified_card.review_event_ids == []
    assert uncertain_card.review_required is True
    assert uncertain_card.review_event_ids == ["citation-uncertain"]
