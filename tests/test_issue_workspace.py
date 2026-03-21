"""Tests for issue-workspace read model helpers."""

from __future__ import annotations

from war_room.issue_workspace import (
    build_issue_workspace,
    build_issue_workspace_from_parts,
    format_issue_workspace,
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
        posture=["denial", "bad_faith"],
        coverage_issues=["wind vs water causation", "scope of repair"],
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
                "issue": "wind vs water causation",
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
            },
            {
                "issue": "scope of repair",
                "cases": [
                    {
                        "name": "Smith v. Carrier",
                        "citation": "321 So.3d 654",
                        "court": "Fla. App.",
                        "year": "2022",
                        "one_liner": "Reasonable matching scope was required.",
                        "url": "https://example.com/scope",
                        "badge": "professional",
                    }
                ],
                "notes": ["Matching analysis."],
            },
        ],
        "sources": [
            {
                "title": "Case",
                "url": "https://example.com/case",
                "badge": "professional",
                "reason": "Professional source",
            },
            {
                "title": "Case",
                "url": "https://example.com/scope",
                "badge": "professional",
                "reason": "Professional source",
            },
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
            },
            {
                "badge": "verified",
                "case_name": "Smith v. Carrier",
                "citation": "321 So.3d 654",
                "status": "verified",
                "note": "Found on reviewed source",
                "source_url": "https://example.com/scope",
            },
        ],
        "summary": {"total": 2, "verified": 1, "uncertain": 1, "not_found": 0},
    }
    query_plan = [QuerySpec(module="weather", query="test query", category="test")]
    return intake, weather, carrier, caselaw, citecheck, query_plan


def test_build_issue_workspace_links_clusters_claims_and_citation_outcomes():
    intake, weather, carrier, caselaw, citecheck, query_plan = _sample_parts()
    snapshot = run_audit_snapshot_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        query_plan,
    )

    workspace = build_issue_workspace(snapshot)

    assert len(workspace.issue_cards) == 2
    assert workspace.review_required_issue_count == 2
    first_card = workspace.issue_cards[0]
    assert first_card.issue_label == "scope of repair"
    assert first_card.review_required is True
    assert first_card.evidence_cluster_ids
    assert first_card.case_candidates
    assert first_card.citation_outcomes[0].status == "verified"


def test_build_issue_workspace_from_parts_matches_snapshot_builder():
    intake, weather, carrier, caselaw, citecheck, query_plan = _sample_parts()

    from_parts = build_issue_workspace_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        query_plan,
    )
    from_snapshot = build_issue_workspace(
        run_audit_snapshot_from_parts(
            intake,
            weather,
            carrier,
            caselaw,
            citecheck,
            query_plan,
        )
    )

    assert len(from_parts.issue_cards) == len(from_snapshot.issue_cards)
    assert from_parts.review_required_issue_count == from_snapshot.review_required_issue_count
    assert from_parts.issue_cards[0].issue_label == from_snapshot.issue_cards[0].issue_label


def test_format_issue_workspace_surfaces_issue_status_and_authorities():
    workspace = build_issue_workspace_from_parts(*_sample_parts())

    rendered = format_issue_workspace(workspace)

    assert "ISSUE WORKSPACE" in rendered
    assert "Review Required:   2 issues" in rendered
    assert "[review_required] wind vs water causation" in rendered
    assert "[review_required] scope of repair" in rendered
    assert "Strongest authorities:" in rendered
    assert "Citation outcomes:" in rendered
