"""Export-history read model helpers derived from the audit snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from war_room.models import (
    CaseIntake,
    CaseLawPack,
    CarrierDocPack,
    CitationVerifyPack,
    QuerySpec,
    RunAuditSnapshot,
    WeatherBrief,
    adapt_run_audit_snapshot,
    run_audit_snapshot_from_parts,
)


@dataclass(frozen=True)
class ExportHistoryEntry:
    """Single export-history row for the current run."""

    artifact_id: str
    artifact_type: str
    title: str
    artifact_uri: str
    created_at: str
    disclaimer_present: bool
    review_required: bool
    run_status: str
    delivery_state: str
    audit_snapshot_ref: str


@dataclass(frozen=True)
class ExportHistoryReadModel:
    """Export-history read model for notebook-era flows."""

    run_id: str
    entries: list[ExportHistoryEntry] = field(default_factory=list)
    review_required_export_count: int = 0


def build_export_history(
    snapshot: Mapping[str, Any] | RunAuditSnapshot,
    *,
    run_status: str,
    export_written: bool,
    artifact_uri: str | None = None,
) -> ExportHistoryReadModel:
    """Build an export-history read model from the canonical audit snapshot."""

    typed_snapshot = adapt_run_audit_snapshot(snapshot)
    artifact = typed_snapshot.export_artifact
    resolved_uri = artifact_uri or artifact.uri
    entry = ExportHistoryEntry(
        artifact_id=artifact.artifact_id,
        artifact_type=artifact.artifact_type,
        title=artifact.title,
        artifact_uri=resolved_uri,
        created_at=artifact.created_at.isoformat() if artifact.created_at is not None else "",
        disclaimer_present=bool(artifact.disclaimer.strip()),
        review_required=artifact.review_required,
        run_status=run_status,
        delivery_state="written" if export_written else "not_written",
        audit_snapshot_ref=f"run_audit_snapshot:{artifact.run_id}",
    )
    return ExportHistoryReadModel(
        run_id=artifact.run_id,
        entries=[entry],
        review_required_export_count=1 if artifact.review_required else 0,
    )


def build_export_history_from_parts(
    intake: Mapping[str, Any] | CaseIntake,
    weather: Mapping[str, Any] | WeatherBrief,
    carrier: Mapping[str, Any] | CarrierDocPack,
    caselaw: Mapping[str, Any] | CaseLawPack,
    citecheck: Mapping[str, Any] | CitationVerifyPack,
    query_plan: list[Mapping[str, Any] | QuerySpec],
    *,
    run_status: str,
    export_written: bool,
    artifact_uri: str | Path | None = None,
) -> ExportHistoryReadModel:
    """Build the read model directly from current notebook-era module outputs."""

    return build_export_history(
        run_audit_snapshot_from_parts(
            intake,
            weather,
            carrier,
            caselaw,
            citecheck,
            query_plan,
        ),
        run_status=run_status,
        export_written=export_written,
        artifact_uri=str(artifact_uri) if artifact_uri is not None else None,
    )


def format_export_history(history: ExportHistoryReadModel) -> str:
    """Render the export-history read model as a notebook-friendly text block."""

    lines = [
        "=" * 60,
        "EXPORT HISTORY",
        "=" * 60,
        f"  Run ID:            {history.run_id}",
        f"  Artifacts:         {len(history.entries)}",
        f"  Review Required:   {history.review_required_export_count} exports",
        "",
    ]

    for entry in history.entries:
        review_state = "review_required" if entry.review_required else "ready"
        lines.append(f"  [{entry.delivery_state}] {entry.artifact_type} | {review_state}")
        lines.append(f"    Artifact ID: {entry.artifact_id}")
        lines.append(f"    Run status: {entry.run_status}")
        lines.append(f"    URI: {entry.artifact_uri}")
        lines.append(
            f"    Disclaimer: {'present' if entry.disclaimer_present else 'missing'} | "
            f"Audit ref: {entry.audit_snapshot_ref}"
        )
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)
