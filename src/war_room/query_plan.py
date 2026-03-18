"""Case intake and query plan generation.

Generates 12-18 targeted research queries from a CaseIntake,
organized by module: weather, carrier_docs, caselaw.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Mapping

from war_room.models import CaseIntake, QuerySpec, adapt_query_plan

CASE_INTAKE_REQUIRED_FIELDS = (
    "event_name",
    "event_date",
    "state",
    "county",
    "carrier",
    "policy_type",
)
CASE_INTAKE_OPTIONAL_FIELDS = (
    "posture",
    "key_facts",
    "coverage_issues",
)
CASE_INTAKE_ALLOWED_FIELDS = CASE_INTAKE_REQUIRED_FIELDS + CASE_INTAKE_OPTIONAL_FIELDS
POSTURE_VALUE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class IntakeValidationError(ValueError):
    """Raised when an intake payload fails strict schema validation."""


def _require_non_empty_string(value: Any, field_name: str) -> str:
    """Validate and normalize required string fields."""
    if not isinstance(value, str):
        raise IntakeValidationError(f"Field '{field_name}' must be a non-empty string.")
    normalized = value.strip()
    if not normalized:
        raise IntakeValidationError(f"Field '{field_name}' must be a non-empty string.")
    return normalized


def _validate_event_date(value: Any) -> str:
    """Validate date shape to keep intake payloads deterministic."""
    event_date = _require_non_empty_string(value, "event_date")
    try:
        dt.date.fromisoformat(event_date)
    except ValueError as exc:
        raise IntakeValidationError(
            "Field 'event_date' must be a valid date in YYYY-MM-DD format."
        ) from exc
    return event_date


def _validate_string_list(
    value: Any,
    field_name: str,
    *,
    allow_empty: bool,
    enforce_posture_tokens: bool = False,
) -> list[str]:
    """Validate list[str] fields with strict, actionable errors."""
    if not isinstance(value, list):
        raise IntakeValidationError(
            f"Field '{field_name}' must be a list of non-empty strings."
        )

    normalized: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise IntakeValidationError(
                f"Field '{field_name}[{index}]' must be a non-empty string."
            )

        cleaned = item.strip()
        if not cleaned:
            raise IntakeValidationError(
                f"Field '{field_name}[{index}]' must be a non-empty string."
            )

        if enforce_posture_tokens and not POSTURE_VALUE_PATTERN.fullmatch(cleaned):
            raise IntakeValidationError(
                f"Field '{field_name}[{index}]' must use snake_case tokens "
                f"like 'bad_faith', got '{item}'."
            )

        normalized.append(cleaned)

    if not allow_empty and not normalized:
        raise IntakeValidationError(f"Field '{field_name}' must contain at least one value.")

    return normalized


def validate_case_intake_payload(payload: Mapping[str, Any]) -> CaseIntake:
    """Validate and normalize a JSON-like intake payload into CaseIntake."""
    if not isinstance(payload, Mapping):
        raise IntakeValidationError(
            "Intake payload must be a JSON object with named fields."
        )

    missing_fields = [field for field in CASE_INTAKE_REQUIRED_FIELDS if field not in payload]
    if missing_fields:
        required = ", ".join(CASE_INTAKE_REQUIRED_FIELDS)
        missing = ", ".join(missing_fields)
        raise IntakeValidationError(
            f"Missing required field(s): {missing}. Required fields: {required}."
        )

    unknown_fields = [
        str(field)
        for field in payload.keys()
        if field not in CASE_INTAKE_ALLOWED_FIELDS
    ]
    if unknown_fields:
        allowed = ", ".join(CASE_INTAKE_ALLOWED_FIELDS)
        unknown = ", ".join(sorted(unknown_fields))
        raise IntakeValidationError(
            f"Unexpected field(s): {unknown}. Allowed fields: {allowed}."
        )

    posture: list[str]
    if "posture" in payload:
        posture = _validate_string_list(
            payload["posture"],
            "posture",
            allow_empty=False,
            enforce_posture_tokens=True,
        )
    else:
        posture = ["denial"]

    key_facts = _validate_string_list(
        payload.get("key_facts", []),
        "key_facts",
        allow_empty=True,
    )
    coverage_issues = _validate_string_list(
        payload.get("coverage_issues", []),
        "coverage_issues",
        allow_empty=True,
    )

    return CaseIntake(
        event_name=_require_non_empty_string(payload["event_name"], "event_name"),
        event_date=_validate_event_date(payload["event_date"]),
        state=_require_non_empty_string(payload["state"], "state"),
        county=_require_non_empty_string(payload["county"], "county"),
        carrier=_require_non_empty_string(payload["carrier"], "carrier"),
        policy_type=_require_non_empty_string(payload["policy_type"], "policy_type"),
        posture=posture,
        key_facts=key_facts,
        coverage_issues=coverage_issues,
    )


def load_case_intake(path: str | Path) -> CaseIntake:
    """Load and strictly validate a case intake JSON file."""
    intake_path = Path(path)
    try:
        raw_payload = json.loads(intake_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise IntakeValidationError(f"Intake file not found: {intake_path}") from exc
    except json.JSONDecodeError as exc:
        raise IntakeValidationError(
            f"Invalid JSON in intake file '{intake_path}' "
            f"(line {exc.lineno}, column {exc.colno})."
        ) from exc
    except OSError as exc:
        raise IntakeValidationError(f"Could not read intake file '{intake_path}': {exc}") from exc

    return validate_case_intake_payload(raw_payload)


def generate_query_plan(intake: CaseIntake) -> list[QuerySpec]:
    """Generate 12-18 targeted research queries from a case intake.

    Queries are organized by module: weather, carrier_docs, caselaw.
    """
    queries: list[QuerySpec] = []

    queries.append(QuerySpec(
        module="weather",
        query=f"{intake.event_name} {intake.county} County {intake.state} damage report",
        category="damage_report",
        date_start=intake.event_date,
        preferred_domains=["noaa.gov", "weather.gov"],
    ))
    queries.append(QuerySpec(
        module="weather",
        query=f"NWS {intake.event_name} wind speed {intake.county} {intake.state}",
        category="wind_data",
        date_start=intake.event_date,
        preferred_domains=["weather.gov", "nhc.noaa.gov"],
    ))
    queries.append(QuerySpec(
        module="weather",
        query=f"{intake.event_name} storm surge flood {intake.county} County {intake.state}",
        category="flood_surge",
        date_start=intake.event_date,
        preferred_domains=["noaa.gov", "usgs.gov"],
    ))
    queries.append(QuerySpec(
        module="weather",
        query=f"FEMA disaster declaration {intake.event_name} {intake.state}",
        category="fema_declaration",
        date_start=intake.event_date,
        preferred_domains=["fema.gov", "disasterassistance.gov"],
    ))
    queries.append(QuerySpec(
        module="weather",
        query=f"{intake.event_name} damage assessment {intake.county} County insured losses",
        category="loss_estimate",
        date_start=intake.event_date,
        preferred_domains=["fema.gov", "noaa.gov", "weather.gov"],
    ))

    queries.append(QuerySpec(
        module="carrier_docs",
        query=f"{intake.carrier} {intake.event_name} claim denial {intake.state}",
        category="denial_patterns",
        date_start=intake.event_date,
    ))
    queries.append(QuerySpec(
        module="carrier_docs",
        query=f"{intake.carrier} department of insurance complaints {intake.state}",
        category="doi_complaints",
        preferred_domains=["floir.com", "tdi.texas.gov", "naic.org"],
    ))
    queries.append(QuerySpec(
        module="carrier_docs",
        query=f"{intake.carrier} {intake.event_name} regulatory action {intake.state}",
        category="regulatory_action",
        date_start=intake.event_date,
        preferred_domains=["floir.com", "naic.org", "insurance.ca.gov"],
    ))
    queries.append(QuerySpec(
        module="carrier_docs",
        query=f"{intake.carrier} claims handling guidelines {intake.policy_type}",
        category="claims_manual",
        preferred_domains=["floir.com", "citizensfla.com", "naic.org"],
    ))
    queries.append(QuerySpec(
        module="carrier_docs",
        query=f"{intake.carrier} bad faith insurance {intake.state} settlement practices",
        category="bad_faith_history",
        preferred_domains=["floir.com", "naic.org", "insurancejournal.com"],
    ))

    posture_terms = " ".join(intake.posture)
    queries.append(QuerySpec(
        module="caselaw",
        query=f"{intake.carrier} {intake.policy_type} {posture_terms} {intake.state}",
        category="carrier_precedent",
        preferred_domains=["scholar.google.com", "law.cornell.edu", "casetext.com", "courtlistener.com"],
    ))
    queries.append(QuerySpec(
        module="caselaw",
        query=(
            f"{intake.event_name} wind damage insurance coverage {intake.policy_type} "
            f"{intake.state}"
        ),
        category="coverage_law",
        preferred_domains=["scholar.google.com", "casetext.com", "courtlistener.com"],
    ))
    queries.append(QuerySpec(
        module="caselaw",
        query=(
            f"concurrent causation wind water damage insurance {intake.state} "
            f"{intake.event_name}"
        ),
        category="concurrent_causation",
        preferred_domains=["scholar.google.com", "law.cornell.edu", "courtlistener.com"],
    ))
    queries.append(QuerySpec(
        module="caselaw",
        query=(
            f"insurance bad faith {intake.state} {intake.carrier} failure to investigate "
            f"penalty damages"
        ),
        category="bad_faith_precedent",
        preferred_domains=["scholar.google.com", "casetext.com", "courtlistener.com"],
    ))

    seen_issue_queries: set[str] = set()
    for issue in intake.coverage_issues:
        normalized_issue = " ".join(issue.lower().split())
        if normalized_issue in seen_issue_queries:
            continue
        seen_issue_queries.add(normalized_issue)
        queries.append(QuerySpec(
            module="caselaw",
            query=(
                f'"{issue}" insurance coverage {intake.state} {intake.policy_type} '
                f'{intake.event_name}'
            ),
            category="coverage_issue",
            preferred_domains=["scholar.google.com", "law.cornell.edu", "casetext.com", "courtlistener.com"],
        ))

    if "bad_faith" in intake.posture:
        queries.append(QuerySpec(
            module="caselaw",
            query=(
                f"bad faith failure to investigate insurance claim {intake.state} "
                f"{intake.carrier} {intake.event_name}"
            ),
            category="bad_faith_law",
            preferred_domains=["scholar.google.com", "casetext.com", "courtlistener.com"],
        ))
    if "underpayment" in intake.posture:
        queries.append(QuerySpec(
            module="caselaw",
            query=f"insurance underpayment {intake.event_name} appraisal {intake.state}",
            category="underpayment_law",
            preferred_domains=["scholar.google.com", "casetext.com", "courtlistener.com"],
        ))

    return queries


def format_query_plan(queries: list[Mapping[str, Any] | QuerySpec]) -> str:
    """Format the query plan grouped by module for display."""
    typed_queries = adapt_query_plan(queries)

    lines = [
        "=" * 60,
        f"QUERY PLAN - {len(typed_queries)} queries",
        "=" * 60,
    ]

    modules = ["weather", "carrier_docs", "caselaw"]
    module_labels = {
        "weather": "WEATHER DATA",
        "carrier_docs": "CARRIER DOCUMENTS",
        "caselaw": "CASE LAW",
    }

    for mod in modules:
        mod_queries = [q for q in typed_queries if q.module == mod]
        if mod_queries:
            lines.append(f"\n  [{module_labels.get(mod, mod)}] ({len(mod_queries)} queries)")
            lines.append("  " + "-" * 40)
            for q in mod_queries:
                lines.append(q.format_row())

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)
