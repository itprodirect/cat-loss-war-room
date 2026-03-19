"""Helpers for stable notebook runtime and scenario preparation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, MutableMapping

from war_room.bootstrap import BootstrapContext, bootstrap_runtime
from war_room.models import CaseIntake
from war_room.scenarios import (
    ScenarioDefinition,
    default_scenario_id,
    list_scenarios,
    load_scenario,
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
    available_scenarios: list[ScenarioDefinition]
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
        available_scenarios=list_scenarios(repo_root=context.repo_root),
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
    return selection


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
