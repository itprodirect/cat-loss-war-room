"""Operator-facing orchestration status presentation helpers.

This module sits above the typed service/API contracts. It keeps the canonical
run status unchanged while deriving a small app-friendly view that future CLI,
API, or UX consumers can display without adding a web framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from war_room.orchestration_api_contracts import (
    GetRunStatusResponse,
    get_run_status_response_to_payload,
)


@dataclass(frozen=True)
class OrchestrationStatusView:
    """Stable presentation contract for an orchestration run status."""

    run_id: str
    status: str
    operator_status: str
    headline: str
    operator_message: str
    usable_outputs_available: bool
    usable_outputs: list[dict[str, Any]] = field(default_factory=list)
    review_required: bool = False
    review_reasons: list[str] = field(default_factory=list)
    degraded_stages: list[dict[str, Any]] = field(default_factory=list)
    failed_stages: list[dict[str, Any]] = field(default_factory=list)
    failure_kind: str | None = None
    failure_message: str = ""
    next_actions: list[str] = field(default_factory=list)
    scenario_id: str | None = None

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready dictionary for transport or CLI rendering."""

        return {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "status": self.status,
            "operator_status": self.operator_status,
            "headline": self.headline,
            "operator_message": self.operator_message,
            "usable_outputs_available": self.usable_outputs_available,
            "usable_outputs": list(self.usable_outputs),
            "review_required": self.review_required,
            "review_reasons": list(self.review_reasons),
            "degraded_stages": list(self.degraded_stages),
            "failed_stages": list(self.failed_stages),
            "failure_kind": self.failure_kind,
            "failure_message": self.failure_message,
            "next_actions": list(self.next_actions),
        }


def build_orchestration_status_view(
    response: Mapping[str, Any] | GetRunStatusResponse,
    *,
    scenario_id: str | None = None,
) -> OrchestrationStatusView:
    """Build an operator-facing status view from a typed service response."""

    payload = get_run_status_response_to_payload(response)
    run = payload["run"]
    stages = payload["timeline"]["stages"]
    usable_outputs = [_usable_output_summary(output) for output in payload["usable_outputs"]]
    degraded_stages = [
        _stage_summary(stage)
        for stage in stages
        if stage["status"] == "degraded"
    ]
    failed_stages = [
        _stage_summary(stage)
        for stage in stages
        if stage["status"] == "failed"
    ]
    failure = _first_failure(payload, failed_stages)
    review_reasons = _review_reasons(
        review_required=run["review_required"],
        degraded_stages=degraded_stages,
        failed_stages=failed_stages,
        usable_outputs=usable_outputs,
    )
    operator_status = _operator_status(
        status=run["status"],
        review_required=run["review_required"],
        degraded_stages=degraded_stages,
    )
    headline, operator_message = _operator_language(
        operator_status=operator_status,
        usable_output_count=len(usable_outputs),
        degraded_stages=degraded_stages,
        failed_stages=failed_stages,
        failure_message=failure["message"],
    )

    return OrchestrationStatusView(
        run_id=run["run_id"],
        scenario_id=scenario_id,
        status=run["status"],
        operator_status=operator_status,
        headline=headline,
        operator_message=operator_message,
        usable_outputs_available=bool(usable_outputs),
        usable_outputs=usable_outputs,
        review_required=run["review_required"],
        review_reasons=review_reasons,
        degraded_stages=degraded_stages,
        failed_stages=failed_stages,
        failure_kind=failure["kind"],
        failure_message=failure["message"],
        next_actions=_next_actions(
            operator_status=operator_status,
            review_required=run["review_required"],
            usable_output_count=len(usable_outputs),
        ),
    )


def orchestration_status_view_to_payload(
    response: Mapping[str, Any] | GetRunStatusResponse | OrchestrationStatusView,
    *,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    """Return the status presentation view as a JSON-ready dictionary."""

    if isinstance(response, OrchestrationStatusView):
        return response.to_payload()
    return build_orchestration_status_view(response, scenario_id=scenario_id).to_payload()


def _operator_status(
    *,
    status: str,
    review_required: bool,
    degraded_stages: list[dict[str, Any]],
) -> str:
    if status in {"failed", "partial_success", "queued", "running", "cancelled"}:
        return status
    if degraded_stages:
        return "degraded"
    if review_required:
        return "review_required"
    return status


def _operator_language(
    *,
    operator_status: str,
    usable_output_count: int,
    degraded_stages: list[dict[str, Any]],
    failed_stages: list[dict[str, Any]],
    failure_message: str,
) -> tuple[str, str]:
    if operator_status == "completed":
        return (
            "Run completed with usable outputs.",
            (
                "The offline orchestration run completed successfully and "
                f"{usable_output_count} output(s) are available for demo review."
            ),
        )
    if operator_status == "degraded":
        stage_list = _join_stage_keys(degraded_stages)
        return (
            "Run completed with degraded stages.",
            (
                "Outputs are usable, but "
                f"{stage_list} reported limitations that a human should review."
            ),
        )
    if operator_status == "review_required":
        return (
            "Run completed and requires human review.",
            (
                "Outputs are usable, but the run is marked review_required. "
                "Inspect the review reasons before relying on the result."
            ),
        )
    if operator_status == "partial_success":
        stage_list = _join_stage_keys(failed_stages)
        return (
            "Run partially completed with preserved outputs.",
            (
                "The run did not fully complete, but usable outputs survived. "
                f"Review preserved outputs and investigate failed stage(s): {stage_list}."
            ),
        )
    if operator_status == "failed":
        message = failure_message or "No typed failure message was provided."
        return (
            "Run failed before usable outputs were produced.",
            f"The run did not complete successfully. Typed failure: {message}",
        )
    if operator_status == "running":
        return (
            "Run is still running.",
            "The run has not reached a terminal status yet. Check status again before demo use.",
        )
    if operator_status == "queued":
        return (
            "Run is queued.",
            "The run has been accepted but has not started execution yet.",
        )
    return (
        f"Run status is {operator_status}.",
        "Inspect the typed status response before using this run in a demo.",
    )


def _next_actions(
    *,
    operator_status: str,
    review_required: bool,
    usable_output_count: int,
) -> list[str]:
    if operator_status == "failed":
        return [
            "Do not present this run as demo-ready.",
            "Inspect the typed failure details, fixture availability, and scenario mapping, then rerun.",
        ]
    if operator_status == "partial_success":
        return [
            "Review the preserved usable outputs before relying on them.",
            "Investigate failed stages before presenting the run as complete.",
        ]
    if operator_status in {"degraded", "review_required"} or review_required:
        return [
            "Inspect review reasons, degraded stages, and review-required outputs.",
            "Verify citations, memo warnings, and disclaimers before showing the scenario.",
        ]
    if usable_output_count:
        return [
            "Open the usable outputs and confirm the memo disclaimer and citation posture before demo use.",
        ]
    return [
        "Check the typed status response before demo use.",
    ]


def _review_reasons(
    *,
    review_required: bool,
    degraded_stages: list[dict[str, Any]],
    failed_stages: list[dict[str, Any]],
    usable_outputs: list[dict[str, Any]],
) -> list[str]:
    reasons: list[str] = []
    for stage in degraded_stages:
        reasons.append(_stage_reason(stage, fallback="Stage is degraded."))
    for stage in failed_stages:
        reasons.append(_stage_reason(stage, fallback="Stage failed."))
    for output in usable_outputs:
        if output["review_required"]:
            reasons.append(f"{output['label']} requires review.")
    if review_required and not reasons:
        reasons.append("Run is marked review_required by the orchestration contract.")
    return _dedupe(reasons)


def _stage_summary(stage: Mapping[str, Any]) -> dict[str, Any]:
    failure = stage.get("failure") or {}
    failure_message = failure.get("message") or stage.get("error_summary") or ""
    return {
        "stage_key": stage["stage_key"],
        "status": stage["status"],
        "review_required": stage["review_required"],
        "summary": stage.get("summary", ""),
        "error_summary": stage.get("error_summary", ""),
        "failure_kind": failure.get("code"),
        "failure_message": failure_message,
    }


def _usable_output_summary(output: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "output_type": output["output_type"],
        "stage_key": output["stage_key"],
        "label": output["label"],
        "uri": output.get("uri"),
        "review_required": output["review_required"],
    }


def _first_failure(
    payload: Mapping[str, Any],
    failed_stages: list[dict[str, Any]],
) -> dict[str, str | None]:
    response_failure = payload.get("failure")
    if response_failure:
        return {
            "kind": response_failure.get("code"),
            "message": response_failure.get("message") or response_failure.get("detail") or "",
        }
    for stage in failed_stages:
        return {
            "kind": stage.get("failure_kind") or "stage_failed",
            "message": stage.get("failure_message") or stage.get("error_summary") or "",
        }
    return {"kind": None, "message": ""}


def _stage_reason(stage: Mapping[str, Any], *, fallback: str) -> str:
    detail = stage.get("failure_message") or stage.get("error_summary") or stage.get("summary")
    if detail:
        return f"{stage['stage_key']}: {detail}"
    return f"{stage['stage_key']}: {fallback}"


def _join_stage_keys(stages: list[dict[str, Any]]) -> str:
    keys = [stage["stage_key"] for stage in stages]
    if not keys:
        return "none"
    if len(keys) == 1:
        return keys[0]
    if len(keys) == 2:
        return f"{keys[0]} and {keys[1]}"
    return ", ".join(keys[:-1]) + f", and {keys[-1]}"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
