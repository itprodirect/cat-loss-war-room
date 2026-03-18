"""Tests for Pydantic domain models introduced in issue #6."""

import pytest
from pydantic import ValidationError

from war_room.models import (
    CaseCandidate,
    CaseIntake,
    ExportArtifact,
    LegalIssue,
    MemoSection,
    QuerySpec,
    ResearchPlan,
    RetrievalTask,
    Run,
    RunEvent,
    RunStage,
    ReviewEvent,
    adapt_query_plan,
    case_candidate_to_payload,
    case_intake_to_payload,
    legal_issue_to_payload,
    memo_section_to_payload,
    query_plan_to_payloads,
    query_spec_to_payload,
    retrieval_task_to_payload,
    research_plan_to_payload,
    run_event_to_payload,
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


def test_legal_issue_and_case_candidate_payload_helpers_validate_contracts():
    issue = LegalIssue(
        issue_id="issue-wind",
        run_id="run-milton",
        label="Wind vs. water causation",
        summary="Need county-specific wind evidence and matching authority.",
        status="review_required",
        evidence_cluster_ids=["cluster-weather", "cluster-case"],
        case_candidate_ids=["case-doe"],
        review_required=True,
    )
    candidate = CaseCandidate(
        case_candidate_id="case-doe",
        run_id="run-milton",
        issue_id="issue-wind",
        name="Doe v. Ins",
        citation="123 So.3d 456",
        court="Fla. App.",
        year="2023",
        url="https://example.com/case",
        source_tier="professional",
        summary="Coverage upheld where wind damage evidence was specific.",
    )

    issue_payload = legal_issue_to_payload(issue)
    candidate_payload = case_candidate_to_payload(candidate)

    assert issue_payload["status"] == "review_required"
    assert issue_payload["evidence_cluster_ids"] == ["cluster-weather", "cluster-case"]
    assert candidate_payload["case_candidate_id"] == "case-doe"
    assert candidate_payload["source_tier"] == "professional"


def test_legal_issue_rejects_blank_related_ids():
    with pytest.raises(ValidationError, match="evidence_cluster_ids"):
        LegalIssue(
            issue_id="issue-wind",
            run_id="run-milton",
            label="Wind vs. water causation",
            evidence_cluster_ids=[""],
        )


def test_run_event_and_retrieval_task_payload_helpers_validate_contracts():
    event = RunEvent(
        run_event_id="event-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        event_type="retry_scheduled",
        severity="warning",
        message="Weather retrieval retried after timeout.",
        artifact_refs=["artifact-log-1"],
    )
    task = RetrievalTask(
        retrieval_task_id="task-weather-1",
        run_id="run-milton",
        stage_id="run-milton:weather",
        provider="exa",
        query_text="milton pinellas weather.gov",
        status="degraded",
        attempt_count=2,
        raw_artifact_refs=["raw-search-1"],
        review_required=True,
    )

    event_payload = run_event_to_payload(event)
    task_payload = retrieval_task_to_payload(task)

    assert event_payload["severity"] == "warning"
    assert event_payload["artifact_refs"] == ["artifact-log-1"]
    assert task_payload["status"] == "degraded"
    assert task_payload["raw_artifact_refs"] == ["raw-search-1"]


def test_review_event_and_export_artifact_capture_graph_linkage_fields():
    review_event = ReviewEvent(
        event_id="event-1",
        run_id="run-milton",
        event_type="warning",
        label="Weather review required",
        detail="County-specific weather corroboration is limited.",
        module="weather",
        target_type="memo_claim",
        target_ids=["weather-corroboration"],
        related_evidence_ids=["weather-source-1"],
        related_cluster_ids=["cluster-1"],
        related_claim_ids=["weather-corroboration"],
        related_stage_id="run-milton:weather",
    )
    artifact = ExportArtifact(
        artifact_id="run-milton:artifact:markdown-memo",
        run_id="run-milton",
        title="CAT-Loss War Room - Research Memo",
        disclaimer="DEMO RESEARCH MEMO - VERIFY CITATIONS - NOT LEGAL ADVICE",
        uri="runs/run-milton/research-memo.md",
        section_ids=["trust-snapshot", "case-intake"],
        review_required=True,
        section_titles=["Trust Snapshot", "Case Intake"],
    )

    assert review_event.run_id == "run-milton"
    assert review_event.target_type == "memo_claim"
    assert review_event.related_claim_ids == ["weather-corroboration"]
    assert review_event.related_stage_id == "run-milton:weather"
    assert artifact.artifact_id == "run-milton:artifact:markdown-memo"
    assert artifact.run_id == "run-milton"
    assert artifact.section_ids == ["trust-snapshot", "case-intake"]
    assert artifact.review_required is True


def test_run_event_rejects_blank_artifact_refs():
    with pytest.raises(ValidationError, match="artifact_refs"):
        RunEvent(
            run_event_id="event-1",
            run_id="run-milton",
            event_type="retry_scheduled",
            message="Weather retrieval retried after timeout.",
            artifact_refs=[""],
        )


def test_retrieval_task_rejects_blank_artifact_refs():
    with pytest.raises(ValidationError, match="raw_artifact_refs"):
        RetrievalTask(
            retrieval_task_id="task-weather-1",
            run_id="run-milton",
            stage_id="run-milton:weather",
            provider="exa",
            query_text="milton pinellas weather.gov",
            raw_artifact_refs=[""],
        )
