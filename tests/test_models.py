"""Tests for Pydantic domain models introduced in issue #6."""

import pytest
from pydantic import ValidationError

from war_room.models import (
    CaseIntake,
    MemoSection,
    QuerySpec,
    ResearchPlan,
    Run,
    RunStage,
    adapt_query_plan,
    case_intake_to_payload,
    memo_section_to_payload,
    query_plan_to_payloads,
    query_spec_to_payload,
    research_plan_to_payload,
    run_stage_to_payload,
    run_to_payload,
)


def test_case_intake_round_trip_dump_and_validate():
    intake = CaseIntake(
        event_name="Hurricane Milton",
        event_date="2024-10-09",
        state="FL",
        county="Pinellas",
        carrier="Citizens Property Insurance",
        policy_type="HO-3 Dwelling",
        posture=["denial", "bad_faith"],
        key_facts=["Roof damage"],
        coverage_issues=["wind_vs_water_causation"],
    )

    payload = intake.model_dump()
    reloaded = CaseIntake.model_validate(payload)

    assert reloaded == intake


def test_case_intake_payload_helper_normalizes_model():
    intake = CaseIntake(
        event_name="Hurricane Milton",
        event_date="2024-10-09",
        state="FL",
        county="Pinellas",
        carrier="Citizens Property Insurance",
        policy_type="HO-3 Dwelling",
    )

    payload = case_intake_to_payload(intake)

    assert payload["event_name"] == "Hurricane Milton"
    assert payload["posture"] == ["denial"]


def test_case_intake_rejects_invalid_date():
    with pytest.raises(ValidationError, match="YYYY-MM-DD"):
        CaseIntake(
            event_name="Hurricane Milton",
            event_date="10/09/2024",
            state="FL",
            county="Pinellas",
            carrier="Citizens Property Insurance",
            policy_type="HO-3 Dwelling",
        )


def test_case_intake_rejects_unknown_field():
    with pytest.raises(ValidationError):
        CaseIntake.model_validate(
            {
                "event_name": "Hurricane Milton",
                "event_date": "2024-10-09",
                "state": "FL",
                "county": "Pinellas",
                "carrier": "Citizens Property Insurance",
                "policy_type": "HO-3 Dwelling",
                "unknown_field": "x",
            }
        )


def test_query_spec_format_row_includes_dates_and_domains():
    spec = QuerySpec(
        module="weather",
        query="milton pinellas weather",
        category="damage_report",
        date_start="2024-10-09",
        date_end="2024-10-10",
        preferred_domains=["weather.gov"],
    )

    row = spec.format_row()
    assert "[damage_report]" in row
    assert "2024-10-09" in row and "2024-10-10" in row
    assert "weather.gov" in row


def test_query_plan_adapters_accept_mixed_shapes():
    spec = QuerySpec(module="weather", query="storm report", category="damage_report")

    typed = adapt_query_plan([spec.model_dump(), spec])
    payloads = query_plan_to_payloads(typed)

    assert [item.module for item in typed] == ["weather", "weather"]
    assert payloads[0]["query"] == "storm report"


def test_query_spec_payload_helper_normalizes_model():
    spec = QuerySpec(module="weather", query="storm report", category="damage_report")

    payload = query_spec_to_payload(spec)

    assert payload["module"] == "weather"
    assert payload["query"] == "storm report"


def test_research_plan_payload_helper_tracks_schema_version_and_queries():
    plan = ResearchPlan(
        plan_id="plan-milton",
        run_id="run-milton",
        planned_modules=["weather", "caselaw"],
        issue_hypotheses=["wind_vs_water_causation"],
        query_plan=[QuerySpec(module="weather", query="milton pinellas", category="damage_report")],
        preferred_domains=["weather.gov", "courtlistener.com"],
        estimated_scope="standard",
    )

    payload = research_plan_to_payload(plan)

    assert payload["schema_version"] == "v2alpha1"
    assert payload["query_plan"][0]["module"] == "weather"


def test_run_payload_helper_normalizes_status_and_schema_version():
    run = Run(
        run_id="run-milton",
        environment="local",
        status="running",
        intake_id="intake-milton",
        plan_id="plan-milton",
    )

    payload = run_to_payload(run)

    assert payload["schema_version"] == "v2alpha1"
    assert payload["status"] == "running"


def test_run_rejects_blank_schema_version():
    with pytest.raises(ValidationError, match="schema_version"):
        Run(
            run_id="run-milton",
            environment="local",
            schema_version="   ",
        )


def test_run_stage_and_memo_section_payload_helpers_validate_contracts():
    stage = RunStage(
        stage_id="run-milton:weather",
        run_id="run-milton",
        stage_key="weather",
        status="degraded",
        summary="Used fallback sources",
    )
    section = MemoSection(
        section_id="section-weather",
        run_id="run-milton",
        title="Weather Corroboration",
        status="review_required",
        issue_ids=["issue-wind"],
        claim_ids=["claim-weather"],
        review_required=True,
    )

    stage_payload = run_stage_to_payload(stage)
    section_payload = memo_section_to_payload(section)

    assert stage_payload["stage_key"] == "weather"
    assert stage_payload["status"] == "degraded"
    assert section_payload["status"] == "review_required"
    assert section_payload["issue_ids"] == ["issue-wind"]
