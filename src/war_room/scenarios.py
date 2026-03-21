"""Shared scenario registry for curated benchmark matters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from war_room.bootstrap import discover_repo_root
from war_room.models import CaseIntake
from war_room.query_plan import CASE_INTAKE_ALLOWED_FIELDS, IntakeValidationError, validate_case_intake_payload

SCENARIO_REGISTRY_SCHEMA = "scenario-registry.v1"
SCENARIO_SCHEMA = "scenario.v1"
SCENARIO_INDEX_FILENAME = "index.json"
DEFAULT_SCENARIOS_DIRNAME = "scenarios"


class ScenarioValidationError(ValueError):
    """Raised when a scenario file or registry entry is invalid."""


@dataclass(frozen=True)
class ScenarioAvailabilitySummary:
    """Human-readable availability summary for notebook and preflight surfaces."""

    surface: Literal["notebook", "preflight"]
    scenario_id: str
    title: str
    case_key: str
    status: Literal["offline-ready", "live-only"]
    detail: str


class ScenarioRegistryIndex(BaseModel):
    """Registry ordering and default scenario metadata."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: str = Field(min_length=1)
    default_scenario_id: str = Field(min_length=1)
    scenario_order: list[str] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        if value != SCENARIO_REGISTRY_SCHEMA:
            raise ValueError(
                f"scenario registry schema_version must be '{SCENARIO_REGISTRY_SCHEMA}'."
            )
        return value

    @field_validator("scenario_order")
    @classmethod
    def _validate_scenario_order(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for slug in value:
            normalized = slug.strip()
            if not normalized:
                raise ValueError("scenario_order values must be non-empty strings.")
            if normalized in seen:
                raise ValueError(f"scenario_order contains duplicate slug '{normalized}'.")
            seen.add(normalized)
            cleaned.append(normalized)
        return cleaned


class ScenarioDefinition(BaseModel):
    """Curated benchmark scenario backed by the canonical CaseIntake contract."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    title: str = Field(min_length=1)
    benchmark_focus: str = Field(min_length=1)
    fixture_case_key: str | None = None
    offline_demo_ready: bool = False
    event_name: str = Field(min_length=1)
    event_date: str = Field(min_length=1)
    state: str = Field(min_length=1)
    county: str = Field(min_length=1)
    carrier: str = Field(min_length=1)
    policy_type: str = Field(min_length=1)
    posture: list[str] = Field(default_factory=lambda: ["denial"])
    key_facts: list[str] = Field(default_factory=list)
    coverage_issues: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        if value != SCENARIO_SCHEMA:
            raise ValueError(f"scenario schema_version must be '{SCENARIO_SCHEMA}'.")
        return value

    @field_validator("tags", "notes")
    @classmethod
    def _validate_string_lists(cls, value: list[str], info: Any) -> list[str]:
        cleaned: list[str] = []
        for token in value:
            normalized = token.strip()
            if not normalized:
                raise ValueError(f"{info.field_name} values must be non-empty strings.")
            cleaned.append(normalized)
        return cleaned

    @property
    def case_key(self) -> str:
        """Return the cache/output key that best matches this scenario."""

        return self.fixture_case_key or self.slug

    def intake_payload(self) -> dict[str, Any]:
        """Return the scenario as a canonical CaseIntake payload."""

        return {
            field: getattr(self, field)
            for field in CASE_INTAKE_ALLOWED_FIELDS
            if hasattr(self, field)
        }

    def to_case_intake(self, overrides: Mapping[str, Any] | None = None) -> CaseIntake:
        """Return a validated CaseIntake, optionally applying local notebook overrides."""

        payload = self.intake_payload()
        if overrides:
            payload.update(dict(overrides))
        return validate_case_intake_payload(payload)


def scenario_availability_summary(
    scenario: ScenarioDefinition,
    *,
    live_retrieval_enabled: bool,
) -> ScenarioAvailabilitySummary:
    """Summarize whether a registry scenario is cache-only ready or live-only."""

    if scenario.offline_demo_ready:
        detail = "Registry marks this scenario as offline-demo-ready for cache-only use."
        status: Literal["offline-ready", "live-only"] = "offline-ready"
    elif live_retrieval_enabled:
        detail = (
            "Registry marks this scenario as live-only; live retrieval is enabled for "
            "the current runtime."
        )
        status = "live-only"
    else:
        detail = (
            "Registry marks this scenario as live-only; enable live retrieval or add "
            "committed fixtures for cache-only runs."
        )
        status = "live-only"

    return ScenarioAvailabilitySummary(
        surface="notebook",
        scenario_id=scenario.slug,
        title=scenario.title,
        case_key=scenario.case_key,
        status=status,
        detail=detail,
    )


def scenario_catalog_availability(
    repo_root: str | Path | None = None,
    *,
    live_retrieval_enabled: bool,
) -> list[ScenarioAvailabilitySummary]:
    """Return availability summaries for every curated notebook scenario."""

    return [
        scenario_availability_summary(scenario, live_retrieval_enabled=live_retrieval_enabled)
        for scenario in list_scenarios(repo_root=repo_root)
    ]


def fixture_case_availability_summary(
    *,
    case_key: str,
    title: str,
    registry_slug: str | None = None,
    registry_offline_ready: bool | None = None,
) -> ScenarioAvailabilitySummary:
    """Summarize an offline preflight fixture lane."""

    if registry_slug is None:
        detail = "No registry scenario maps to this committed fixture lane, but preflight stays offline-safe."
        scenario_id = case_key
    elif registry_offline_ready:
        detail = (
            f"Registry scenario '{registry_slug}' is offline-ready, and the committed fixture lane is available."
        )
        scenario_id = registry_slug
    else:
        detail = (
            f"Registry scenario '{registry_slug}' is live-only, but the committed fixture lane keeps preflight offline-ready."
        )
        scenario_id = registry_slug

    return ScenarioAvailabilitySummary(
        surface="preflight",
        scenario_id=scenario_id,
        title=title,
        case_key=case_key,
        status="offline-ready",
        detail=detail,
    )


def scenarios_dir(repo_root: str | Path | None = None) -> Path:
    """Return the canonical scenarios directory path."""

    root = Path(repo_root) if repo_root is not None else discover_repo_root()
    return root / DEFAULT_SCENARIOS_DIRNAME


def default_scenario_id(repo_root: str | Path | None = None) -> str:
    """Return the configured default scenario slug."""

    return _load_registry_index_cached(scenarios_dir(repo_root)).default_scenario_id


def list_scenarios(repo_root: str | Path | None = None) -> list[ScenarioDefinition]:
    """Return curated scenarios in registry order."""

    directory = scenarios_dir(repo_root)
    index = _load_registry_index_cached(directory)
    return [load_scenario(slug, repo_root=directory.parent) for slug in index.scenario_order]


def load_scenario(slug: str, repo_root: str | Path | None = None) -> ScenarioDefinition:
    """Load one scenario by slug from the canonical registry."""

    directory = scenarios_dir(repo_root)
    scenario_path = directory / f"{slug}.json"
    if not scenario_path.exists():
        raise ScenarioValidationError(f"Scenario '{slug}' not found: {scenario_path}")

    payload = _load_json_file(scenario_path)
    scenario = validate_scenario(payload, path=scenario_path)
    if scenario.slug != slug:
        raise ScenarioValidationError(
            f"Scenario file '{scenario_path.name}' declares slug '{scenario.slug}', expected '{slug}'."
        )
    return scenario


def load_scenario_for_fixture_case(
    case_key: str,
    repo_root: str | Path | None = None,
) -> ScenarioDefinition | None:
    """Return the scenario whose fixture key matches a committed cache-samples case key."""

    for scenario in list_scenarios(repo_root=repo_root):
        if scenario.fixture_case_key == case_key:
            return scenario
    return None


def validate_scenario(
    data: Mapping[str, Any],
    *,
    path: str | Path | None = None,
) -> ScenarioDefinition:
    """Validate one JSON-like scenario payload against scenario and intake rules."""

    if not isinstance(data, Mapping):
        raise ScenarioValidationError("Scenario payload must be a JSON object with named fields.")

    location = f" '{path}'" if path else ""
    try:
        scenario = ScenarioDefinition.model_validate(data)
    except ValidationError as exc:
        raise ScenarioValidationError(f"Invalid scenario payload{location}: {exc}") from exc

    try:
        validate_case_intake_payload(scenario.intake_payload())
    except IntakeValidationError as exc:
        raise ScenarioValidationError(
            f"Invalid CaseIntake fields in scenario{location}: {exc}"
        ) from exc

    return scenario


@lru_cache(maxsize=1)
def _load_registry_index_cached(directory: Path) -> ScenarioRegistryIndex:
    index_path = directory / SCENARIO_INDEX_FILENAME
    payload = _load_json_file(index_path)
    try:
        index = ScenarioRegistryIndex.model_validate(payload)
    except ValidationError as exc:
        raise ScenarioValidationError(
            f"Invalid scenario registry index '{index_path}': {exc}"
        ) from exc

    known_files = {path.stem for path in directory.glob("*.json") if path.name != SCENARIO_INDEX_FILENAME}
    missing = [slug for slug in index.scenario_order if slug not in known_files]
    if missing:
        raise ScenarioValidationError(
            f"Scenario registry index '{index_path}' references missing scenario file(s): {', '.join(missing)}."
        )
    if index.default_scenario_id not in index.scenario_order:
        raise ScenarioValidationError(
            f"Default scenario '{index.default_scenario_id}' is not present in scenario_order."
        )
    return index


def _load_json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ScenarioValidationError(f"Scenario file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ScenarioValidationError(
            f"Invalid JSON in scenario file '{path}' (line {exc.lineno}, column {exc.colno})."
        ) from exc
    except OSError as exc:
        raise ScenarioValidationError(f"Could not read scenario file '{path}': {exc}") from exc
