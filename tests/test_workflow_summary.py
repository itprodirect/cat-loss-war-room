"""Tests for workflow-oriented plan preview and run timeline helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from war_room.models import (
    CaseIntake,
    RunTimelineReadModel,
    adapt_run_timeline,
    run_timeline_to_payload,
)
from war_room.query_plan import build_research_plan
from war_room.workflow_summary import (
    build_run_timeline,
    build_run_timeline_read_model,
    format_research_plan_preview,
    format_run_timeline,
)


def _sample_workflow_parts():
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
    research_plan = build_research_plan(intake)
    weather = {
        "module": "weather",
        "event_summary": "Hurricane Milton - Pinellas County, FL",
        "key_observations": ["Winds of 120 mph", "Storm surge drove coastal flooding."],
        "metrics": {"max_wind_mph": 120, "storm_surge_ft": 8.0, "rain_in": None},
        "sources": [
            {
                "title": "NWS advisory",
                "url": "https://weather.gov/milton",
                "badge": "official",
                "reason": "Official source",
            }
        ],
        "retrieval_tasks": [
            {
                "retrieval_task_id": "run-milton:weather:damage_report",
                "run_id": research_plan.run_id,
                "stage_id": f"{research_plan.run_id}:weather",
                "provider": "exa",
                "query_text": "milton pinellas weather",
                "status": "completed",
                "attempt_count": 1,
                "requested_at": None,
                "completed_at": None,
                "raw_artifact_refs": ["https://weather.gov/milton"],
                "review_required": False,
            }
        ],
    }
    carrier = {
        "module": "carrier",
        "carrier_snapshot": {
            "name": "Citizens Property Insurance",
            "state": "FL",
            "event": "Hurricane Milton",
            "policy_type": "HO-3 Dwelling",
        },
        "document_pack": [
            {
                "doc_type": "Claims Manual",
                "title": "Wind claim manual",
                "url": "https://example.com/manual",
                "badge": "professional",
                "why_it_matters": "Shows internal handling expectations.",
            }
        ],
        "common_defenses": ["Pre-existing damage"],
        "rebuttal_angles": ["Storm timeline aligns with the reported loss date."],
        "sources": [
            {
                "title": "Claims manual",
                "url": "https://example.com/manual",
                "badge": "professional",
                "reason": "Professional source",
            }
        ],
        "retrieval_tasks": [
            {
                "retrieval_task_id": "run-milton:carrier:claims_manual",
                "run_id": research_plan.run_id,
                "stage_id": f"{research_plan.run_id}:carrier",
                "provider": "exa",
                "query_text": "citizens claims manual",
                "status": "completed",
                "attempt_count": 1,
                "requested_at": None,
                "completed_at": None,
                "raw_artifact_refs": ["https://example.com/manual"],
                "review_required": False,
            }
        ],
    }
    caselaw = {
        "module": "caselaw",
        "issues": [
            {
                "issue": "Wind vs Water Causation",
                "cases": [
                    {
                        "name": "Doe v. Ins.",
                        "citation": "123 So.3d 456",
                        "court": "Fla. App.",
                        "year": "2023",
                        "one_liner": "Specific wind evidence supported coverage.",
                        "url": "https://example.com/case",
                        "badge": "professional",
                    }
                ],
                "notes": ["Use for concurrent-causation framing."],
            }
        ],
        "sources": [
            {
                "title": "Case digest",
                "url": "https://example.com/case",
                "badge": "professional",
                "reason": "Professional source",
            }
        ],
        "retrieval_tasks": [
            {
                "retrieval_task_id": "run-milton:caselaw:coverage_law",
                "run_id": research_plan.run_id,
                "stage_id": f"{research_plan.run_id}:caselaw",
                "provider": "exa",
                "query_text": "milton coverage law",
                "status": "completed",
                "attempt_count": 1,
                "requested_at": None,
                "completed_at": None,
                "raw_artifact_refs": ["https://example.com/case"],
                "review_required": False,
            }
        ],
    }
    citecheck = {
        "module": "citation_verify",
        "disclaimer": "SPOT-CHECK ONLY",
        "checks": [
            {
                "badge": "verified",
                "case_name": "Doe v. Ins.",
                "citation": "123 So.3d 456",
                "status": "verified",
                "note": "Found on reviewed source",
                "source_url": "https://example.com/case",
            }
        ],
        "summary": {"total": 1, "verified": 1, "uncertain": 0, "not_found": 0},
        "retrieval_tasks": [
            {
                "retrieval_task_id": "run-milton:citation_verify:doe",
                "run_id": research_plan.run_id,
                "stage_id": f"{research_plan.run_id}:citation_verify",
                "provider": "exa",
                "query_text": "Doe v. Ins. 123 So.3d 456",
                "status": "completed",
                "attempt_count": 1,
                "requested_at": None,
                "completed_at": None,
                "raw_artifact_refs": ["https://example.com/case"],
                "review_required": False,
            }
        ],
    }
    return intake, research_plan, weather, carrier, caselaw, citecheck


def test_format_research_plan_preview_surfaces_scope_modules_and_domains():
    intake, research_plan, *_ = _sample_workflow_parts()

    preview = format_research_plan_preview(research_plan)

    assert research_plan.plan_id in preview
    assert research_plan.run_id in preview
    assert "RESEARCH PLAN PREVIEW" in preview
    assert "Weather" in preview
    assert "Carrier Documents" in preview
    assert intake.coverage_issues[0] in preview


def test_build_run_timeline_marks_review_required_when_citations_are_uncertain():
    intake, research_plan, weather, carrier, caselaw, citecheck = _sample_workflow_parts()
    citecheck["checks"][0]["status"] = "uncertain"
    citecheck["summary"] = {"total": 1, "verified": 0, "uncertain": 1, "not_found": 0}

    run, stages = build_run_timeline(
        intake,
        research_plan,
        weather,
        carrier,
        caselaw,
        citecheck,
        environment="notebook",
        export_written=True,
    )

    citation_stage = next(stage for stage in stages if stage.stage_key == "citation_verify")
    export_stage = next(stage for stage in stages if stage.stage_key == "export")

    assert run.status == "completed"
    assert run.review_required is True
    assert citation_stage.status == "degraded"
    assert citation_stage.review_required is True
    assert export_stage.status == "completed"


def test_build_run_timeline_marks_partial_success_when_module_output_is_missing():
    intake, research_plan, weather, carrier, caselaw, citecheck = _sample_workflow_parts()
    weather["sources"] = []
    weather["retrieval_tasks"][0]["status"] = "failed"
    weather["retrieval_tasks"][0]["review_required"] = True

    run, stages = build_run_timeline(
        intake,
        research_plan,
        weather,
        carrier,
        caselaw,
        citecheck,
        environment="preflight",
        export_written=False,
    )

    weather_stage = next(stage for stage in stages if stage.stage_key == "weather")

    assert run.status == "partial_success"
    assert weather_stage.status == "failed"
    assert weather_stage.review_required is True


def test_format_run_timeline_includes_stage_summary_and_next_step():
    intake, research_plan, weather, carrier, caselaw, citecheck = _sample_workflow_parts()
    citecheck["checks"][0]["status"] = "uncertain"
    citecheck["summary"] = {"total": 1, "verified": 0, "uncertain": 1, "not_found": 0}
    run, stages = build_run_timeline(
        intake,
        research_plan,
        weather,
        carrier,
        caselaw,
        citecheck,
    )

    timeline = format_run_timeline(run, stages)

    assert "RUN TIMELINE" in timeline
    assert "Stage Summary:" in timeline
    assert "Move into evidence review before relying on memo language." in timeline
    assert "[degraded] Citation Spot-Check" in timeline


def test_run_timeline_payload_round_trips_with_schema_version():
    timeline = build_run_timeline_read_model(
        *_sample_workflow_parts(),
        environment="notebook",
        export_written=True,
    )

    payload = run_timeline_to_payload(timeline)
    restored = adapt_run_timeline(payload)
    rendered = format_run_timeline(payload)

    assert isinstance(timeline, RunTimelineReadModel)
    assert payload["schema_version"] == "v2alpha1"
    assert restored.run.run_id == timeline.run.run_id
    assert len(restored.stages) == len(timeline.stages)
    assert "RUN TIMELINE" in rendered


def test_run_timeline_contract_rejects_stage_from_another_run():
    timeline = build_run_timeline_read_model(
        *_sample_workflow_parts(),
        environment="notebook",
        export_written=True,
    )
    payload = run_timeline_to_payload(timeline)
    payload["stages"][0]["run_id"] = "wrong-run"

    with pytest.raises(ValidationError):
        adapt_run_timeline(payload)
