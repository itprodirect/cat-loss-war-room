"""Tests for the minimal V2 orchestration run-state contract."""

from __future__ import annotations

import pytest

from war_room.models import RunStage
from war_room.orchestration import (
    RUN_STATES,
    STAGE_KEYS,
    STAGE_STATUSES,
    InvalidStateTransitionError,
    StageStateSnapshot,
    UnknownRunStateError,
    UnknownStageStateError,
    derive_run_status_from_stages,
    is_terminal_run_status,
    is_terminal_stage_status,
    normalize_stage_state,
    run_requires_review,
    validate_run_transition,
    validate_stage_transition,
)


def test_canonical_state_contract_includes_v2_run_stage_values():
    assert RUN_STATES == (
        "queued",
        "running",
        "partial_success",
        "failed",
        "completed",
        "cancelled",
    )
    assert STAGE_STATUSES == (
        "not_started",
        "in_progress",
        "completed",
        "degraded",
        "failed",
        "skipped",
    )
    assert STAGE_KEYS == (
        "intake_validation",
        "research_plan",
        "weather",
        "carrier",
        "caselaw",
        "citation_verify",
        "memo_assembly",
        "export",
    )


def test_run_state_transitions_accept_valid_forward_paths():
    assert validate_run_transition("queued", "running") == "running"
    assert validate_run_transition("running", "completed") == "completed"
    assert validate_run_transition("running", "partial_success") == "partial_success"
    assert validate_run_transition("running", "failed") == "failed"
    assert validate_run_transition("completed", "completed") == "completed"
    assert is_terminal_run_status("partial_success") is True


def test_run_state_transitions_reject_unknown_or_terminal_reopen_paths():
    with pytest.raises(InvalidStateTransitionError, match="completed"):
        validate_run_transition("completed", "running")

    with pytest.raises(InvalidStateTransitionError, match="running"):
        validate_run_transition("running", "queued")

    with pytest.raises(UnknownRunStateError, match="mystery"):
        validate_run_transition("mystery", "running")


def test_stage_state_transitions_accept_valid_paths_and_terminal_repeats():
    assert validate_stage_transition("not_started", "in_progress") == "in_progress"
    assert validate_stage_transition("in_progress", "degraded") == "degraded"
    assert validate_stage_transition("not_started", "skipped") == "skipped"
    assert validate_stage_transition("failed", "failed") == "failed"


def test_stage_state_transitions_reject_unknown_or_terminal_reopen_paths():
    with pytest.raises(InvalidStateTransitionError, match="failed"):
        validate_stage_transition("failed", "in_progress")

    with pytest.raises(UnknownStageStateError, match="unknown"):
        validate_stage_transition("unknown", "completed")


def test_stage_status_snapshot_normalizes_current_run_stage_records():
    stage = RunStage(
        stage_id="run-milton:weather",
        run_id="run-milton",
        stage_key="weather",
        status="degraded",
        review_required=True,
    )
    normalized = normalize_stage_state(stage)
    from_mapping = normalize_stage_state(
        {"stage_key": "carrier", "status": "completed", "review_required": False}
    )

    assert normalized == StageStateSnapshot(
        stage_key="weather",
        status="degraded",
        review_required=True,
    )
    assert from_mapping.stage_key == "carrier"
    assert from_mapping.status == "completed"


def test_stage_status_snapshot_rejects_unknown_stage_key():
    with pytest.raises(UnknownStageStateError, match="unknown_stage"):
        StageStateSnapshot("unknown_stage", "completed")


def test_terminal_stage_status_helper_identifies_terminal_values():
    assert is_terminal_stage_status("completed") is True
    assert is_terminal_stage_status("degraded") is True
    assert is_terminal_stage_status("failed") is True
    assert is_terminal_stage_status("skipped") is True
    assert is_terminal_stage_status("not_started") is False
    assert is_terminal_stage_status("in_progress") is False


def test_terminal_stage_status_helper_rejects_unknown_status():
    with pytest.raises(UnknownStageStateError, match="mystery"):
        is_terminal_stage_status("mystery")


def test_derive_run_status_reports_queued_for_empty_stage_list():
    assert derive_run_status_from_stages([]) == "queued"


def test_derive_run_status_reports_failed_for_failed_intake_validation():
    stages = [
        StageStateSnapshot("intake_validation", "failed", review_required=True),
        StageStateSnapshot("research_plan", "not_started"),
        StageStateSnapshot("weather", "not_started"),
    ]

    assert derive_run_status_from_stages(stages) == "failed"


def test_derive_run_status_reports_failed_for_failed_research_plan():
    stages = [
        StageStateSnapshot("intake_validation", "completed"),
        StageStateSnapshot("research_plan", "failed", review_required=True),
        StageStateSnapshot("weather", "not_started"),
    ]

    assert derive_run_status_from_stages(stages) == "failed"


def test_derive_run_status_reports_partial_success_for_failed_stage_with_usable_output():
    stages = [
        StageStateSnapshot("intake_validation", "completed"),
        StageStateSnapshot("research_plan", "completed"),
        StageStateSnapshot("weather", "failed", review_required=True),
        StageStateSnapshot("carrier", "completed"),
        StageStateSnapshot("caselaw", "completed"),
        StageStateSnapshot("citation_verify", "completed"),
    ]

    assert derive_run_status_from_stages(stages) == "partial_success"
    assert run_requires_review(stages) is True


def test_derive_run_status_reports_partial_success_for_failed_memo_assembly_with_outputs():
    stages = [
        StageStateSnapshot("intake_validation", "completed"),
        StageStateSnapshot("research_plan", "completed"),
        StageStateSnapshot("weather", "completed"),
        StageStateSnapshot("carrier", "completed"),
        StageStateSnapshot("caselaw", "completed"),
        StageStateSnapshot("citation_verify", "completed"),
        StageStateSnapshot("memo_assembly", "failed", review_required=True),
    ]

    assert derive_run_status_from_stages(stages) == "partial_success"


def test_derive_run_status_reports_partial_success_for_failed_export_with_outputs():
    stages = [
        StageStateSnapshot("intake_validation", "completed"),
        StageStateSnapshot("research_plan", "completed"),
        StageStateSnapshot("weather", "completed"),
        StageStateSnapshot("carrier", "completed"),
        StageStateSnapshot("caselaw", "completed"),
        StageStateSnapshot("citation_verify", "completed"),
        StageStateSnapshot("memo_assembly", "completed"),
        StageStateSnapshot("export", "failed", review_required=True),
    ]

    assert derive_run_status_from_stages(stages) == "partial_success"


def test_derive_run_status_reports_failed_when_no_reviewable_output_survives():
    stages = [
        StageStateSnapshot("intake_validation", "completed"),
        StageStateSnapshot("research_plan", "completed"),
        StageStateSnapshot("weather", "failed", review_required=True),
        StageStateSnapshot("carrier", "failed", review_required=True),
        StageStateSnapshot("caselaw", "failed", review_required=True),
        StageStateSnapshot("citation_verify", "failed", review_required=True),
    ]

    assert derive_run_status_from_stages(stages) == "failed"


def test_derive_run_status_reports_completed_when_outputs_are_complete_or_degraded():
    stages = [
        StageStateSnapshot("intake_validation", "completed"),
        StageStateSnapshot("research_plan", "completed"),
        StageStateSnapshot("weather", "completed"),
        StageStateSnapshot("carrier", "completed"),
        StageStateSnapshot("caselaw", "completed"),
        StageStateSnapshot("citation_verify", "degraded", review_required=True),
        StageStateSnapshot("memo_assembly", "degraded", review_required=True),
        StageStateSnapshot("export", "skipped"),
    ]

    assert derive_run_status_from_stages(stages) == "completed"
    assert run_requires_review(stages) is True


def test_run_requires_review_includes_memo_assembly_stage():
    stages = [
        StageStateSnapshot("intake_validation", "completed"),
        StageStateSnapshot("research_plan", "completed"),
        StageStateSnapshot("weather", "completed"),
        StageStateSnapshot("carrier", "completed"),
        StageStateSnapshot("caselaw", "completed"),
        StageStateSnapshot("citation_verify", "completed"),
        StageStateSnapshot("memo_assembly", "degraded", review_required=True),
        StageStateSnapshot("export", "skipped"),
    ]

    assert derive_run_status_from_stages(stages) == "completed"
    assert run_requires_review(stages) is True


def test_derive_run_status_reports_queued_and_running_nonterminal_states():
    assert derive_run_status_from_stages(
        [
            StageStateSnapshot("intake_validation", "not_started"),
            StageStateSnapshot("research_plan", "not_started"),
        ]
    ) == "queued"
    assert derive_run_status_from_stages(
        [
            StageStateSnapshot("intake_validation", "completed"),
            StageStateSnapshot("research_plan", "in_progress"),
            StageStateSnapshot("weather", "not_started"),
        ]
    ) == "running"
