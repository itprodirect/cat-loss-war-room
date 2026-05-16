"""In-process offline orchestration service for the first issue #10 slice.

The service intentionally stays below an HTTP/API framework boundary. It
accepts the typed API contracts, executes the current cache-backed offline
runtime synchronously, and returns typed status contracts that future routes can
wrap without changing response semantics.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from war_room.bootstrap import discover_repo_root
from war_room.carrier_module import build_carrier_doc_pack
from war_room.caselaw_module import build_caselaw_pack
from war_room.evidence_board import build_evidence_board_from_parts
from war_room.export_history import build_export_history_from_parts
from war_room.export_md import render_markdown_memo
from war_room.issue_workspace import build_issue_workspace_from_parts
from war_room.memo_composer import build_memo_composer_from_parts
from war_room.models import (
    CaseIntake,
    ExportHistoryReadModel,
    EvidenceBoardReadModel,
    IssueWorkspaceReadModel,
    MemoComposerReadModel,
    ResearchPlan,
    Run,
    RunEvent,
    RunStage,
    RunTimelineReadModel,
)
from war_room.notebook_runtime import build_notebook_citation_review
from war_room.orchestration import STAGE_KEYS, StageKey, StageStatus, is_terminal_run_status
from war_room.orchestration_api_contracts import (
    GetRunStatusResponse,
    OrchestrationErrorResponse,
    OrchestrationFailurePayload,
    OrchestrationRunStatusPayload,
    OrchestrationStagePayload,
    OrchestrationTimelinePayload,
    OrchestrationUsableOutputPayload,
    StartRunRequest,
    StartRunResponse,
    adapt_start_run_request,
    get_run_status_response_to_payload,
    orchestration_error_response_to_payload,
    run_status_payload_from_run,
    start_run_response_to_payload,
)
from war_room.query_plan import build_research_plan
from war_room.scenarios import (
    ScenarioDefinition,
    ScenarioValidationError,
    list_scenarios,
    load_scenario,
)
from war_room.weather_module import build_weather_brief
from war_room.workflow_summary import build_run_timeline

_REQUIRED_FIXTURE_FILES = ("weather.json", "carrier.json", "caselaw.json", "citation_verify.json")
_DEFAULT_SMOKE_SCENARIO = "milton_pinellas_citizens_ho3"


class OrchestrationServiceError(RuntimeError):
    """Base error for in-process service misuse."""


class UnknownRunError(OrchestrationServiceError):
    """Raised when a caller asks for a run id this service has not created."""


class OfflineScenarioUnavailableError(OrchestrationServiceError):
    """Raised when a request cannot be mapped to a committed offline fixture lane."""


@dataclass(frozen=True)
class OrchestrationServiceOutputs:
    """Preserved in-memory outputs from an executed offline run."""

    research_plan: ResearchPlan | None = None
    weather: dict[str, Any] | None = None
    carrier: dict[str, Any] | None = None
    caselaw: dict[str, Any] | None = None
    citation_verify: dict[str, Any] | None = None
    memo_markdown: str = ""
    evidence_board: EvidenceBoardReadModel | None = None
    issue_workspace: IssueWorkspaceReadModel | None = None
    memo_composer: MemoComposerReadModel | None = None
    export_history: ExportHistoryReadModel | None = None
    run_timeline: RunTimelineReadModel | None = None


@dataclass
class _ServiceRunRecord:
    request: StartRunRequest
    run: Run
    stages: list[OrchestrationStagePayload]
    recent_events: list[RunEvent] = field(default_factory=list)
    usable_outputs: list[OrchestrationUsableOutputPayload] = field(default_factory=list)
    outputs: OrchestrationServiceOutputs = field(default_factory=OrchestrationServiceOutputs)
    failure: OrchestrationFailurePayload | None = None


class InMemoryOrchestrationService:
    """Small synchronous service for cache-backed product-mode orchestration."""

    def __init__(
        self,
        *,
        repo_root: str | Path | None = None,
        cache_samples_dir: str | Path | None = None,
    ) -> None:
        self.repo_root = Path(repo_root) if repo_root is not None else discover_repo_root()
        self.cache_samples_dir = (
            Path(cache_samples_dir) if cache_samples_dir is not None else self.repo_root / "cache_samples"
        )
        self._runs: dict[str, _ServiceRunRecord] = {}
        self._run_sequence = 0

    def start_run(self, request: StartRunRequest | Mapping[str, Any]) -> StartRunResponse:
        """Create an in-memory queued run from a typed start-run request."""

        typed_request = adapt_start_run_request(request)
        now = _utc_now()
        run_id = self._next_run_id(typed_request.intake)
        run = Run(
            run_id=run_id,
            environment=typed_request.environment,
            status="queued",
            review_required=False,
            created_at=now,
            intake_id=f"{run_id}:intake",
            plan_id=f"{run_id}:plan",
        )
        stages = [
            _stage_payload(
                run_id=run_id,
                stage_key=stage_key,
                status="not_started",
            )
            for stage_key in STAGE_KEYS
        ]
        record = _ServiceRunRecord(
            request=typed_request,
            run=run,
            stages=stages,
            recent_events=[
                _run_event(
                    run_id=run_id,
                    event_type="run_queued",
                    message="Offline orchestration run queued in memory.",
                    created_at=now,
                )
            ],
        )
        self._runs[run_id] = record
        return StartRunResponse(
            run=record.run,
            status=_status_payload(record),
            timeline=_timeline_payload(record),
        )

    def execute_run(self, run_id: str) -> GetRunStatusResponse:
        """Execute a queued run synchronously against committed offline fixtures."""

        record = self._require_run(run_id)
        if is_terminal_run_status(record.run.status):
            return _status_response(record)

        started_at = record.run.started_at or _utc_now()
        record.run = record.run.model_copy(
            update={
                "status": "running",
                "started_at": started_at,
            }
        )
        record.recent_events.append(
            _run_event(
                run_id=run_id,
                event_type="run_started",
                message="Offline fixture-backed execution started.",
                created_at=started_at,
            )
        )

        try:
            scenario = self._offline_scenario_for_request(record.request)
            self._ensure_fixture_bundle(scenario)
            response = self._execute_offline_fixture_run(record, scenario)
        except Exception as exc:
            response = self._fail_run(
                record,
                code="offline_execution_failed",
                message="Offline orchestration execution failed.",
                detail=f"{type(exc).__name__}: {exc}",
            )
        return response

    def get_run_status(self, run_id: str) -> GetRunStatusResponse:
        """Return the current typed run-status response for an in-memory run."""

        return _status_response(self._require_run(run_id))

    def get_run_outputs(self, run_id: str) -> OrchestrationServiceOutputs:
        """Return preserved in-memory outputs for local callers and tests."""

        return self._require_run(run_id).outputs

    def _execute_offline_fixture_run(
        self,
        record: _ServiceRunRecord,
        scenario: ScenarioDefinition,
    ) -> GetRunStatusResponse:
        intake = record.request.intake
        run_id = record.run.run_id
        research_plan = build_research_plan(
            intake,
            plan_id=f"{run_id}:plan",
            run_id=run_id,
        )
        query_plan = research_plan.query_plan
        cache_samples_dir = str(self.cache_samples_dir)

        weather = build_weather_brief(
            intake,
            None,
            query_plan=query_plan,
            use_cache=True,
            cache_dir=cache_samples_dir,
            cache_samples_dir=cache_samples_dir,
        )
        carrier = build_carrier_doc_pack(
            intake,
            None,
            query_plan=query_plan,
            use_cache=True,
            cache_dir=cache_samples_dir,
            cache_samples_dir=cache_samples_dir,
        )
        caselaw = build_caselaw_pack(
            intake,
            None,
            query_plan=query_plan,
            use_cache=True,
            cache_dir=cache_samples_dir,
            cache_samples_dir=cache_samples_dir,
        )
        citation_verify = build_notebook_citation_review(
            caselaw,
            None,
            case_key=scenario.case_key,
            use_cache=True,
            live_retrieval_enabled=False,
            cache_dir=cache_samples_dir,
            cache_samples_dir=cache_samples_dir,
        )
        memo_markdown = render_markdown_memo(
            intake,
            weather,
            carrier,
            caselaw,
            citation_verify,
            query_plan,
        )
        evidence_board = build_evidence_board_from_parts(
            intake,
            weather,
            carrier,
            caselaw,
            citation_verify,
            query_plan,
        )
        issue_workspace = build_issue_workspace_from_parts(
            intake,
            weather,
            carrier,
            caselaw,
            citation_verify,
            query_plan,
        )
        memo_composer = build_memo_composer_from_parts(
            intake,
            weather,
            carrier,
            caselaw,
            citation_verify,
            query_plan,
        )
        run, run_stages = build_run_timeline(
            intake,
            research_plan,
            weather,
            carrier,
            caselaw,
            citation_verify,
            environment=record.request.environment,
            export_written=False,
        )
        run = run.model_copy(
            update={
                "created_at": record.run.created_at,
                "started_at": record.run.started_at,
                "intake_id": record.run.intake_id,
            }
        )
        export_history = build_export_history_from_parts(
            intake,
            weather,
            carrier,
            caselaw,
            citation_verify,
            query_plan,
            run_status=run.status,
            export_written=False,
        )

        record.run = run
        record.stages = [_api_stage_from_run_stage(stage) for stage in run_stages]
        record.usable_outputs = _usable_outputs_for_run(
            run=record.run,
            stages=record.stages,
            weather=weather,
            carrier=carrier,
            caselaw=caselaw,
            citation_verify=citation_verify,
            memo_composer=memo_composer,
            evidence_board=evidence_board,
            issue_workspace=issue_workspace,
            memo_markdown=memo_markdown,
        )
        record.outputs = OrchestrationServiceOutputs(
            research_plan=research_plan,
            weather=weather,
            carrier=carrier,
            caselaw=caselaw,
            citation_verify=citation_verify,
            memo_markdown=memo_markdown,
            evidence_board=evidence_board,
            issue_workspace=issue_workspace,
            memo_composer=memo_composer,
            export_history=export_history,
            run_timeline=RunTimelineReadModel(run=record.run, stages=run_stages),
        )
        record.failure = None
        record.recent_events.append(
            _run_event(
                run_id=run_id,
                event_type="run_completed",
                severity="warning" if record.run.review_required else "info",
                message=(
                    f"Offline fixture-backed execution finished with status "
                    f"{record.run.status}."
                ),
                created_at=record.run.completed_at or _utc_now(),
            )
        )
        return _status_response(record)

    def _fail_run(
        self,
        record: _ServiceRunRecord,
        *,
        code: str,
        message: str,
        detail: str,
    ) -> GetRunStatusResponse:
        completed_at = _utc_now()
        run_id = record.run.run_id
        failure = OrchestrationFailurePayload(
            code=code,
            message=message,
            stage_key="research_plan",
            stage_id=f"{run_id}:research_plan",
            retryable=False,
            detail=detail,
        )
        record.run = record.run.model_copy(
            update={
                "status": "failed",
                "review_required": True,
                "started_at": record.run.started_at or completed_at,
                "completed_at": completed_at,
            }
        )
        record.stages = [
            _stage_payload(
                run_id=run_id,
                stage_key="intake_validation",
                status="completed",
                started_at=record.run.started_at,
                completed_at=record.run.started_at,
                summary="Typed start-run request accepted.",
            ),
            _stage_payload(
                run_id=run_id,
                stage_key="research_plan",
                status="failed",
                review_required=True,
                started_at=record.run.started_at,
                completed_at=completed_at,
                summary="Offline scenario planning failed before fixture execution.",
                error_summary=message,
                failure=failure,
            ),
            *[
                _stage_payload(
                    run_id=run_id,
                    stage_key=stage_key,
                    status="not_started",
                )
                for stage_key in STAGE_KEYS
                if stage_key not in {"intake_validation", "research_plan"}
            ],
        ]
        record.usable_outputs = []
        record.outputs = OrchestrationServiceOutputs()
        record.failure = None
        record.recent_events.append(
            _run_event(
                run_id=run_id,
                stage_id=f"{run_id}:research_plan",
                event_type="run_failed",
                severity="error",
                message=f"{message} {detail}".strip(),
                created_at=completed_at,
            )
        )
        return _status_response(record)

    def _offline_scenario_for_request(self, request: StartRunRequest) -> ScenarioDefinition:
        requested = request.intake.model_dump()
        for scenario in list_scenarios(repo_root=self.repo_root):
            scenario_intake = scenario.to_case_intake()
            if scenario_intake.model_dump() != requested:
                continue
            if not scenario.offline_demo_ready:
                raise OfflineScenarioUnavailableError(
                    f"Scenario '{scenario.slug}' is not marked offline-demo-ready."
                )
            return scenario
        raise OfflineScenarioUnavailableError(
            "StartRunRequest intake does not match a curated offline-ready scenario."
        )

    def _ensure_fixture_bundle(self, scenario: ScenarioDefinition) -> None:
        fixture_dir = self.cache_samples_dir / scenario.case_key
        missing = [
            filename
            for filename in _REQUIRED_FIXTURE_FILES
            if not (fixture_dir / filename).exists()
        ]
        if missing:
            raise OfflineScenarioUnavailableError(
                f"Scenario '{scenario.slug}' fixture '{scenario.case_key}' is missing: "
                f"{', '.join(missing)}."
            )

    def _next_run_id(self, intake: CaseIntake) -> str:
        self._run_sequence += 1
        base = "run-offline-" + "-".join(
            _stable_token(part)
            for part in (intake.event_name, intake.state, intake.county, intake.carrier)
            if part.strip()
        )
        candidate = base
        if candidate in self._runs:
            candidate = f"{base}-{self._run_sequence}"
        return candidate

    def _require_run(self, run_id: str) -> _ServiceRunRecord:
        try:
            return self._runs[run_id]
        except KeyError as exc:
            raise UnknownRunError(f"Unknown orchestration run_id: {run_id}") from exc


_DEFAULT_SERVICE: InMemoryOrchestrationService | None = None


def default_service() -> InMemoryOrchestrationService:
    """Return the process-local default orchestration service."""

    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        _DEFAULT_SERVICE = InMemoryOrchestrationService()
    return _DEFAULT_SERVICE


def start_run(request: StartRunRequest | Mapping[str, Any]) -> StartRunResponse:
    """Create a queued run with the process-local in-memory service."""

    return default_service().start_run(request)


def execute_run(run_id: str) -> GetRunStatusResponse:
    """Execute a queued run with the process-local in-memory service."""

    return default_service().execute_run(run_id)


def get_run_status(run_id: str) -> GetRunStatusResponse:
    """Get run status from the process-local in-memory service."""

    return default_service().get_run_status(run_id)


def get_run_outputs(run_id: str) -> OrchestrationServiceOutputs:
    """Get preserved outputs from the process-local in-memory service."""

    return default_service().get_run_outputs(run_id)


def error_response_to_payload(
    error: OrchestrationServiceError,
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Return a JSON-safe typed error payload for wrapper boundaries."""

    response = OrchestrationErrorResponse(
        run_id=run_id,
        error=OrchestrationFailurePayload(
            code=_stable_error_code(type(error).__name__),
            message=str(error),
            retryable=False,
        ),
    )
    return orchestration_error_response_to_payload(response)


def main(argv: list[str] | None = None) -> int:
    """Run the dependency-free offline smoke CLI."""

    parser = argparse.ArgumentParser(description="Offline orchestration service smoke runner.")
    parser.add_argument("--smoke", action="store_true", help="Run the offline service smoke.")
    parser.add_argument(
        "--scenario",
        default=_DEFAULT_SMOKE_SCENARIO,
        help="Curated offline-ready scenario slug to execute.",
    )
    args = parser.parse_args(argv)

    if not args.smoke:
        parser.error("--smoke is required for this module CLI")

    try:
        service = InMemoryOrchestrationService()
        scenario = load_scenario(args.scenario, repo_root=service.repo_root)
        response = service.start_run(
            StartRunRequest(
                intake=scenario.to_case_intake(),
                environment="offline_service",
            )
        )
        status = service.execute_run(response.run.run_id)
    except (OrchestrationServiceError, ScenarioValidationError) as exc:
        print(json.dumps(error_response_to_payload(exc), indent=2))
        return 1

    print(json.dumps(_smoke_summary(response, status), indent=2))
    return 0 if status.run.status in {"completed", "partial_success"} else 1


def _status_response(record: _ServiceRunRecord) -> GetRunStatusResponse:
    return GetRunStatusResponse(
        run=record.run,
        status=_status_payload(record),
        timeline=_timeline_payload(record),
        usable_outputs=record.usable_outputs,
        failure=record.failure,
    )


def _status_payload(record: _ServiceRunRecord) -> OrchestrationRunStatusPayload:
    return run_status_payload_from_run(
        record.run,
        current_stage_key=_current_stage_key(record.stages),
        stage_counts=_stage_counts(record.stages),
        usable_output_count=len(record.usable_outputs),
        failure_count=_failure_count(record),
    )


def _timeline_payload(record: _ServiceRunRecord) -> OrchestrationTimelinePayload:
    return OrchestrationTimelinePayload(
        run_id=record.run.run_id,
        stages=record.stages,
        recent_events=record.recent_events[-10:],
    )


def _stage_payload(
    *,
    run_id: str,
    stage_key: str,
    status: str,
    review_required: bool = False,
    started_at: dt.datetime | None = None,
    completed_at: dt.datetime | None = None,
    summary: str = "",
    error_summary: str = "",
    failure: OrchestrationFailurePayload | None = None,
) -> OrchestrationStagePayload:
    return OrchestrationStagePayload(
        stage_id=f"{run_id}:{stage_key}",
        run_id=run_id,
        stage_key=stage_key,
        status=status,
        review_required=review_required,
        started_at=started_at,
        completed_at=completed_at,
        summary=summary,
        error_summary=error_summary,
        failure=failure,
    )


def _api_stage_from_run_stage(stage: RunStage) -> OrchestrationStagePayload:
    return OrchestrationStagePayload(
        stage_id=stage.stage_id,
        run_id=stage.run_id,
        stage_key=stage.stage_key,
        status=stage.status,
        review_required=stage.review_required,
        started_at=stage.started_at,
        completed_at=stage.completed_at,
        summary=stage.summary,
        error_summary=stage.error_summary,
    )


def _usable_outputs_for_run(
    *,
    run: Run,
    stages: list[OrchestrationStagePayload],
    weather: Mapping[str, Any],
    carrier: Mapping[str, Any],
    caselaw: Mapping[str, Any],
    citation_verify: Mapping[str, Any],
    memo_composer: MemoComposerReadModel,
    evidence_board: EvidenceBoardReadModel,
    issue_workspace: IssueWorkspaceReadModel,
    memo_markdown: str,
) -> list[OrchestrationUsableOutputPayload]:
    stages_by_key = {stage.stage_key: stage for stage in stages}
    outputs: list[OrchestrationUsableOutputPayload] = []

    _append_stage_output(
        outputs,
        run_id=run.run_id,
        stage=stages_by_key.get("weather"),
        output_type="weather_brief",
        label=f"Weather brief ({len(weather.get('sources', []))} sources)",
    )
    _append_stage_output(
        outputs,
        run_id=run.run_id,
        stage=stages_by_key.get("carrier"),
        output_type="carrier_doc_pack",
        label=f"Carrier document pack ({len(carrier.get('document_pack', []))} documents)",
    )
    _append_stage_output(
        outputs,
        run_id=run.run_id,
        stage=stages_by_key.get("caselaw"),
        output_type="caselaw_pack",
        label=f"Case-law pack ({sum(len(issue.get('cases', [])) for issue in caselaw.get('issues', []))} authorities)",
    )
    _append_stage_output(
        outputs,
        run_id=run.run_id,
        stage=stages_by_key.get("citation_verify"),
        output_type="citation_verify_pack",
        label=(
            "Citation verification "
            f"({citation_verify.get('summary', {}).get('total', 0)} checks)"
        ),
    )

    memo_stage = stages_by_key.get("memo_assembly")
    if memo_stage is not None and memo_stage.status in {"completed", "degraded"} and memo_markdown:
        outputs.append(
            OrchestrationUsableOutputPayload(
                output_id=f"{run.run_id}:memo_draft",
                run_id=run.run_id,
                stage_key="memo_assembly",
                output_type="memo_draft",
                label=f"Memo draft ({len(memo_composer.section_cards)} sections)",
                uri=f"memory://runs/{run.run_id}/outputs/memo_markdown",
                review_required=memo_stage.review_required,
            )
        )

    if evidence_board.total_evidence_items or issue_workspace.issue_cards:
        outputs.append(
            OrchestrationUsableOutputPayload(
                output_id=f"{run.run_id}:audit_bundle",
                run_id=run.run_id,
                stage_key="memo_assembly",
                output_type="audit_bundle",
                label=(
                    f"Audit read-model bundle ({evidence_board.total_clusters} clusters, "
                    f"{len(issue_workspace.issue_cards)} issues)"
                ),
                uri=f"memory://runs/{run.run_id}/outputs/audit_bundle",
                review_required=run.review_required,
            )
        )
    return outputs


def _append_stage_output(
    outputs: list[OrchestrationUsableOutputPayload],
    *,
    run_id: str,
    stage: OrchestrationStagePayload | None,
    output_type: str,
    label: str,
) -> None:
    if stage is None or stage.status not in {"completed", "degraded"}:
        return
    outputs.append(
        OrchestrationUsableOutputPayload(
            output_id=f"{run_id}:{stage.stage_key}",
            run_id=run_id,
            stage_key=stage.stage_key,
            output_type=output_type,
            label=label,
            uri=f"memory://runs/{run_id}/outputs/{stage.stage_key}",
            review_required=stage.review_required,
        )
    )


def _stage_counts(stages: list[OrchestrationStagePayload]) -> dict[StageStatus, int]:
    counts: dict[StageStatus, int] = {}
    for stage in stages:
        counts[stage.status] = counts.get(stage.status, 0) + 1
    return counts


def _failure_count(record: _ServiceRunRecord) -> int:
    return sum(stage.status == "failed" for stage in record.stages) + (
        1 if record.failure is not None else 0
    )


def _current_stage_key(stages: list[OrchestrationStagePayload]) -> StageKey | None:
    for stage in stages:
        if stage.status == "in_progress":
            return stage.stage_key
    return None


def _run_event(
    *,
    run_id: str,
    event_type: str,
    message: str,
    severity: str = "info",
    stage_id: str | None = None,
    created_at: dt.datetime | None = None,
) -> RunEvent:
    return RunEvent(
        run_event_id=f"{run_id}:event:{_stable_token(event_type)}:{len(message)}",
        run_id=run_id,
        stage_id=stage_id,
        event_type=event_type,
        severity=severity,
        message=message,
        created_at=created_at or _utc_now(),
    )


def _stable_token(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "item"


def _stable_error_code(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized or "orchestration_service_error"


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _smoke_summary(
    start_response: StartRunResponse,
    status_response: GetRunStatusResponse,
) -> dict[str, Any]:
    payload = get_run_status_response_to_payload(status_response)
    return {
        "started": start_run_response_to_payload(start_response)["run"]["status"],
        "run_id": payload["run"]["run_id"],
        "status": payload["run"]["status"],
        "review_required": payload["run"]["review_required"],
        "stage_summary": {
            stage["stage_key"]: stage["status"]
            for stage in payload["timeline"]["stages"]
        },
        "usable_output_summary": [
            {
                "output_type": output["output_type"],
                "stage_key": output["stage_key"],
                "label": output["label"],
                "review_required": output["review_required"],
            }
            for output in payload["usable_outputs"]
        ],
    }


if __name__ == "__main__":
    raise SystemExit(main())
