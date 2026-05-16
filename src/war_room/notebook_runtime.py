"""Helpers for stable notebook runtime and scenario preparation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, MutableMapping

from war_room.bootstrap import BootstrapContext, bootstrap_runtime
from war_room.citation_verify import DISCLAIMER as CITATION_REVIEW_DISCLAIMER
from war_room.citation_verify import MAX_CHECKS, spot_check_citations
from war_room.models import CaseIntake
from war_room.models import citation_verify_pack_to_payload
from war_room.scenarios import (
    ScenarioAvailabilitySummary,
    ScenarioDefinition,
    default_scenario_id,
    list_scenarios,
    load_scenario,
    scenario_availability_summary,
    scenario_catalog_availability,
)
from war_room.settings import WarRoomSettings

_DEFAULT_OFFLINE_SCENARIO_ID = "milton_pinellas_citizens_ho3"


@dataclass(frozen=True)
class NotebookScenarioSelection:
    """Resolved notebook scenario plus runtime context and warning state."""

    context: BootstrapContext
    selected_slug: str
    scenario: ScenarioDefinition
    intake: CaseIntake
    case_key: str
    scenario_availability: ScenarioAvailabilitySummary
    available_scenarios: list[ScenarioDefinition]
    available_scenario_summaries: list[ScenarioAvailabilitySummary]
    live_retrieval_enabled: bool
    warning_message: str | None = None


def ensure_runtime_context(
    namespace: MutableMapping[str, Any] | None = None,
    *,
    start_path: Path | None = None,
    env_file: Path | None = None,
    ensure_dirs: bool = True,
) -> BootstrapContext:
    """Return a bootstrap context and publish stable notebook globals when requested."""

    existing = namespace.get("BOOTSTRAP_CONTEXT") if namespace is not None else None
    if isinstance(existing, BootstrapContext):
        context = existing
    else:
        context = bootstrap_runtime(
            start_path=start_path,
            env_file=env_file,
            ensure_dirs=ensure_dirs,
        )

    if namespace is not None:
        _publish_runtime_globals(namespace, context)
    return context


def resolve_live_retrieval_enabled(
    *,
    settings: WarRoomSettings | None = None,
    context: BootstrapContext | None = None,
    namespace: MutableMapping[str, Any] | None = None,
    start_path: Path | None = None,
    env_file: Path | None = None,
    ensure_dirs: bool = True,
) -> bool:
    """Resolve live-retrieval state from explicit settings or a safe bootstrap fallback."""

    if settings is not None:
        return settings.live_retrieval_enabled
    if context is not None:
        return context.settings.live_retrieval_enabled

    namespace_settings = namespace.get("SETTINGS") if namespace is not None else None
    if isinstance(namespace_settings, WarRoomSettings):
        return namespace_settings.live_retrieval_enabled

    context = ensure_runtime_context(
        namespace=namespace,
        start_path=start_path,
        env_file=env_file,
        ensure_dirs=ensure_dirs,
    )
    return context.settings.live_retrieval_enabled


def load_selected_scenario(
    selected_slug: str | None = None,
    *,
    repo_root: Path | None = None,
) -> ScenarioDefinition:
    """Load the requested scenario or the configured notebook default."""

    scenario_id = (selected_slug or default_scenario_id(repo_root=repo_root)).strip()
    return load_scenario(scenario_id, repo_root=repo_root)


def build_intake_from_scenario(
    selected_slug: str | None = None,
    *,
    overrides: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> tuple[ScenarioDefinition, CaseIntake]:
    """Return a scenario and validated CaseIntake with optional notebook overrides."""

    scenario = load_selected_scenario(selected_slug, repo_root=repo_root)
    return scenario, scenario.to_case_intake(overrides)


def scenario_warning_message(
    scenario: ScenarioDefinition,
    *,
    live_retrieval_enabled: bool,
) -> str | None:
    """Return a user-facing warning when a selected scenario cannot run cache-only."""

    if scenario.offline_demo_ready or live_retrieval_enabled:
        return None

    return (
        f"Warning: {scenario.slug} does not have committed offline fixtures. "
        f"Enable live retrieval or switch back to {_DEFAULT_OFFLINE_SCENARIO_ID} "
        f"for the cache-only demo path."
    )


def prepare_notebook_scenario(
    selected_slug: str | None = None,
    *,
    overrides: Mapping[str, Any] | None = None,
    namespace: MutableMapping[str, Any] | None = None,
    start_path: Path | None = None,
    env_file: Path | None = None,
    ensure_dirs: bool = True,
) -> NotebookScenarioSelection:
    """Resolve bootstrap context, selected scenario, intake, and warning state."""

    context = ensure_runtime_context(
        namespace=namespace,
        start_path=start_path,
        env_file=env_file,
        ensure_dirs=ensure_dirs,
    )
    scenario, intake = build_intake_from_scenario(
        selected_slug,
        overrides=overrides,
        repo_root=context.repo_root,
    )
    live_enabled = resolve_live_retrieval_enabled(context=context)
    selection = NotebookScenarioSelection(
        context=context,
        selected_slug=scenario.slug,
        scenario=scenario,
        intake=intake,
        case_key=scenario.case_key,
        scenario_availability=scenario_availability_summary(
            scenario,
            live_retrieval_enabled=live_enabled,
        ),
        available_scenarios=list_scenarios(repo_root=context.repo_root),
        available_scenario_summaries=scenario_catalog_availability(
            repo_root=context.repo_root,
            live_retrieval_enabled=live_enabled,
        ),
        live_retrieval_enabled=live_enabled,
        warning_message=scenario_warning_message(
            scenario,
            live_retrieval_enabled=live_enabled,
        ),
    )
    if namespace is not None:
        namespace["SCENARIO_SELECTION"] = selection
        namespace["SCENARIO"] = selection.scenario
        namespace["CASE_KEY"] = selection.case_key
        namespace["SCENARIO_AVAILABILITY"] = selection.scenario_availability
        namespace["SCENARIO_AVAILABILITY_SUMMARIES"] = selection.available_scenario_summaries
    return selection


def load_notebook_citation_fixture(
    case_key: str,
    *,
    cache_samples_dir: str | Path = "cache_samples",
) -> dict[str, Any] | None:
    """Load the scenario-level citation-review fixture used by cache-only notebooks."""

    fixture_path = Path(cache_samples_dir) / case_key / "citation_verify.json"
    if not fixture_path.exists():
        return None
    return citation_verify_pack_to_payload(
        json.loads(fixture_path.read_text(encoding="utf-8-sig"))
    )


def build_notebook_citation_review(
    caselaw_pack: Any,
    client: Any | None,
    *,
    case_key: str,
    use_cache: bool = True,
    live_retrieval_enabled: bool = False,
    cache_dir: str | Path = "cache",
    cache_samples_dir: str | Path = "cache_samples",
    max_checks: int = MAX_CHECKS,
) -> dict[str, Any]:
    """Return citation review data for notebook runs without requiring live retrieval.

    In live mode with a real provider this preserves the citation spot-check path.
    In offline cache mode it loads the committed scenario fixture before any client
    metadata is accessed.
    """

    if live_retrieval_enabled and client is not None:
        return spot_check_citations(
            caselaw_pack,
            client,
            use_cache=use_cache,
            cache_dir=cache_dir,
            cache_samples_dir=cache_samples_dir,
            max_checks=max_checks,
        )

    if use_cache:
        fixture = load_notebook_citation_fixture(
            case_key,
            cache_samples_dir=cache_samples_dir,
        )
        if fixture is not None:
            return fixture

    return _offline_citation_review_required_payload(
        caselaw_pack,
        case_key=case_key,
        max_checks=max_checks,
    )


def _publish_runtime_globals(
    namespace: MutableMapping[str, Any],
    context: BootstrapContext,
) -> None:
    namespace["BOOTSTRAP_CONTEXT"] = context
    namespace["SETTINGS"] = context.settings
    namespace["USE_CACHE"] = context.settings.use_cache
    namespace["CACHE_DIR"] = str(context.settings.cache_dir)
    namespace["CACHE_SAMPLES_DIR"] = str(context.settings.cache_samples_dir)
    namespace["OUTPUT_DIR"] = str(context.settings.output_dir)
    namespace["RUNS_DIR"] = str(context.settings.runs_dir)


def _offline_citation_review_required_payload(
    caselaw_pack: Any,
    *,
    case_key: str,
    max_checks: int,
) -> dict[str, Any]:
    cases = _citation_cases_from_caselaw(caselaw_pack)[:max_checks]
    if not cases:
        cases = [
            {
                "name": f"{case_key} citation fixture",
                "citation": "",
            }
        ]

    checks = [
        {
            "status": "uncertain",
            "badge": "warning",
            "source_url": None,
            "note": "Offline citation fixture missing - review citations manually before reliance.",
            "case_name": case["name"],
            "citation": case["citation"],
            "confidence": "low",
            "status_reason": "offline_fixture_missing",
            "trust_explanation": (
                "The offline demo did not include a committed citation fixture for this "
                "scenario, and no live citation retrieval was attempted."
            ),
        }
        for case in cases
    ]
    return citation_verify_pack_to_payload(
        {
            "module": "citation_verify",
            "disclaimer": CITATION_REVIEW_DISCLAIMER,
            "checks": checks,
            "summary": {
                "total": len(checks),
                "verified": 0,
                "uncertain": len(checks),
                "not_found": 0,
            },
            "retrieval_tasks": [],
            "run_events": [],
        }
    )


def _citation_cases_from_caselaw(caselaw_pack: Any) -> list[dict[str, str]]:
    if isinstance(caselaw_pack, Mapping):
        issues = caselaw_pack.get("issues", [])
    else:
        issues = getattr(caselaw_pack, "issues", [])

    cases: list[dict[str, str]] = []
    for issue in issues:
        if isinstance(issue, Mapping):
            issue_cases = issue.get("cases", [])
        else:
            issue_cases = getattr(issue, "cases", [])

        for case in issue_cases:
            if isinstance(case, Mapping):
                name = (case.get("name") or "").strip()
                citation = (case.get("citation") or "").strip()
            else:
                name = (getattr(case, "name", "") or "").strip()
                citation = (getattr(case, "citation", "") or "").strip()
            if name and citation:
                cases.append({"name": name, "citation": citation})
    return cases
