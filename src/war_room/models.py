"""Typed domain models for core pipeline contracts."""

from __future__ import annotations

import datetime as dt
import re
from typing import Any, Literal, Mapping

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


class MemoRenderInput(BaseModel):
    """Typed contract for markdown memo rendering input."""

    model_config = ConfigDict(extra="forbid")

    intake: CaseIntake
    weather: WeatherBrief
    carrier: CarrierDocPack
    caselaw: CaseLawPack
    citecheck: CitationVerifyPack
    query_plan: list[QuerySpec] = Field(default_factory=list)


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
    typed_queries = [adapt_query_spec(item) for item in query_plan]
    return MemoRenderInput(
        intake=adapt_case_intake(intake),
        weather=adapt_weather_brief(weather),
        carrier=adapt_carrier_doc_pack(carrier),
        caselaw=adapt_caselaw_pack(caselaw),
        citecheck=adapt_citation_verify_pack(citecheck),
        query_plan=typed_queries,
    )


def _model_to_payload(model: BaseModel) -> dict[str, Any]:
    """Dump model while preserving legacy omission of `warnings` when empty."""
    data = model.model_dump()
    if data.get("warnings") is None:
        data.pop("warnings", None)
    return data


def weather_brief_to_payload(payload: Mapping[str, Any] | WeatherBrief) -> dict[str, Any]:
    """Return a weather payload normalized against the typed contract."""
    return _model_to_payload(adapt_weather_brief(payload))


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
