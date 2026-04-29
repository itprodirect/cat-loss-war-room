"""Typed domain models for core pipeline contracts."""

from __future__ import annotations

import datetime as dt
import re
from typing import Any, Literal, Mapping, Sequence
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from war_room.source_scoring import score_url

POSTURE_VALUE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
SCHEMA_VERSION_DEFAULT = "v2alpha1"

RunStatus = Literal["queued", "running", "partial_success", "failed", "completed", "cancelled"]
RunStageStatus = Literal["not_started", "in_progress", "completed", "degraded", "failed", "skipped"]
RunStageKey = Literal[
    "intake_validation",
    "research_plan",
    "weather",
    "carrier",
    "caselaw",
    "citation_verify",
    "memo_assembly",
    "export",
]
MemoSectionStatus = Literal["draft", "review_required", "ready"]
LegalIssueStatus = Literal["open", "review_required", "resolved"]
RunEventSeverity = Literal["info", "warning", "error"]
RetrievalTaskStatus = Literal["queued", "running", "completed", "failed", "degraded", "cancelled"]


def _validate_schema_version(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("schema_version must be non-empty.")
    return cleaned


def _validate_non_empty_string_list(value: list[str], field_name: str) -> list[str]:
    for token in value:
        if not token:
            raise ValueError(f"{field_name} values must be non-empty strings.")
    return value


class CaseIntake(BaseModel):
    """Structured case intake for a CAT loss matter."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_name: str = Field(min_length=1)
    event_date: str = Field(min_length=1)
    state: str = Field(min_length=1)
    county: str = Field(min_length=1)
    carrier: str = Field(min_length=1)
    policy_type: str = Field(min_length=1)
    posture: list[str] = Field(default_factory=lambda: ["denial"])
    key_facts: list[str] = Field(default_factory=list)
    coverage_issues: list[str] = Field(default_factory=list)

    @field_validator("event_date")
    @classmethod
    def _validate_event_date(cls, value: str) -> str:
        try:
            dt.date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("event_date must be a valid date in YYYY-MM-DD format.") from exc
        return value

    @field_validator("posture")
    @classmethod
    def _validate_posture(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("posture must contain at least one value.")

        for token in value:
            if not POSTURE_VALUE_PATTERN.fullmatch(token):
                raise ValueError(
                    "posture values must use snake_case tokens like 'bad_faith'."
                )
        return value

    @field_validator("key_facts", "coverage_issues")
    @classmethod
    def _validate_string_lists(cls, value: list[str]) -> list[str]:
        for token in value:
            if not token:
                raise ValueError("list items must be non-empty strings.")
        return value

    def summary(self) -> str:
        """One-line case summary."""
        return (
            f"{self.event_name} | {self.carrier} | "
            f"{self.county} County, {self.state} | "
            f"{self.policy_type} | Posture: {', '.join(self.posture)}"
        )

    def format_card(self) -> str:
        """Multi-line formatted intake card for display."""
        lines = [
            "=" * 60,
            "CASE INTAKE",
            "=" * 60,
            f"  Event:       {self.event_name} ({self.event_date})",
            f"  Location:    {self.county} County, {self.state}",
            f"  Carrier:     {self.carrier}",
            f"  Policy:      {self.policy_type}",
            f"  Posture:     {', '.join(self.posture)}",
        ]
        if self.key_facts:
            lines.append(f"  Key Facts:   {'; '.join(self.key_facts)}")
        if self.coverage_issues:
            lines.append(f"  Issues:      {'; '.join(self.coverage_issues)}")
        lines.append("=" * 60)
        return "\n".join(lines)


class QuerySpec(BaseModel):
    """A single search query specification."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    module: str = Field(min_length=1)
    query: str = Field(min_length=1)
    category: str = Field(min_length=1)
    date_start: str | None = None
    date_end: str | None = None
    preferred_domains: list[str] = Field(default_factory=list)

    @field_validator("preferred_domains")
    @classmethod
    def _validate_domains(cls, value: list[str]) -> list[str]:
        for domain in value:
            if not domain:
                raise ValueError("preferred_domains values must be non-empty strings.")
        return value

    def format_row(self) -> str:
        """Format as a display row."""
        date_range = ""
        if self.date_start and self.date_end:
            date_range = f" [{self.date_start} -> {self.date_end}]"
        elif self.date_start:
            date_range = f" [from {self.date_start}]"
        domains = ""
        if self.preferred_domains:
            domains = f" (prefer: {', '.join(self.preferred_domains)})"
        return f"  [{self.category}] {self.query}{date_range}{domains}"


class ResearchPlan(BaseModel):
    """Canonical research-plan contract for a run."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: str = SCHEMA_VERSION_DEFAULT
    plan_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    planned_modules: list[str] = Field(default_factory=list)
    issue_hypotheses: list[str] = Field(default_factory=list)
    query_plan: list[QuerySpec] = Field(default_factory=list)
    preferred_domains: list[str] = Field(default_factory=list)
    estimated_scope: str = ""
    review_required: bool = False
    created_at: dt.datetime | None = None

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        return _validate_schema_version(value)

    @field_validator("planned_modules", "issue_hypotheses", "preferred_domains")
    @classmethod
    def _validate_string_lists(cls, value: list[str], info: Any) -> list[str]:
        return _validate_non_empty_string_list(value, info.field_name)


class Run(BaseModel):
    """Top-level canonical execution record."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: str = SCHEMA_VERSION_DEFAULT
    run_id: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    status: RunStatus = "queued"
    review_required: bool = False
    created_at: dt.datetime | None = None
    started_at: dt.datetime | None = None
    completed_at: dt.datetime | None = None
    intake_id: str | None = None
    plan_id: str | None = None
    latest_export_artifact_id: str | None = None

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        return _validate_schema_version(value)


class RunStage(BaseModel):
    """Canonical stage-level progress record."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    stage_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    stage_key: RunStageKey
    status: RunStageStatus = "not_started"
    review_required: bool = False
    started_at: dt.datetime | None = None
    completed_at: dt.datetime | None = None
    summary: str = ""
    error_summary: str = ""


class RunEvent(BaseModel):
    """Append-only operational event for a run."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    run_event_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    stage_id: str | None = None
    event_type: str = Field(min_length=1)
    severity: RunEventSeverity = "info"
    message: str = Field(min_length=1)
    created_at: dt.datetime | None = None
    artifact_refs: list[str] = Field(default_factory=list)

    @field_validator("artifact_refs")
    @classmethod
    def _validate_artifact_refs(cls, value: list[str]) -> list[str]:
        return _validate_non_empty_string_list(value, "artifact_refs")


class RetrievalTask(BaseModel):
    """Provider-facing retrieval work unit for a run."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    retrieval_task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    stage_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    query_text: str = Field(min_length=1)
    status: RetrievalTaskStatus = "queued"
    attempt_count: int = Field(default=0, ge=0)
    requested_at: dt.datetime | None = None
    completed_at: dt.datetime | None = None
    raw_artifact_refs: list[str] = Field(default_factory=list)
    review_required: bool = False

    @field_validator("raw_artifact_refs")
    @classmethod
    def _validate_raw_artifact_refs(cls, value: list[str]) -> list[str]:
        return _validate_non_empty_string_list(value, "raw_artifact_refs")


class MemoSection(BaseModel):
    """Section-level memo composition container."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    section_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: MemoSectionStatus = "draft"
    issue_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    review_required: bool = False

    @field_validator("issue_ids", "claim_ids")
    @classmethod
    def _validate_string_lists(cls, value: list[str], info: Any) -> list[str]:
        return _validate_non_empty_string_list(value, info.field_name)


class SourceReference(BaseModel):
    """Canonical source reference for module outputs."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = ""
    url: str = Field(min_length=1)
    badge: str = Field(min_length=1)
    reason: str | None = None
    source_class: str | None = None
    is_primary_authority: bool = False


class WeatherMetrics(BaseModel):
    """Normalized weather metric container."""

    model_config = ConfigDict(extra="forbid")

    max_wind_mph: int | None = None
    storm_surge_ft: float | None = None
    rain_in: float | None = None


class WeatherBrief(BaseModel):
    """Typed weather module payload."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    module: Literal["weather"] = "weather"
    event_summary: str = Field(min_length=1)
    key_observations: list[str] = Field(default_factory=list)
    metrics: WeatherMetrics
    sources: list[SourceReference] = Field(default_factory=list)
    warnings: list[str] | None = None
    retrieval_tasks: list[RetrievalTask] = Field(default_factory=list)
    run_events: list[RunEvent] = Field(default_factory=list)


class CarrierSnapshot(BaseModel):
    """Carrier context for a run."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    state: str = Field(min_length=1)
    event: str = Field(min_length=1)
    policy_type: str = Field(min_length=1)


class CarrierDocument(BaseModel):
    """Single document row in the carrier pack."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    doc_type: str = Field(min_length=1)
    title: str = ""
    url: str = Field(min_length=1)
    badge: str = Field(min_length=1)
    why_it_matters: str = Field(min_length=1)


class CarrierDocPack(BaseModel):
    """Typed carrier module payload."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    module: Literal["carrier"] = "carrier"
    carrier_snapshot: CarrierSnapshot
    document_pack: list[CarrierDocument] = Field(default_factory=list)
    common_defenses: list[str] = Field(default_factory=list)
    rebuttal_angles: list[str] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)
    warnings: list[str] | None = None
    retrieval_tasks: list[RetrievalTask] = Field(default_factory=list)
    run_events: list[RunEvent] = Field(default_factory=list)


class CaseEntry(BaseModel):
    """Single case summary in a legal issue bucket."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = ""
    citation: str = ""
    court: str = ""
    year: str = ""
    one_liner: str = ""
    url: str = Field(min_length=1)
    badge: str = Field(min_length=1)
    source_class: str | None = None
    source_tier: str | None = None
    is_primary_authority: bool = False


class CaseIssue(BaseModel):
    """Case-law issue grouping."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    issue: str = Field(min_length=1)
    cases: list[CaseEntry] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CaseLawPack(BaseModel):
    """Typed caselaw module payload."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    module: Literal["caselaw"] = "caselaw"
    issues: list[CaseIssue] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)
    warnings: list[str] | None = None
    retrieval_tasks: list[RetrievalTask] = Field(default_factory=list)
    run_events: list[RunEvent] = Field(default_factory=list)


class LegalIssue(BaseModel):
    """Canonical issue-oriented analysis node for a run."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    issue_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    summary: str = ""
    status: LegalIssueStatus = "open"
    evidence_cluster_ids: list[str] = Field(default_factory=list)
    case_candidate_ids: list[str] = Field(default_factory=list)
    review_required: bool = False

    @field_validator("evidence_cluster_ids", "case_candidate_ids")
    @classmethod
    def _validate_string_lists(cls, value: list[str], info: Any) -> list[str]:
        return _validate_non_empty_string_list(value, info.field_name)


class CaseCandidate(BaseModel):
    """Canonical case-authority record attached to a legal issue."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    case_candidate_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    issue_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    citation: str = ""
    court: str = ""
    year: str = ""
    url: str = Field(min_length=1)
    source_tier: str = Field(min_length=1)
    summary: str = ""
    review_required: bool = False


class CitationCheck(BaseModel):
    """Single citation spot-check outcome."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: Literal["verified", "uncertain", "not_found"]
    badge: str = Field(min_length=1)
    source_url: str | None = None
    note: str = Field(min_length=1)
    case_name: str = ""
    citation: str = ""
    confidence: Literal["high", "medium", "low"] = "low"
    status_reason: str = ""
    trust_explanation: str = ""
    source_tier: str | None = None
    source_class: str | None = None
    is_primary_authority: bool = False
    alternate_candidate_count: int = Field(default=0, ge=0)


class CitationSummary(BaseModel):
    """Aggregate citation spot-check counts."""

    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    verified: int = Field(ge=0)
    uncertain: int = Field(ge=0)
    not_found: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate_total(self) -> "CitationSummary":
        if self.total != self.verified + self.uncertain + self.not_found:
            raise ValueError("summary total must equal verified + uncertain + not_found")
        return self


class CitationVerifyPack(BaseModel):
    """Typed citation-verify module payload."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    module: Literal["citation_verify"] = "citation_verify"
    disclaimer: str = Field(min_length=1)
    checks: list[CitationCheck] = Field(default_factory=list)
    summary: CitationSummary
    retrieval_tasks: list[RetrievalTask] = Field(default_factory=list)
    run_events: list[RunEvent] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    """Canonical evidence record derived from module outputs."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    evidence_id: str = Field(min_length=1)
    module: Literal["weather", "carrier", "caselaw", "citation_verify"]
    evidence_type: str = Field(min_length=1)
    title: str = ""
    summary: str = ""
    url: str | None = None
    badge: str = Field(min_length=1)
    source_reason: str | None = None
    source_class: str | None = None
    source_tier: str | None = None
    is_primary_authority: bool = False
    authority_key: str | None = None
    issue: str | None = None
    citation: str | None = None
    review_required: bool = False


class EvidenceCluster(BaseModel):
    """Normalized evidence grouping keyed by citation or URL."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    cluster_id: str = Field(min_length=1)
    cluster_type: Literal["citation", "url", "derived"]
    label: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    modules: list[str] = Field(default_factory=list)
    citation: str | None = None
    url: str | None = None
    authority_key: str | None = None
    provenance_urls: list[str] = Field(default_factory=list)
    member_count: int = Field(default=0, ge=0)
    review_required: bool = False


class QualitySnapshot(BaseModel):
    """Lightweight structured retrieval-quality telemetry for one memo run."""

    model_config = ConfigDict(extra="forbid")

    source_class_counts: dict[str, int] = Field(default_factory=dict)
    primary_source_count: int = Field(default=0, ge=0)
    secondary_source_count: int = Field(default=0, ge=0)
    citation_status_counts: dict[str, int] = Field(default_factory=dict)
    citation_reason_counts: dict[str, int] = Field(default_factory=dict)
    evidence_item_count: int = Field(default=0, ge=0)
    evidence_cluster_count: int = Field(default=0, ge=0)
    grouped_evidence_count: int = Field(default=0, ge=0)
    raw_evidence_count: int = Field(default=0, ge=0)
    normalized_authority_count: int = Field(default=0, ge=0)
    duplicate_authority_count: int = Field(default=0, ge=0)
    provenance_link_count: int = Field(default=0, ge=0)


class MemoClaim(BaseModel):
    """Evidence-linked memo assertion for audit purposes."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    claim_id: str = Field(min_length=1)
    section: str = Field(min_length=1)
    text: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    cluster_ids: list[str] = Field(default_factory=list)
    status: Literal["supported", "review_required"] = "supported"


class ReviewEvent(BaseModel):
    """Review-required event emitted during memo assembly."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_id: str = Field(min_length=1)
    run_id: str = Field(default="")
    event_type: Literal["warning", "citation_uncertain", "citation_not_found", "human_override", "missing_support"]
    label: str = Field(min_length=1)
    detail: str = Field(min_length=1)
    module: str | None = None
    target_type: str = Field(default="")
    target_ids: list[str] = Field(default_factory=list)
    related_evidence_ids: list[str] = Field(default_factory=list)
    related_cluster_ids: list[str] = Field(default_factory=list)
    related_claim_ids: list[str] = Field(default_factory=list)
    related_stage_id: str | None = None
    created_at: dt.datetime | None = None


class ExportArtifact(BaseModel):
    """Export metadata for the generated memo artifact."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    artifact_id: str = Field(default="")
    run_id: str = Field(default="")
    artifact_type: Literal["markdown_memo"] = "markdown_memo"
    title: str = Field(min_length=1)
    disclaimer: str = Field(min_length=1)
    uri: str = Field(default="")
    section_ids: list[str] = Field(default_factory=list)
    review_required: bool = False
    created_at: dt.datetime | None = None
    section_titles: list[str] = Field(default_factory=list)


class MemoRenderInput(BaseModel):
    """Typed contract for markdown memo rendering input."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION_DEFAULT
    intake: CaseIntake
    weather: WeatherBrief
    carrier: CarrierDocPack
    caselaw: CaseLawPack
    citecheck: CitationVerifyPack
    query_plan: list[QuerySpec] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        return _validate_schema_version(value)


class RunAuditSnapshot(BaseModel):
    """Canonical audit snapshot for a rendered research memo."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION_DEFAULT
    intake: CaseIntake
    query_plan: list[QuerySpec] = Field(default_factory=list)
    retrieval_tasks: list[RetrievalTask] = Field(default_factory=list)
    run_events: list[RunEvent] = Field(default_factory=list)
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
    evidence_clusters: list[EvidenceCluster] = Field(default_factory=list)
    memo_claims: list[MemoClaim] = Field(default_factory=list)
    review_events: list[ReviewEvent] = Field(default_factory=list)
    quality_snapshot: QualitySnapshot = Field(default_factory=QualitySnapshot)
    export_artifact: ExportArtifact

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        return _validate_schema_version(value)


class EvidenceBoardItemPreview(BaseModel):
    """Compact evidence-item preview for board rendering."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    evidence_id: str = Field(min_length=1)
    module: str = Field(min_length=1)
    title: str = ""
    summary: str = ""
    badge: str = Field(min_length=1)
    source_tier: str = Field(min_length=1)
    url: str | None = None


class EvidenceBoardClusterCard(BaseModel):
    """Cluster-first evidence card for the transitional read model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    cluster_id: str = Field(min_length=1)
    cluster_type: str = Field(min_length=1)
    label: str = Field(min_length=1)
    member_count: int = Field(ge=0)
    modules: list[str] = Field(default_factory=list)
    source_tier_summary: str = ""
    issue_labels: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    review_event_ids: list[str] = Field(default_factory=list)
    provenance_urls: list[str] = Field(default_factory=list)
    review_required: bool = False
    evidence_previews: list[EvidenceBoardItemPreview] = Field(default_factory=list)

    @field_validator(
        "modules",
        "issue_labels",
        "claim_ids",
        "review_event_ids",
        "provenance_urls",
    )
    @classmethod
    def _validate_string_lists(cls, value: list[str], info: Any) -> list[str]:
        return _validate_non_empty_string_list(value, info.field_name)


class EvidenceBoardReadModel(BaseModel):
    """Cluster-first evidence-board read model for current notebook-era flows."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    schema_version: str = SCHEMA_VERSION_DEFAULT
    run_id: str = Field(min_length=1)
    total_clusters: int = Field(ge=0)
    total_evidence_items: int = Field(ge=0)
    review_required_clusters: int = Field(ge=0)
    primary_source_count: int = Field(ge=0)
    secondary_source_count: int = Field(ge=0)
    fallback_to_item_view: bool = False
    cluster_cards: list[EvidenceBoardClusterCard] = Field(default_factory=list)
    ungrouped_items: list[EvidenceBoardItemPreview] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        return _validate_schema_version(value)


class IssueWorkspaceCaseCandidate(BaseModel):
    """Compact authority row for an issue workspace."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    evidence_id: str = Field(min_length=1)
    name: str = ""
    citation: str = ""
    source_tier: str = Field(min_length=1)
    badge: str = Field(min_length=1)
    summary: str = ""
    url: str | None = None


class IssueWorkspaceCitationOutcome(BaseModel):
    """Citation-check outcome linked to an issue workspace."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    evidence_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    citation: str = ""
    note: str = ""
    source_tier: str = Field(min_length=1)
    url: str | None = None


class IssueWorkspaceCard(BaseModel):
    """Issue-level read model derived from current canonical graph objects."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    issue_label: str = Field(min_length=1)
    summary: str = ""
    status: Literal["review_required", "ready"]
    evidence_cluster_ids: list[str] = Field(default_factory=list)
    case_candidates: list[IssueWorkspaceCaseCandidate] = Field(default_factory=list)
    citation_outcomes: list[IssueWorkspaceCitationOutcome] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    review_event_ids: list[str] = Field(default_factory=list)
    review_required: bool = False

    @field_validator("evidence_cluster_ids", "claim_ids", "review_event_ids")
    @classmethod
    def _validate_string_lists(cls, value: list[str], info: Any) -> list[str]:
        return _validate_non_empty_string_list(value, info.field_name)


class IssueWorkspaceReadModel(BaseModel):
    """Issue-workspace read model for notebook-era flows."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    schema_version: str = SCHEMA_VERSION_DEFAULT
    run_id: str = Field(min_length=1)
    issue_cards: list[IssueWorkspaceCard] = Field(default_factory=list)
    review_required_issue_count: int = Field(default=0, ge=0)

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        return _validate_schema_version(value)


class MemoComposerClaimLink(BaseModel):
    """Claim-level support row for a memo section."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    claim_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    status: Literal["supported", "review_required"]
    cluster_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("cluster_ids", "evidence_ids")
    @classmethod
    def _validate_string_lists(cls, value: list[str], info: Any) -> list[str]:
        return _validate_non_empty_string_list(value, info.field_name)


class MemoComposerSectionCard(BaseModel):
    """Section-first memo-composer card."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    section_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: MemoSectionStatus
    claim_links: list[MemoComposerClaimLink] = Field(default_factory=list)
    review_event_ids: list[str] = Field(default_factory=list)
    review_required: bool = False

    @field_validator("review_event_ids")
    @classmethod
    def _validate_review_event_ids(cls, value: list[str]) -> list[str]:
        return _validate_non_empty_string_list(value, "review_event_ids")


class MemoComposerReadModel(BaseModel):
    """Memo-composer read model for notebook-era flows."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    schema_version: str = SCHEMA_VERSION_DEFAULT
    run_id: str = Field(min_length=1)
    export_eligibility: Literal["review_required_export", "ready_to_export"]
    review_required_section_count: int = Field(ge=0)
    section_cards: list[MemoComposerSectionCard] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        return _validate_schema_version(value)


def adapt_case_intake(payload: Mapping[str, Any] | CaseIntake) -> CaseIntake:
    """Validate/coerce intake payload into typed model."""
    if isinstance(payload, CaseIntake):
        return payload
    return CaseIntake.model_validate(payload)


def adapt_query_spec(payload: Mapping[str, Any] | QuerySpec) -> QuerySpec:
    """Validate/coerce query spec payload into typed model."""
    if isinstance(payload, QuerySpec):
        return payload
    return QuerySpec.model_validate(payload)


def adapt_query_plan(
    payload: Sequence[Mapping[str, Any] | QuerySpec],
) -> list[QuerySpec]:
    """Validate/coerce a mixed query-plan payload into typed query specs."""
    return [adapt_query_spec(item) for item in payload]


def adapt_research_plan(payload: Mapping[str, Any] | ResearchPlan) -> ResearchPlan:
    """Validate/coerce research-plan payload into typed model."""
    if isinstance(payload, ResearchPlan):
        return payload
    return ResearchPlan.model_validate(payload)


def adapt_run(payload: Mapping[str, Any] | Run) -> Run:
    """Validate/coerce run payload into typed model."""
    if isinstance(payload, Run):
        return payload
    return Run.model_validate(payload)


def adapt_run_stage(payload: Mapping[str, Any] | RunStage) -> RunStage:
    """Validate/coerce run-stage payload into typed model."""
    if isinstance(payload, RunStage):
        return payload
    return RunStage.model_validate(payload)


def adapt_run_event(payload: Mapping[str, Any] | RunEvent) -> RunEvent:
    """Validate/coerce run-event payload into typed model."""
    if isinstance(payload, RunEvent):
        return payload
    return RunEvent.model_validate(payload)


def adapt_retrieval_task(payload: Mapping[str, Any] | RetrievalTask) -> RetrievalTask:
    """Validate/coerce retrieval-task payload into typed model."""
    if isinstance(payload, RetrievalTask):
        return payload
    return RetrievalTask.model_validate(payload)


def adapt_memo_section(payload: Mapping[str, Any] | MemoSection) -> MemoSection:
    """Validate/coerce memo-section payload into typed model."""
    if isinstance(payload, MemoSection):
        return payload
    return MemoSection.model_validate(payload)


def adapt_weather_brief(payload: Mapping[str, Any] | WeatherBrief) -> WeatherBrief:
    """Validate/coerce weather payload into typed model."""
    if isinstance(payload, WeatherBrief):
        return payload
    return WeatherBrief.model_validate(payload)


def adapt_carrier_doc_pack(payload: Mapping[str, Any] | CarrierDocPack) -> CarrierDocPack:
    """Validate/coerce carrier payload into typed model."""
    if isinstance(payload, CarrierDocPack):
        return payload
    return CarrierDocPack.model_validate(payload)


def adapt_caselaw_pack(payload: Mapping[str, Any] | CaseLawPack) -> CaseLawPack:
    """Validate/coerce case-law payload into typed model."""
    if isinstance(payload, CaseLawPack):
        return payload
    return CaseLawPack.model_validate(payload)


def adapt_legal_issue(payload: Mapping[str, Any] | LegalIssue) -> LegalIssue:
    """Validate/coerce legal-issue payload into typed model."""
    if isinstance(payload, LegalIssue):
        return payload
    return LegalIssue.model_validate(payload)


def adapt_case_candidate(payload: Mapping[str, Any] | CaseCandidate) -> CaseCandidate:
    """Validate/coerce case-candidate payload into typed model."""
    if isinstance(payload, CaseCandidate):
        return payload
    return CaseCandidate.model_validate(payload)


def adapt_citation_verify_pack(
    payload: Mapping[str, Any] | CitationVerifyPack,
) -> CitationVerifyPack:
    """Validate/coerce citation-verify payload into typed model."""
    pack = payload if isinstance(payload, CitationVerifyPack) else CitationVerifyPack.model_validate(payload)
    return pack.model_copy(update={"checks": [_enrich_citation_check(check) for check in pack.checks]})


def memo_render_input_from_parts(
    intake: Mapping[str, Any] | CaseIntake,
    weather: Mapping[str, Any] | WeatherBrief,
    carrier: Mapping[str, Any] | CarrierDocPack,
    caselaw: Mapping[str, Any] | CaseLawPack,
    citecheck: Mapping[str, Any] | CitationVerifyPack,
    query_plan: list[Mapping[str, Any] | QuerySpec],
    *,
    schema_version: str = SCHEMA_VERSION_DEFAULT,
) -> MemoRenderInput:
    """Build typed memo-render input from mixed dict/model payloads."""
    return MemoRenderInput(
        schema_version=schema_version,
        intake=adapt_case_intake(intake),
        weather=adapt_weather_brief(weather),
        carrier=adapt_carrier_doc_pack(carrier),
        caselaw=adapt_caselaw_pack(caselaw),
        citecheck=adapt_citation_verify_pack(citecheck),
        query_plan=adapt_query_plan(query_plan),
    )


def adapt_run_audit_snapshot(
    payload: Mapping[str, Any] | RunAuditSnapshot,
) -> RunAuditSnapshot:
    """Validate/coerce a run audit snapshot into the canonical typed contract."""
    if isinstance(payload, RunAuditSnapshot):
        return payload
    return RunAuditSnapshot.model_validate(payload)


def adapt_evidence_board(
    payload: Mapping[str, Any] | EvidenceBoardReadModel,
) -> EvidenceBoardReadModel:
    """Validate/coerce an evidence-board read model into the typed contract."""
    if isinstance(payload, EvidenceBoardReadModel):
        return payload
    return EvidenceBoardReadModel.model_validate(payload)


def adapt_issue_workspace(
    payload: Mapping[str, Any] | IssueWorkspaceReadModel,
) -> IssueWorkspaceReadModel:
    """Validate/coerce an issue-workspace read model into the typed contract."""
    if isinstance(payload, IssueWorkspaceReadModel):
        return payload
    return IssueWorkspaceReadModel.model_validate(payload)


def adapt_memo_composer(
    payload: Mapping[str, Any] | MemoComposerReadModel,
) -> MemoComposerReadModel:
    """Validate/coerce a memo-composer read model into the typed contract."""
    if isinstance(payload, MemoComposerReadModel):
        return payload
    return MemoComposerReadModel.model_validate(payload)


def run_audit_snapshot_from_memo_input(memo_input: MemoRenderInput) -> RunAuditSnapshot:
    """Build a canonical audit snapshot from normalized memo-render input."""
    weather_payload = weather_brief_to_payload(memo_input.weather)
    carrier_payload = carrier_doc_pack_to_payload(memo_input.carrier)
    caselaw_payload = caselaw_pack_to_payload(memo_input.caselaw)
    citecheck_payload = citation_verify_pack_to_payload(memo_input.citecheck)
    run_id = _run_id_from_intake(memo_input.intake)
    created_at = dt.datetime.combine(
        dt.date.fromisoformat(memo_input.intake.event_date),
        dt.time.min,
        tzinfo=dt.UTC,
    )

    evidence_items: list[EvidenceItem] = []
    evidence_ids_by_module = {
        "weather": [],
        "carrier": [],
        "caselaw": [],
        "citation_verify": [],
    }

    weather_observations = weather_payload.get("key_observations", [])
    for index, source in enumerate(weather_payload.get("sources", []), 1):
        evidence_id = f"weather-source-{index}"
        source_profile = score_url(source.get("url", ""), source.get("title", ""))
        summary = (
            weather_observations[index - 1]
            if index <= len(weather_observations)
            else weather_payload.get("event_summary", "")
        )
        evidence_items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                module="weather",
                evidence_type="weather_source",
                title=source.get("title", ""),
                summary=summary,
                url=source.get("url"),
                badge=source.get("badge", ""),
                source_reason=source.get("reason"),
                source_class=source.get("source_class") or source_profile.get("source_class"),
                source_tier=source_profile.get("tier"),
                is_primary_authority=bool(
                    source.get("is_primary_authority", source_profile.get("is_primary_authority"))
                ),
                authority_key=_authority_key_from_parts(
                    url=source.get("url"),
                    title=source.get("title"),
                ),
            )
        )
        evidence_ids_by_module["weather"].append(evidence_id)

    carrier_source_reasons = {
        source.get("url"): source.get("reason")
        for source in carrier_payload.get("sources", [])
        if source.get("url")
    }
    for index, document in enumerate(carrier_payload.get("document_pack", []), 1):
        evidence_id = f"carrier-document-{index}"
        source_profile = score_url(document.get("url", ""), document.get("title", ""))
        evidence_items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                module="carrier",
                evidence_type=document.get("doc_type", "carrier_document").lower().replace(" ", "_"),
                title=document.get("title", ""),
                summary=document.get("why_it_matters", ""),
                url=document.get("url"),
                badge=document.get("badge", ""),
                source_reason=carrier_source_reasons.get(document.get("url")),
                source_class=source_profile.get("source_class"),
                source_tier=source_profile.get("tier"),
                is_primary_authority=bool(source_profile.get("is_primary_authority")),
                authority_key=_authority_key_from_parts(
                    url=document.get("url"),
                    title=document.get("title"),
                ),
            )
        )
        evidence_ids_by_module["carrier"].append(evidence_id)

    caselaw_source_reasons = {
        source.get("url"): source.get("reason")
        for source in caselaw_payload.get("sources", [])
        if source.get("url")
    }
    for issue_index, issue in enumerate(caselaw_payload.get("issues", []), 1):
        for case_index, case in enumerate(issue.get("cases", []), 1):
            evidence_id = f"caselaw-case-{issue_index}-{case_index}"
            source_profile = score_url(case.get("url", ""), case.get("name", ""))
            normalized_citation = _normalize_citation_value(case.get("citation"))
            evidence_items.append(
                EvidenceItem(
                    evidence_id=evidence_id,
                    module="caselaw",
                    evidence_type="case_authority",
                    title=case.get("name", ""),
                    summary=case.get("one_liner", ""),
                    url=case.get("url"),
                    badge=case.get("badge", ""),
                    source_reason=caselaw_source_reasons.get(case.get("url")),
                    source_class=case.get("source_class") or source_profile.get("source_class"),
                    source_tier=case.get("source_tier") or source_profile.get("tier"),
                    is_primary_authority=bool(
                        case.get("is_primary_authority", source_profile.get("is_primary_authority"))
                    ),
                    authority_key=_authority_key_from_parts(
                        citation=normalized_citation,
                        title=case.get("name"),
                        court=case.get("court"),
                        year=case.get("year"),
                        url=case.get("url"),
                    ),
                    issue=issue.get("issue"),
                    citation=normalized_citation,
                )
            )
            evidence_ids_by_module["caselaw"].append(evidence_id)

    for index, check in enumerate(citecheck_payload.get("checks", []), 1):
        evidence_id = f"citation-check-{index}"
        has_source_url = bool(check.get("source_url"))
        normalized_citation = _normalize_citation_value(check.get("citation"))
        source_profile = score_url(
            check.get("source_url") or "",
            check.get("case_name") or check.get("citation") or f"Citation Check {index}",
        )
        evidence_items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                module="citation_verify",
                evidence_type="citation_check",
                title=check.get("case_name") or check.get("citation") or f"Citation Check {index}",
                summary=check.get("note", ""),
                url=check.get("source_url"),
                badge=check.get("badge", ""),
                source_reason=check.get("status"),
                source_class=check.get("source_class") or (source_profile.get("source_class") if has_source_url else None),
                source_tier=check.get("source_tier") or (source_profile.get("tier") if has_source_url else None),
                is_primary_authority=bool(
                    check.get("is_primary_authority", source_profile.get("is_primary_authority")) if has_source_url else False
                ),
                authority_key=_authority_key_from_parts(
                    citation=normalized_citation,
                    title=check.get("case_name"),
                    url=check.get("source_url"),
                ),
                citation=normalized_citation,
                review_required=check.get("status") != "verified",
            )
        )
        evidence_ids_by_module["citation_verify"].append(evidence_id)

    evidence_clusters = _build_evidence_clusters(evidence_items)
    quality_snapshot = _build_quality_snapshot(evidence_items, evidence_clusters, citecheck_payload)

    evidence_cluster_ids_by_evidence_id = {
        evidence_id: cluster.cluster_id
        for cluster in evidence_clusters
        for evidence_id in cluster.evidence_ids
    }

    retrieval_tasks = [
        *memo_input.weather.retrieval_tasks,
        *memo_input.carrier.retrieval_tasks,
        *memo_input.caselaw.retrieval_tasks,
        *memo_input.citecheck.retrieval_tasks,
    ]
    run_events = [
        *memo_input.weather.run_events,
        *memo_input.carrier.run_events,
        *memo_input.caselaw.run_events,
        *memo_input.citecheck.run_events,
    ]
    claim_ids_by_module = {
        "weather": "weather-corroboration",
        "carrier": "carrier-positioning",
        "caselaw": "case-law-support",
        "citation_verify": "citation-check-status",
    }
    review_events: list[ReviewEvent] = []
    for module_key, module_label, payload in (
        ("weather", "Weather", weather_payload),
        ("carrier", "Carrier", carrier_payload),
        ("caselaw", "Case law", caselaw_payload),
    ):
        for index, warning in enumerate(payload.get("warnings", []) or [], 1):
            related_cluster_ids = _cluster_ids_for_evidence_ids(
                evidence_ids_by_module[module_key],
                evidence_cluster_ids_by_evidence_id,
            )
            claim_id = claim_ids_by_module[module_key]
            review_events.append(
                ReviewEvent(
                    event_id=f"{module_key}-warning-{index}",
                    run_id=run_id,
                    event_type="warning",
                    label=f"{module_label} review required",
                    detail=warning,
                    module=module_key,
                    target_type="memo_claim",
                    target_ids=[claim_id],
                    related_evidence_ids=evidence_ids_by_module[module_key],
                    related_cluster_ids=related_cluster_ids,
                    related_claim_ids=[claim_id],
                    created_at=created_at,
                )
            )

    citation_summary = citecheck_payload.get("summary", {})
    uncertain = citation_summary.get("uncertain", 0)
    not_found = citation_summary.get("not_found", 0)
    uncertain_evidence_ids = [
        evidence_id
        for evidence_id, check in zip(
            evidence_ids_by_module["citation_verify"],
            citecheck_payload.get("checks", []),
            strict=False,
        )
        if check.get("status") == "uncertain"
    ]
    not_found_evidence_ids = [
        evidence_id
        for evidence_id, check in zip(
            evidence_ids_by_module["citation_verify"],
            citecheck_payload.get("checks", []),
            strict=False,
        )
        if check.get("status") == "not_found"
    ]
    if uncertain:
        related_cluster_ids = _cluster_ids_for_evidence_ids(
            uncertain_evidence_ids,
            evidence_cluster_ids_by_evidence_id,
        )
        claim_id = claim_ids_by_module["citation_verify"]
        review_events.append(
            ReviewEvent(
                event_id="citation-uncertain",
                run_id=run_id,
                event_type="citation_uncertain",
                label="Citation review required",
                detail=f"{uncertain} citation checks are uncertain.",
                module="citation_verify",
                target_type="memo_claim",
                target_ids=[claim_id],
                related_evidence_ids=uncertain_evidence_ids,
                related_cluster_ids=related_cluster_ids,
                related_claim_ids=[claim_id],
                created_at=created_at,
            )
        )
    if not_found:
        related_cluster_ids = _cluster_ids_for_evidence_ids(
            not_found_evidence_ids,
            evidence_cluster_ids_by_evidence_id,
        )
        claim_id = claim_ids_by_module["citation_verify"]
        review_events.append(
            ReviewEvent(
                event_id="citation-not-found",
                run_id=run_id,
                event_type="citation_not_found",
                label="Citation not found",
                detail=f"{not_found} citation checks were not found on reviewed sources.",
                module="citation_verify",
                target_type="memo_claim",
                target_ids=[claim_id],
                related_evidence_ids=not_found_evidence_ids,
                related_cluster_ids=related_cluster_ids,
                related_claim_ids=[claim_id],
                created_at=created_at,
            )
        )

    review_modules = {event.module for event in review_events if event.module}
    memo_claims = [
        MemoClaim(
            claim_id="weather-corroboration",
            section="Weather Corroboration",
            text=weather_payload.get("event_summary", "Weather evidence assembled."),
            evidence_ids=evidence_ids_by_module["weather"],
            cluster_ids=_cluster_ids_for_evidence_ids(
                evidence_ids_by_module["weather"],
                evidence_cluster_ids_by_evidence_id,
            ),
            status=_claim_status(
                evidence_ids_by_module["weather"],
                "weather" in review_modules,
            ),
        ),
        MemoClaim(
            claim_id="carrier-positioning",
            section="Carrier Document Pack",
            text=_carrier_claim_text(carrier_payload),
            evidence_ids=evidence_ids_by_module["carrier"],
            cluster_ids=_cluster_ids_for_evidence_ids(
                evidence_ids_by_module["carrier"],
                evidence_cluster_ids_by_evidence_id,
            ),
            status=_claim_status(
                evidence_ids_by_module["carrier"],
                "carrier" in review_modules,
            ),
        ),
        MemoClaim(
            claim_id="case-law-support",
            section="Case Law",
            text=_caselaw_claim_text(caselaw_payload),
            evidence_ids=evidence_ids_by_module["caselaw"],
            cluster_ids=_cluster_ids_for_evidence_ids(
                evidence_ids_by_module["caselaw"],
                evidence_cluster_ids_by_evidence_id,
            ),
            status=_claim_status(
                evidence_ids_by_module["caselaw"],
                "caselaw" in review_modules or bool(uncertain or not_found),
            ),
        ),
        MemoClaim(
            claim_id="citation-check-status",
            section="Citation Spot-Check",
            text=citecheck_payload.get("disclaimer", "Citation spot-check completed."),
            evidence_ids=evidence_ids_by_module["citation_verify"],
            cluster_ids=_cluster_ids_for_evidence_ids(
                evidence_ids_by_module["citation_verify"],
                evidence_cluster_ids_by_evidence_id,
            ),
            status=_claim_status(
                evidence_ids_by_module["citation_verify"],
                bool(uncertain or not_found),
            ),
        ),
    ]

    section_titles = [
        "Trust Snapshot",
        "Case Intake",
        "Weather Corroboration",
        "Carrier Document Pack",
        "Case Law",
        "Appendix: Query Plan",
        "Appendix: Quality Snapshot",
        "Appendix: Evidence Clusters",
        "Appendix: Evidence Index",
        "Appendix: All Sources",
        "Methodology & Limitations",
    ]
    if review_events:
        section_titles.insert(9, "Appendix: Review Log")

    section_ids = [_stable_token(title) for title in section_titles]

    return RunAuditSnapshot(
        schema_version=memo_input.schema_version,
        intake=memo_input.intake,
        query_plan=memo_input.query_plan,
        retrieval_tasks=retrieval_tasks,
        run_events=run_events,
        evidence_items=evidence_items,
        evidence_clusters=evidence_clusters,
        memo_claims=memo_claims,
        review_events=review_events,
        quality_snapshot=quality_snapshot,
        export_artifact=ExportArtifact(
            artifact_id=f"{run_id}:artifact:markdown-memo",
            run_id=run_id,
            title="CAT-Loss War Room - Research Memo",
            disclaimer="DEMO RESEARCH MEMO - VERIFY CITATIONS - NOT LEGAL ADVICE",
            uri=f"runs/{run_id}/research-memo.md",
            section_ids=section_ids,
            review_required=bool(review_events),
            created_at=created_at,
            section_titles=section_titles,
        ),
    )


def run_audit_snapshot_from_parts(
    intake: Mapping[str, Any] | CaseIntake,
    weather: Mapping[str, Any] | WeatherBrief,
    carrier: Mapping[str, Any] | CarrierDocPack,
    caselaw: Mapping[str, Any] | CaseLawPack,
    citecheck: Mapping[str, Any] | CitationVerifyPack,
    query_plan: list[Mapping[str, Any] | QuerySpec],
    *,
    schema_version: str = SCHEMA_VERSION_DEFAULT,
) -> RunAuditSnapshot:
    """Build a canonical audit snapshot from mixed dict/model payloads."""
    return run_audit_snapshot_from_memo_input(
        memo_render_input_from_parts(
            intake,
            weather,
            carrier,
            caselaw,
            citecheck,
            query_plan,
            schema_version=schema_version,
        )
    )


def _build_evidence_clusters(evidence_items: list[EvidenceItem]) -> list[EvidenceCluster]:
    """Group evidence by citation first, then URL, then a derived fallback key."""
    grouped: dict[tuple[str, str], list[EvidenceItem]] = {}
    ordered_keys: list[tuple[str, str]] = []

    for item in evidence_items:
        cluster_key = _cluster_key_for_item(item)
        if cluster_key not in grouped:
            grouped[cluster_key] = []
            ordered_keys.append(cluster_key)
        grouped[cluster_key].append(item)

    clusters: list[EvidenceCluster] = []
    for index, cluster_key in enumerate(ordered_keys, 1):
        items = grouped[cluster_key]
        first = items[0]
        modules = list(dict.fromkeys(item.module for item in items))
        label = first.citation or first.title or first.summary or first.evidence_type
        provenance_urls = list(
            dict.fromkeys(item.url for item in items if item.url)
        )
        clusters.append(
            EvidenceCluster(
                cluster_id=f"cluster-{index}",
                cluster_type=cluster_key[0],
                label=label,
                evidence_ids=[item.evidence_id for item in items],
                modules=modules,
                citation=first.citation,
                url=first.url,
                authority_key=first.authority_key,
                provenance_urls=provenance_urls,
                member_count=len(items),
                review_required=any(item.review_required for item in items),
            )
        )

    return clusters


def _build_quality_snapshot(
    evidence_items: list[EvidenceItem],
    evidence_clusters: list[EvidenceCluster],
    citecheck_payload: Mapping[str, Any],
) -> QualitySnapshot:
    evidence_items_by_id = {item.evidence_id: item for item in evidence_items}
    source_class_counts: dict[str, int] = {}
    primary_source_count = 0
    classified_cluster_count = 0
    source_class_rank = {
        "court_opinion": 0,
        "statute_regulation": 1,
        "government_guidance": 2,
        "commentary": 3,
        "news": 4,
        "other": 5,
    }

    for cluster in evidence_clusters:
        cluster_items = [
            evidence_items_by_id[evidence_id]
            for evidence_id in cluster.evidence_ids
            if evidence_id in evidence_items_by_id
        ]
        if not cluster_items:
            continue
        classified_items = [item for item in cluster_items if item.source_class]
        if not classified_items:
            continue
        classified_cluster_count += 1
        best_class = min(
            (
                item.source_class or "other"
                for item in classified_items
            ),
            key=lambda value: source_class_rank.get(value, 9),
        )
        source_class_counts[best_class] = source_class_counts.get(best_class, 0) + 1
        if any(item.is_primary_authority for item in classified_items):
            primary_source_count += 1

    citation_status_counts: dict[str, int] = {}
    citation_reason_counts: dict[str, int] = {}
    for check in citecheck_payload.get("checks", []):
        status = (check.get("status") or "").strip()
        if status:
            citation_status_counts[status] = citation_status_counts.get(status, 0) + 1
        reason = (check.get("status_reason") or "").strip()
        if reason:
            citation_reason_counts[reason] = citation_reason_counts.get(reason, 0) + 1

    evidence_item_count = len(evidence_items)
    evidence_cluster_count = len(evidence_clusters)
    normalized_authority_count = sum(1 for cluster in evidence_clusters if cluster.authority_key)
    provenance_link_count = sum(len(cluster.provenance_urls) for cluster in evidence_clusters)

    return QualitySnapshot(
        source_class_counts=source_class_counts,
        primary_source_count=primary_source_count,
        secondary_source_count=max(0, classified_cluster_count - primary_source_count),
        citation_status_counts=citation_status_counts,
        citation_reason_counts=citation_reason_counts,
        evidence_item_count=evidence_item_count,
        evidence_cluster_count=evidence_cluster_count,
        grouped_evidence_count=max(0, evidence_item_count - evidence_cluster_count),
        raw_evidence_count=evidence_item_count,
        normalized_authority_count=normalized_authority_count,
        duplicate_authority_count=max(0, evidence_item_count - normalized_authority_count),
        provenance_link_count=provenance_link_count,
    )


def _authority_key_from_parts(
    *,
    citation: str | None = None,
    title: str | None = None,
    court: str | None = None,
    year: str | None = None,
    url: str | None = None,
) -> str | None:
    normalized_citation = _normalize_citation_value(citation)
    if normalized_citation:
        return f"citation:{normalized_citation}"

    normalized_name = _normalize_authority_name(title)
    if normalized_name:
        parts = [normalized_name]
        normalized_court = _normalize_authority_name(court)
        if normalized_court:
            parts.append(normalized_court)
        if year:
            parts.append(str(year).strip())
        return "authority:" + "|".join(parts)

    normalized_url = _normalize_cluster_url(url or "")
    if normalized_url:
        return f"url:{normalized_url}"
    return None


def _enrich_citation_check(check: CitationCheck) -> CitationCheck:
    has_source_url = bool(check.source_url)
    source_profile = (
        score_url(
            check.source_url or "",
            check.case_name or check.citation or check.note,
        )
        if has_source_url
        else {}
    )
    source_tier = check.source_tier or (source_profile.get("tier") if has_source_url else None)
    source_class = check.source_class or (source_profile.get("source_class") if has_source_url else None)
    is_primary_authority = bool(
        check.is_primary_authority
        or (source_profile.get("is_primary_authority") if has_source_url else False)
    )
    status_reason = (check.status_reason or "").strip() or _infer_citation_status_reason(
        check.status,
        source_tier=source_tier,
        is_primary_authority=is_primary_authority,
        note=check.note,
    )
    trust_explanation = (check.trust_explanation or "").strip() or _citation_trust_explanation(
        status_reason
    )
    confidence = (
        check.confidence
        if (check.status_reason or "").strip()
        else _infer_citation_confidence(
            check.status,
            status_reason=status_reason,
            source_tier=source_tier,
            is_primary_authority=is_primary_authority,
        )
    )
    return check.model_copy(
        update={
            "confidence": confidence,
            "status_reason": status_reason,
            "trust_explanation": trust_explanation,
            "source_tier": source_tier,
            "source_class": source_class,
            "is_primary_authority": is_primary_authority,
        }
    )


def _infer_citation_status_reason(
    status: str,
    *,
    source_tier: str | None,
    is_primary_authority: bool,
    note: str,
) -> str:
    normalized_note = note.lower()
    if "budget exhausted" in normalized_note:
        return "budget_exhausted"
    if "search error" in normalized_note:
        return "search_error"
    if "no relevant citation match" in normalized_note:
        return "no_relevant_match"
    if "no results found" in normalized_note:
        return "no_results"
    if "name match only" in normalized_note or "case-name match only" in normalized_note:
        return "name_match_only"
    if "non-authoritative" in normalized_note:
        return "non_authoritative_match"

    if status == "not_found":
        return "no_results"
    if status == "verified":
        if source_tier == "official" and is_primary_authority:
            return "official_citation_match"
        if source_tier == "official":
            return "official_non_primary_match"
        if source_tier == "professional":
            return "secondary_authority_match"
    if status == "uncertain":
        if source_tier == "official" and not is_primary_authority:
            return "official_non_primary_match"
        if source_tier in {"official", "professional"}:
            return "secondary_authority_match"
        return "non_authoritative_match"
    return ""


def _infer_citation_confidence(
    status: str,
    *,
    status_reason: str,
    source_tier: str | None,
    is_primary_authority: bool,
) -> str:
    if status == "verified" and source_tier == "official" and is_primary_authority:
        return "high"
    if status_reason in {"secondary_authority_match", "official_non_primary_match"}:
        return "medium"
    return "low"


def _citation_trust_explanation(status_reason: str) -> str:
    explanations = {
        "official_citation_match": "Citation text matched on a primary legal authority source.",
        "official_non_primary_match": "Citation text matched, but the best hit is not a primary court-opinion authority.",
        "secondary_authority_match": "Citation text matched, but the best hit is not a primary court-opinion authority.",
        "multiple_conflicting_hits": "Multiple citation-aligned hits were found with conflicting authority strength, so manual review is still required.",
        "name_match_only": "The case name matched a reviewable source, but the citation text was not confirmed in the reviewed hit.",
        "non_authoritative_match": "Only commentary, news, or otherwise non-authoritative sources aligned with this citation search.",
        "no_results": "No citation-check search results were returned for this authority.",
        "no_relevant_match": "The reviewed hits did not contain a matching citation or sufficient case-name overlap.",
        "retrieval_failed": "Live citation retrieval failed, so this result requires manual verification.",
        "budget_exhausted": "Citation verification stopped because the live retrieval budget was exhausted.",
        "search_error": "Citation verification hit a live-search error and should be reviewed manually.",
    }
    return explanations.get(status_reason, "")


def _normalize_citation_value(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.lower()
    normalized = normalized.replace(",", " ")
    normalized = normalized.replace(".", ". ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = re.sub(r"\s+\.\s+", ". ", normalized)
    return normalized or None


def _normalize_authority_name(value: str | None) -> str:
    if not value:
        return ""
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", normalized).strip()


def _cluster_key_for_item(item: EvidenceItem) -> tuple[str, str]:
    if item.authority_key:
        if item.authority_key.startswith("citation:"):
            return ("citation", item.authority_key.removeprefix("citation:"))
        return ("derived", item.authority_key)
    if item.citation:
        return ("citation", item.citation.lower())
    if item.url:
        return ("url", _normalize_cluster_url(item.url))
    fallback = "|".join([item.module, item.evidence_type, item.title.lower()])
    return ("derived", fallback)


def _normalize_cluster_url(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
    except Exception:
        return url.strip().rstrip("/").lower()

    hostname = (parsed.hostname or "").lower().removeprefix("www.")
    path = re.sub(r"/+", "/", (parsed.path or "").rstrip("/"))
    normalized = f"{hostname}{path}".strip("/")
    return normalized.lower()


def _cluster_ids_for_evidence_ids(
    evidence_ids: list[str],
    evidence_cluster_ids_by_evidence_id: Mapping[str, str],
) -> list[str]:
    cluster_ids: list[str] = []
    for evidence_id in evidence_ids:
        cluster_id = evidence_cluster_ids_by_evidence_id.get(evidence_id)
        if cluster_id and cluster_id not in cluster_ids:
            cluster_ids.append(cluster_id)
    return cluster_ids


def _claim_status(evidence_ids: list[str], has_review_event: bool) -> str:
    if not evidence_ids or has_review_event:
        return "review_required"
    return "supported"


def _carrier_claim_text(carrier_payload: dict[str, Any]) -> str:
    rebuttals = carrier_payload.get("rebuttal_angles", [])
    if rebuttals:
        return rebuttals[0]

    defenses = carrier_payload.get("common_defenses", [])
    if defenses:
        return defenses[0]

    snapshot = carrier_payload.get("carrier_snapshot", {})
    carrier_name = snapshot.get("name", "Carrier")
    return f"{carrier_name} document pack assembled for review."


def _caselaw_claim_text(caselaw_payload: dict[str, Any]) -> str:
    issues = caselaw_payload.get("issues", [])
    if not issues:
        return "Case-law review requires manual follow-up."

    first_issue = issues[0]
    if first_issue.get("notes"):
        return first_issue["notes"][0]

    first_case = first_issue.get("cases", [])
    if first_case and first_case[0].get("one_liner"):
        return first_case[0]["one_liner"]

    return f"Case-law authorities identified across {len(issues)} issue buckets."


def _stable_token(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "item"


def _run_id_from_intake(intake: CaseIntake) -> str:
    parts = (
        intake.event_name,
        intake.state,
        intake.county,
        intake.carrier,
    )
    slug = "-".join(_stable_token(part) for part in parts if part.strip())
    return f"run-notebook-{slug}"


def _model_to_payload(model: BaseModel) -> dict[str, Any]:
    """Dump model while preserving legacy omission of `warnings` when empty."""
    data = model.model_dump()
    if data.get("warnings") is None:
        data.pop("warnings", None)
    if not data.get("retrieval_tasks"):
        data.pop("retrieval_tasks", None)
    if not data.get("run_events"):
        data.pop("run_events", None)
    return data


def weather_brief_to_payload(payload: Mapping[str, Any] | WeatherBrief) -> dict[str, Any]:
    """Return a weather payload normalized against the typed contract."""
    return _model_to_payload(adapt_weather_brief(payload))


def case_intake_to_payload(payload: Mapping[str, Any] | CaseIntake) -> dict[str, Any]:
    """Return an intake payload normalized against the typed contract."""
    return _model_to_payload(adapt_case_intake(payload))


def query_spec_to_payload(payload: Mapping[str, Any] | QuerySpec) -> dict[str, Any]:
    """Return a query-spec payload normalized against the typed contract."""
    return _model_to_payload(adapt_query_spec(payload))


def query_plan_to_payloads(
    payload: Sequence[Mapping[str, Any] | QuerySpec],
) -> list[dict[str, Any]]:
    """Return a query plan normalized against the typed contract."""
    return [query_spec_to_payload(item) for item in adapt_query_plan(payload)]


def research_plan_to_payload(
    payload: Mapping[str, Any] | ResearchPlan,
) -> dict[str, Any]:
    """Return a research plan normalized against the typed contract."""
    return _model_to_payload(adapt_research_plan(payload))


def legal_issue_to_payload(payload: Mapping[str, Any] | LegalIssue) -> dict[str, Any]:
    """Return a legal issue normalized against the typed contract."""
    return _model_to_payload(adapt_legal_issue(payload))


def case_candidate_to_payload(
    payload: Mapping[str, Any] | CaseCandidate,
) -> dict[str, Any]:
    """Return a case candidate normalized against the typed contract."""
    return _model_to_payload(adapt_case_candidate(payload))


def run_to_payload(payload: Mapping[str, Any] | Run) -> dict[str, Any]:
    """Return a run normalized against the typed contract."""
    return _model_to_payload(adapt_run(payload))


def run_event_to_payload(payload: Mapping[str, Any] | RunEvent) -> dict[str, Any]:
    """Return a run event normalized against the typed contract."""
    return _model_to_payload(adapt_run_event(payload))


def retrieval_task_to_payload(
    payload: Mapping[str, Any] | RetrievalTask,
) -> dict[str, Any]:
    """Return a retrieval task normalized against the typed contract."""
    return _model_to_payload(adapt_retrieval_task(payload))


def run_stage_to_payload(payload: Mapping[str, Any] | RunStage) -> dict[str, Any]:
    """Return a run stage normalized against the typed contract."""
    return _model_to_payload(adapt_run_stage(payload))


def memo_section_to_payload(
    payload: Mapping[str, Any] | MemoSection,
) -> dict[str, Any]:
    """Return a memo section normalized against the typed contract."""
    return _model_to_payload(adapt_memo_section(payload))


def run_audit_snapshot_to_payload(
    payload: Mapping[str, Any] | RunAuditSnapshot,
) -> dict[str, Any]:
    """Return a run audit snapshot normalized against the typed contract."""
    return _model_to_payload(adapt_run_audit_snapshot(payload))


def evidence_board_to_payload(
    payload: Mapping[str, Any] | EvidenceBoardReadModel,
) -> dict[str, Any]:
    """Return an evidence-board read model normalized against the typed contract."""
    return _model_to_payload(adapt_evidence_board(payload))


def issue_workspace_to_payload(
    payload: Mapping[str, Any] | IssueWorkspaceReadModel,
) -> dict[str, Any]:
    """Return an issue-workspace read model normalized against the typed contract."""
    return _model_to_payload(adapt_issue_workspace(payload))


def memo_composer_to_payload(
    payload: Mapping[str, Any] | MemoComposerReadModel,
) -> dict[str, Any]:
    """Return a memo-composer read model normalized against the typed contract."""
    return _model_to_payload(adapt_memo_composer(payload))


def carrier_doc_pack_to_payload(
    payload: Mapping[str, Any] | CarrierDocPack,
) -> dict[str, Any]:
    """Return a carrier payload normalized against the typed contract."""
    return _model_to_payload(adapt_carrier_doc_pack(payload))


def caselaw_pack_to_payload(payload: Mapping[str, Any] | CaseLawPack) -> dict[str, Any]:
    """Return a caselaw payload normalized against the typed contract."""
    return _model_to_payload(adapt_caselaw_pack(payload))


def citation_verify_pack_to_payload(
    payload: Mapping[str, Any] | CitationVerifyPack,
) -> dict[str, Any]:
    """Return a citation-verify payload normalized against the typed contract."""
    return _model_to_payload(adapt_citation_verify_pack(payload))
