"""Typed domain models for core pipeline contracts."""

from __future__ import annotations

import datetime as dt
import re
from typing import Any, Literal, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

POSTURE_VALUE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


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


class SourceReference(BaseModel):
    """Canonical source reference for module outputs."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = ""
    url: str = Field(min_length=1)
    badge: str = Field(min_length=1)
    reason: str | None = None


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


class CitationCheck(BaseModel):
    """Single citation spot-check outcome."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: Literal["verified", "uncertain", "not_found"]
    badge: str = Field(min_length=1)
    source_url: str | None = None
    note: str = Field(min_length=1)
    case_name: str = ""
    citation: str = ""


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
    review_required: bool = False


class MemoClaim(BaseModel):
    """Evidence-linked memo assertion for audit purposes."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    claim_id: str = Field(min_length=1)
    section: str = Field(min_length=1)
    text: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    status: Literal["supported", "review_required"] = "supported"


class ReviewEvent(BaseModel):
    """Review-required event emitted during memo assembly."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_id: str = Field(min_length=1)
    event_type: Literal["warning", "citation_uncertain", "citation_not_found"]
    label: str = Field(min_length=1)
    detail: str = Field(min_length=1)
    module: str | None = None
    related_evidence_ids: list[str] = Field(default_factory=list)


class ExportArtifact(BaseModel):
    """Export metadata for the generated memo artifact."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    artifact_type: Literal["markdown_memo"] = "markdown_memo"
    title: str = Field(min_length=1)
    disclaimer: str = Field(min_length=1)
    section_titles: list[str] = Field(default_factory=list)


class MemoRenderInput(BaseModel):
    """Typed contract for markdown memo rendering input."""

    model_config = ConfigDict(extra="forbid")

    intake: CaseIntake
    weather: WeatherBrief
    carrier: CarrierDocPack
    caselaw: CaseLawPack
    citecheck: CitationVerifyPack
    query_plan: list[QuerySpec] = Field(default_factory=list)


class RunAuditSnapshot(BaseModel):
    """Canonical audit snapshot for a rendered research memo."""

    model_config = ConfigDict(extra="forbid")

    intake: CaseIntake
    query_plan: list[QuerySpec] = Field(default_factory=list)
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
    evidence_clusters: list[EvidenceCluster] = Field(default_factory=list)
    memo_claims: list[MemoClaim] = Field(default_factory=list)
    review_events: list[ReviewEvent] = Field(default_factory=list)
    export_artifact: ExportArtifact


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


def adapt_citation_verify_pack(
    payload: Mapping[str, Any] | CitationVerifyPack,
) -> CitationVerifyPack:
    """Validate/coerce citation-verify payload into typed model."""
    if isinstance(payload, CitationVerifyPack):
        return payload
    return CitationVerifyPack.model_validate(payload)


def memo_render_input_from_parts(
    intake: Mapping[str, Any] | CaseIntake,
    weather: Mapping[str, Any] | WeatherBrief,
    carrier: Mapping[str, Any] | CarrierDocPack,
    caselaw: Mapping[str, Any] | CaseLawPack,
    citecheck: Mapping[str, Any] | CitationVerifyPack,
    query_plan: list[Mapping[str, Any] | QuerySpec],
) -> MemoRenderInput:
    """Build typed memo-render input from mixed dict/model payloads."""
    return MemoRenderInput(
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


def run_audit_snapshot_from_memo_input(memo_input: MemoRenderInput) -> RunAuditSnapshot:
    """Build a canonical audit snapshot from normalized memo-render input."""
    weather_payload = weather_brief_to_payload(memo_input.weather)
    carrier_payload = carrier_doc_pack_to_payload(memo_input.carrier)
    caselaw_payload = caselaw_pack_to_payload(memo_input.caselaw)
    citecheck_payload = citation_verify_pack_to_payload(memo_input.citecheck)

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
                    issue=issue.get("issue"),
                    citation=case.get("citation") or None,
                )
            )
            evidence_ids_by_module["caselaw"].append(evidence_id)

    for index, check in enumerate(citecheck_payload.get("checks", []), 1):
        evidence_id = f"citation-check-{index}"
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
                citation=check.get("citation") or None,
                review_required=check.get("status") != "verified",
            )
        )
        evidence_ids_by_module["citation_verify"].append(evidence_id)

    evidence_clusters = _build_evidence_clusters(evidence_items)

    review_events: list[ReviewEvent] = []
    for module_key, module_label, payload in (
        ("weather", "Weather", weather_payload),
        ("carrier", "Carrier", carrier_payload),
        ("caselaw", "Case law", caselaw_payload),
    ):
        for index, warning in enumerate(payload.get("warnings", []) or [], 1):
            review_events.append(
                ReviewEvent(
                    event_id=f"{module_key}-warning-{index}",
                    event_type="warning",
                    label=f"{module_label} review required",
                    detail=warning,
                    module=module_key,
                    related_evidence_ids=evidence_ids_by_module[module_key],
                )
            )

    citation_summary = citecheck_payload.get("summary", {})
    uncertain = citation_summary.get("uncertain", 0)
    not_found = citation_summary.get("not_found", 0)
    if uncertain:
        review_events.append(
            ReviewEvent(
                event_id="citation-uncertain",
                event_type="citation_uncertain",
                label="Citation review required",
                detail=f"{uncertain} citation checks are uncertain.",
                module="citation_verify",
                related_evidence_ids=evidence_ids_by_module["citation_verify"],
            )
        )
    if not_found:
        review_events.append(
            ReviewEvent(
                event_id="citation-not-found",
                event_type="citation_not_found",
                label="Citation not found",
                detail=f"{not_found} citation checks were not found on reviewed sources.",
                module="citation_verify",
                related_evidence_ids=evidence_ids_by_module["citation_verify"],
            )
        )

    review_modules = {event.module for event in review_events if event.module}
    memo_claims = [
        MemoClaim(
            claim_id="weather-corroboration",
            section="Weather Corroboration",
            text=weather_payload.get("event_summary", "Weather evidence assembled."),
            evidence_ids=evidence_ids_by_module["weather"],
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
        "Appendix: Evidence Clusters",
        "Appendix: Evidence Index",
        "Appendix: All Sources",
        "Methodology & Limitations",
    ]
    if review_events:
        section_titles.insert(8, "Appendix: Review Log")

    return RunAuditSnapshot(
        intake=memo_input.intake,
        query_plan=memo_input.query_plan,
        evidence_items=evidence_items,
        evidence_clusters=evidence_clusters,
        memo_claims=memo_claims,
        review_events=review_events,
        export_artifact=ExportArtifact(
            title="CAT-Loss War Room - Research Memo",
            disclaimer="DEMO RESEARCH MEMO - VERIFY CITATIONS - NOT LEGAL ADVICE",
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
) -> RunAuditSnapshot:
    """Build a canonical audit snapshot from mixed dict/model payloads."""
    return run_audit_snapshot_from_memo_input(
        memo_render_input_from_parts(intake, weather, carrier, caselaw, citecheck, query_plan)
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
        clusters.append(
            EvidenceCluster(
                cluster_id=f"cluster-{index}",
                cluster_type=cluster_key[0],
                label=label,
                evidence_ids=[item.evidence_id for item in items],
                modules=modules,
                citation=first.citation,
                url=first.url,
                review_required=any(item.review_required for item in items),
            )
        )

    return clusters


def _cluster_key_for_item(item: EvidenceItem) -> tuple[str, str]:
    if item.citation:
        return ("citation", item.citation.lower())
    if item.url:
        return ("url", _normalize_cluster_url(item.url))
    fallback = "|".join([item.module, item.evidence_type, item.title.lower()])
    return ("derived", fallback)


def _normalize_cluster_url(url: str) -> str:
    return url.strip().rstrip("/").lower()


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


def _model_to_payload(model: BaseModel) -> dict[str, Any]:
    """Dump model while preserving legacy omission of `warnings` when empty."""
    data = model.model_dump()
    if data.get("warnings") is None:
        data.pop("warnings", None)
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


def run_audit_snapshot_to_payload(
    payload: Mapping[str, Any] | RunAuditSnapshot,
) -> dict[str, Any]:
    """Return a run audit snapshot normalized against the typed contract."""
    return _model_to_payload(adapt_run_audit_snapshot(payload))


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
