"""Workflow-oriented plan preview and run timeline helpers."""

from __future__ import annotations

import datetime as dt
from typing import Any, Mapping, Sequence

from war_room.models import (
    CaseIntake,
    CaseLawPack,
    CarrierDocPack,
    CitationVerifyPack,
    ResearchPlan,
    Run,
    RunStage,
    RunTimelineReadModel,
    WeatherBrief,
    adapt_run,
    adapt_run_stage,
    adapt_run_timeline,
    adapt_research_plan,
    memo_render_input_from_parts,
    run_audit_snapshot_from_memo_input,
)

_PLAN_MODULE_LABELS = {
    "weather": "Weather",
    "carrier_docs": "Carrier Documents",
    "caselaw": "Case Law",
}
_STAGE_LABELS = {
    "intake_validation": "Intake Validation",
    "research_plan": "Research Plan Preview",
    "weather": "Weather Corroboration",
    "carrier": "Carrier Document Pack",
    "caselaw": "Case Law",
    "citation_verify": "Citation Spot-Check",
    "memo_assembly": "Memo Assembly",
    "export": "Export",
}
_REVIEWABLE_STAGE_KEYS = {
    "research_plan",
    "weather",
    "carrier",
    "caselaw",
    "citation_verify",
    "memo_assembly",
}
_OUTPUT_STAGE_KEYS = {
    "weather",
    "carrier",
    "caselaw",
    "citation_verify",
}


def format_research_plan_preview(plan: Mapping[str, Any] | ResearchPlan) -> str:
    """Render the research-plan preview as a notebook-friendly text block."""

    typed_plan = adapt_research_plan(plan)
    query_counts: dict[str, int] = {}
    for query in typed_plan.query_plan:
        query_counts[query.module] = query_counts.get(query.module, 0) + 1

    lines = [
        "=" * 60,
        "RESEARCH PLAN PREVIEW",
        "=" * 60,
        f"  Plan ID:           {typed_plan.plan_id}",
        f"  Run ID:            {typed_plan.run_id}",
        f"  Planned Modules:   {', '.join(_plan_module_labels(typed_plan.planned_modules)) or 'none'}",
        f"  Estimated Scope:   {typed_plan.estimated_scope or 'Not set'}",
    ]

    if typed_plan.issue_hypotheses:
        lines.append("  Issue Hypotheses:")
        for item in typed_plan.issue_hypotheses:
            lines.append(f"    - {item}")

    if query_counts:
        lines.append("  Query Load:")
        for module_name in typed_plan.planned_modules:
            count = query_counts.get(module_name, 0)
            lines.append(
                f"    - {_PLAN_MODULE_LABELS.get(module_name, module_name)}: {count} queries"
            )

    if typed_plan.preferred_domains:
        lines.append(
            "  Preferred Domains: "
            + ", ".join(typed_plan.preferred_domains[:8])
            + (" ..." if len(typed_plan.preferred_domains) > 8 else "")
        )

    if typed_plan.review_required:
        lines.append("  Review Required:   yes")

    lines.append("=" * 60)
    return "\n".join(lines)


def build_run_timeline(
    intake: Mapping[str, Any] | CaseIntake,
    research_plan: Mapping[str, Any] | ResearchPlan,
    weather: Mapping[str, Any] | WeatherBrief,
    carrier: Mapping[str, Any] | CarrierDocPack,
    caselaw: Mapping[str, Any] | CaseLawPack,
    citecheck: Mapping[str, Any] | CitationVerifyPack,
    *,
    environment: str = "notebook",
    export_written: bool = False,
) -> tuple[Run, list[RunStage]]:
    """Derive canonical run and stage state from the current notebook-era flow."""

    typed_plan = adapt_research_plan(research_plan)
    memo_input = memo_render_input_from_parts(
        intake,
        weather,
        carrier,
        caselaw,
        citecheck,
        typed_plan.query_plan,
    )
    audit_snapshot = run_audit_snapshot_from_memo_input(memo_input)
    run_id = typed_plan.run_id
    created_at = typed_plan.created_at or audit_snapshot.export_artifact.created_at
    started_at, completed_at = _timeline_bounds(
        [
            *memo_input.weather.retrieval_tasks,
            *memo_input.carrier.retrieval_tasks,
            *memo_input.caselaw.retrieval_tasks,
            *memo_input.citecheck.retrieval_tasks,
        ],
        fallback=created_at,
    )

    stages = [
        RunStage(
            stage_id=f"{run_id}:intake_validation",
            run_id=run_id,
            stage_key="intake_validation",
            status="completed",
            summary=(
                f"Validated required intake fields for {memo_input.intake.event_name} in "
                f"{memo_input.intake.county} County, {memo_input.intake.state}."
            ),
            started_at=created_at,
            completed_at=created_at,
        ),
        RunStage(
            stage_id=f"{run_id}:research_plan",
            run_id=run_id,
            stage_key="research_plan",
            status="degraded" if typed_plan.review_required else "completed",
            review_required=typed_plan.review_required,
            summary=(
                f"{len(typed_plan.query_plan)} queries across "
                f"{len(typed_plan.planned_modules)} planned modules."
            ),
            error_summary="Research plan marked review-required."
            if typed_plan.review_required
            else "",
            started_at=created_at,
            completed_at=created_at,
        ),
        _module_stage(
            run_id,
            "weather",
            primary_count=len(memo_input.weather.sources),
            retrieval_tasks=memo_input.weather.retrieval_tasks,
            warnings=memo_input.weather.warnings or [],
            summary=(
                f"{len(memo_input.weather.sources)} sources, "
                f"{len(memo_input.weather.key_observations)} observations, "
                f"{len(memo_input.weather.retrieval_tasks)} retrieval tasks."
            ),
        ),
        _module_stage(
            run_id,
            "carrier",
            primary_count=len(memo_input.carrier.document_pack),
            retrieval_tasks=memo_input.carrier.retrieval_tasks,
            warnings=memo_input.carrier.warnings or [],
            summary=(
                f"{len(memo_input.carrier.document_pack)} documents, "
                f"{len(memo_input.carrier.common_defenses)} defenses, "
                f"{len(memo_input.carrier.retrieval_tasks)} retrieval tasks."
            ),
        ),
        _module_stage(
            run_id,
            "caselaw",
            primary_count=sum(len(issue.cases) for issue in memo_input.caselaw.issues),
            retrieval_tasks=memo_input.caselaw.retrieval_tasks,
            warnings=memo_input.caselaw.warnings or [],
            summary=(
                f"{len(memo_input.caselaw.issues)} issues, "
                f"{sum(len(issue.cases) for issue in memo_input.caselaw.issues)} authorities, "
                f"{len(memo_input.caselaw.retrieval_tasks)} retrieval tasks."
            ),
        ),
        _citation_stage(run_id, memo_input.citecheck),
        RunStage(
            stage_id=f"{run_id}:memo_assembly",
            run_id=run_id,
            stage_key="memo_assembly",
            status="degraded" if audit_snapshot.review_events else "completed",
            review_required=bool(audit_snapshot.review_events),
            summary=(
                f"{len(audit_snapshot.evidence_items)} evidence items, "
                f"{len(audit_snapshot.evidence_clusters)} evidence clusters, "
                f"{len(audit_snapshot.memo_claims)} memo claims."
            ),
            error_summary=(
                f"{len(audit_snapshot.review_events)} review events require follow-up."
                if audit_snapshot.review_events
                else ""
            ),
            started_at=completed_at,
            completed_at=completed_at,
        ),
        RunStage(
            stage_id=f"{run_id}:export",
            run_id=run_id,
            stage_key="export",
            status="completed" if export_written else "skipped",
            summary=(
                f"Export artifact ready: {audit_snapshot.export_artifact.artifact_id}"
                if export_written
                else "Export not written in this flow."
            ),
            started_at=completed_at if export_written else None,
            completed_at=completed_at if export_written else None,
        ),
    ]

    run = Run(
        run_id=run_id,
        environment=environment,
        status=_overall_run_status(stages),
        review_required=any(
            stage.review_required for stage in stages if stage.stage_key in _REVIEWABLE_STAGE_KEYS
        ),
        created_at=created_at,
        started_at=started_at,
        completed_at=completed_at,
        plan_id=typed_plan.plan_id,
        latest_export_artifact_id=(
            audit_snapshot.export_artifact.artifact_id if export_written else None
        ),
    )
    return run, stages


def build_run_timeline_read_model(
    intake: Mapping[str, Any] | CaseIntake,
    research_plan: Mapping[str, Any] | ResearchPlan,
    weather: Mapping[str, Any] | WeatherBrief,
    carrier: Mapping[str, Any] | CarrierDocPack,
    caselaw: Mapping[str, Any] | CaseLawPack,
    citecheck: Mapping[str, Any] | CitationVerifyPack,
    *,
    environment: str = "notebook",
    export_written: bool = False,
) -> RunTimelineReadModel:
    """Build the schema-versioned run-timeline read-model envelope."""

    run, stages = build_run_timeline(
        intake,
        research_plan,
        weather,
        carrier,
        caselaw,
        citecheck,
        environment=environment,
        export_written=export_written,
    )
    return RunTimelineReadModel(run=run, stages=stages)


def format_run_timeline(
    run: Mapping[str, Any] | Run | RunTimelineReadModel,
    stages: Sequence[Mapping[str, Any] | RunStage] | None = None,
) -> str:
    """Render a compact workflow timeline for notebook or CLI output."""

    if _is_timeline_payload(run, stages):
        timeline = adapt_run_timeline(run)
        typed_run = timeline.run
        typed_stages = timeline.stages
    else:
        if stages is None:
            raise ValueError("stages are required when formatting a Run directly.")
        typed_run = adapt_run(run)
        typed_stages = [adapt_run_stage(stage) for stage in stages]

    completed = sum(stage.status == "completed" for stage in typed_stages)
    degraded = sum(stage.status == "degraded" for stage in typed_stages)
    failed = sum(stage.status == "failed" for stage in typed_stages)
    skipped = sum(stage.status == "skipped" for stage in typed_stages)
    lines = [
        "=" * 60,
        "RUN TIMELINE",
        "=" * 60,
        f"  Run ID:            {typed_run.run_id}",
        f"  Environment:       {typed_run.environment}",
        f"  Status:            {typed_run.status}",
        f"  Review Required:   {'yes' if typed_run.review_required else 'no'}",
        (
            "  Stage Summary:     "
            f"{completed} completed, {degraded} degraded, {failed} failed, {skipped} skipped"
        ),
        f"  Next Step:         {_next_step(typed_run, typed_stages)}",
        "",
    ]

    for stage in typed_stages:
        lines.append(
            f"  [{stage.status}] {_STAGE_LABELS.get(stage.stage_key, stage.stage_key)}"
        )
        lines.append(f"    {stage.summary}")
        if stage.review_required and stage.error_summary:
            lines.append(f"    Review: {stage.error_summary}")
        elif stage.error_summary:
            lines.append(f"    Note: {stage.error_summary}")

    lines.append("=" * 60)
    return "\n".join(lines)


def _is_timeline_payload(
    run: Mapping[str, Any] | Run | RunTimelineReadModel,
    stages: Sequence[Mapping[str, Any] | RunStage] | None,
) -> bool:
    return isinstance(run, RunTimelineReadModel) or (
        stages is None
        and isinstance(run, Mapping)
        and "run" in run
        and "stages" in run
    )


def _module_stage(
    run_id: str,
    stage_key: str,
    *,
    primary_count: int,
    retrieval_tasks: list[Any],
    warnings: list[str],
    summary: str,
) -> RunStage:
    status = "completed"
    review_required = bool(warnings) or any(
        task.review_required or task.status in {"degraded", "failed"} for task in retrieval_tasks
    )
    error_summary = "; ".join(warnings)

    if primary_count == 0:
        status = "failed"
        review_required = True
        error_summary = error_summary or "No reviewable output was produced."
    elif review_required:
        status = "degraded"

    started_at, completed_at = _timeline_bounds(retrieval_tasks)
    return RunStage(
        stage_id=f"{run_id}:{stage_key}",
        run_id=run_id,
        stage_key=stage_key,
        status=status,
        review_required=review_required,
        summary=summary,
        error_summary=error_summary,
        started_at=started_at,
        completed_at=completed_at,
    )


def _citation_stage(run_id: str, citecheck: CitationVerifyPack) -> RunStage:
    summary = (
        f"{citecheck.summary.total} checks, "
        f"{citecheck.summary.verified} verified, "
        f"{citecheck.summary.uncertain} uncertain, "
        f"{citecheck.summary.not_found} not found."
    )
    review_required = bool(citecheck.summary.uncertain or citecheck.summary.not_found) or any(
        task.review_required or task.status in {"degraded", "failed"}
        for task in citecheck.retrieval_tasks
    )
    status = "completed"
    error_summary = ""

    if citecheck.summary.total == 0:
        status = "failed"
        review_required = True
        error_summary = "No citation checks were produced."
    elif review_required:
        status = "degraded"
        error_summary = (
            f"{citecheck.summary.uncertain} uncertain and "
            f"{citecheck.summary.not_found} not found citations require review."
        )

    started_at, completed_at = _timeline_bounds(citecheck.retrieval_tasks)
    return RunStage(
        stage_id=f"{run_id}:citation_verify",
        run_id=run_id,
        stage_key="citation_verify",
        status=status,
        review_required=review_required,
        summary=summary,
        error_summary=error_summary,
        started_at=started_at,
        completed_at=completed_at,
    )


def _overall_run_status(stages: list[RunStage]) -> str:
    failed_output_stages = [
        stage for stage in stages if stage.stage_key in _OUTPUT_STAGE_KEYS and stage.status == "failed"
    ]
    usable_output_stages = [
        stage
        for stage in stages
        if stage.stage_key in _OUTPUT_STAGE_KEYS and stage.status in {"completed", "degraded"}
    ]
    if failed_output_stages and usable_output_stages:
        return "partial_success"
    if failed_output_stages:
        return "failed"
    return "completed"


def _next_step(run: Run, stages: list[RunStage]) -> str:
    export_stage = next((stage for stage in stages if stage.stage_key == "export"), None)
    if run.status == "failed":
        return "Return to intake or plan review before relying on output."
    if run.review_required:
        return "Move into evidence review before relying on memo language."
    if export_stage is not None and export_stage.status != "completed":
        return "Export is optional; evidence review is ready now."
    return "Memo and audit bundle are ready for attorney review."


def _timeline_bounds(
    retrieval_tasks: list[Any],
    *,
    fallback: dt.datetime | None = None,
) -> tuple[dt.datetime | None, dt.datetime | None]:
    started_at = min(
        (task.requested_at for task in retrieval_tasks if task.requested_at is not None),
        default=fallback,
    )
    completed_at = max(
        (task.completed_at for task in retrieval_tasks if task.completed_at is not None),
        default=started_at or fallback,
    )
    return started_at, completed_at


def _plan_module_labels(modules: list[str]) -> list[str]:
    return [_PLAN_MODULE_LABELS.get(module_name, module_name) for module_name in modules]
