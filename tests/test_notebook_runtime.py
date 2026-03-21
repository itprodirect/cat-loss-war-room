"""Tests for stable notebook runtime and scenario preparation helpers."""

from __future__ import annotations

from pathlib import Path

from war_room.bootstrap import BootstrapContext
from war_room.notebook_runtime import (
    build_intake_from_scenario,
    ensure_runtime_context,
    prepare_notebook_scenario,
    resolve_live_retrieval_enabled,
    scenario_warning_message,
)
from war_room.scenarios import load_scenario, scenario_availability_summary, scenario_catalog_availability
from war_room.settings import FeatureFlags, RuntimeEnvironment, WarRoomSettings

ROOT = Path(__file__).resolve().parent.parent


def _settings(*, live_retrieval_enabled: bool) -> WarRoomSettings:
    return WarRoomSettings(
        app_env=RuntimeEnvironment.LOCAL,
        use_cache=True,
        schema_version="v0-demo",
        exa_api_key=None,
        cache_dir=ROOT / "cache",
        cache_samples_dir=ROOT / "cache_samples",
        output_dir=ROOT / "output",
        runs_dir=ROOT / "runs",
        feature_flags=FeatureFlags(
            allow_live_retrieval=live_retrieval_enabled,
            enable_notebook_surface=True,
        ),
    )


def test_ensure_runtime_context_populates_notebook_globals_when_missing_settings(monkeypatch):
    namespace: dict[str, object] = {}
    expected_context = BootstrapContext(repo_root=ROOT, settings=_settings(live_retrieval_enabled=False))

    monkeypatch.setattr(
        "war_room.notebook_runtime.bootstrap_runtime",
        lambda **kwargs: expected_context,
    )

    context = ensure_runtime_context(namespace, ensure_dirs=False)

    assert context == expected_context
    assert namespace["BOOTSTRAP_CONTEXT"] == expected_context
    assert namespace["SETTINGS"] == expected_context.settings
    assert namespace["USE_CACHE"] is True
    assert namespace["CACHE_SAMPLES_DIR"] == str(ROOT / "cache_samples")


def test_resolve_live_retrieval_enabled_uses_explicit_settings():
    assert resolve_live_retrieval_enabled(settings=_settings(live_retrieval_enabled=True)) is True
    assert resolve_live_retrieval_enabled(settings=_settings(live_retrieval_enabled=False)) is False


def test_resolve_live_retrieval_enabled_uses_namespace_settings_without_bootstrap():
    namespace = {"SETTINGS": _settings(live_retrieval_enabled=True)}

    assert resolve_live_retrieval_enabled(namespace=namespace) is True


def test_resolve_live_retrieval_enabled_bootstraps_when_settings_missing(monkeypatch):
    expected_context = BootstrapContext(repo_root=ROOT, settings=_settings(live_retrieval_enabled=False))
    namespace: dict[str, object] = {}

    monkeypatch.setattr(
        "war_room.notebook_runtime.bootstrap_runtime",
        lambda **kwargs: expected_context,
    )

    assert resolve_live_retrieval_enabled(namespace=namespace, ensure_dirs=False) is False
    assert namespace["SETTINGS"] == expected_context.settings


def test_scenario_warning_message_skips_offline_ready_milton_in_offline_mode():
    scenario = load_scenario("milton_pinellas_citizens_ho3", repo_root=ROOT)

    assert scenario_warning_message(scenario, live_retrieval_enabled=False) is None


def test_scenario_warning_message_warns_for_non_offline_ready_scenario_in_offline_mode():
    scenario = load_scenario("ian_lee_citizens_ho3", repo_root=ROOT)

    warning = scenario_warning_message(scenario, live_retrieval_enabled=False)

    assert warning is not None
    assert "ian_lee_citizens_ho3" in warning
    assert "milton_pinellas_citizens_ho3" in warning


def test_scenario_warning_message_suppressed_when_live_retrieval_enabled():
    scenario = load_scenario("irma_monroe_citizens_ho3", repo_root=ROOT)

    assert scenario_warning_message(scenario, live_retrieval_enabled=True) is None


def test_scenario_availability_summary_distinguishes_offline_ready_and_live_only():
    milton = load_scenario("milton_pinellas_citizens_ho3", repo_root=ROOT)
    ian = load_scenario("ian_lee_citizens_ho3", repo_root=ROOT)

    offline_ready = scenario_availability_summary(milton, live_retrieval_enabled=False)
    live_only = scenario_availability_summary(ian, live_retrieval_enabled=False)

    assert offline_ready.status == "offline-ready"
    assert "offline-demo-ready" in offline_ready.detail
    assert live_only.status == "live-only"
    assert "live-only" in live_only.detail


def test_scenario_catalog_availability_reports_current_notebook_statuses():
    summaries = scenario_catalog_availability(ROOT, live_retrieval_enabled=False)

    assert len(summaries) == 5
    assert summaries[0].status == "offline-ready"
    assert {summary.status for summary in summaries} == {"offline-ready", "live-only"}


def test_build_intake_from_scenario_applies_overrides():
    scenario, intake = build_intake_from_scenario(
        "idalia_taylor_default_ho3",
        overrides={"posture": ["underpayment"], "coverage_issues": ["scope of repair"]},
        repo_root=ROOT,
    )

    assert scenario.slug == "idalia_taylor_default_ho3"
    assert intake.posture == ["underpayment"]
    assert intake.coverage_issues == ["scope of repair"]


def test_prepare_notebook_scenario_returns_full_contract_and_warning(monkeypatch):
    namespace: dict[str, object] = {}
    expected_context = BootstrapContext(repo_root=ROOT, settings=_settings(live_retrieval_enabled=False))

    monkeypatch.setattr(
        "war_room.notebook_runtime.bootstrap_runtime",
        lambda **kwargs: expected_context,
    )

    selection = prepare_notebook_scenario(
        "ian_lee_citizens_ho3",
        overrides={"coverage_issues": ["scope of repair"]},
        namespace=namespace,
        ensure_dirs=False,
    )

    assert selection.selected_slug == "ian_lee_citizens_ho3"
    assert selection.scenario.title == "Hurricane Ian (Lee benchmark)"
    assert selection.case_key == "ian_lee_citizens_ho3"
    assert selection.intake.coverage_issues == ["scope of repair"]
    assert selection.live_retrieval_enabled is False
    assert selection.warning_message is not None
    assert selection.scenario_availability.status == "live-only"
    assert selection.available_scenario_summaries[0].status == "offline-ready"
    assert {summary.status for summary in selection.available_scenario_summaries} == {
        "offline-ready",
        "live-only",
    }
    assert namespace["SCENARIO_SELECTION"] == selection
    assert namespace["CASE_KEY"] == "ian_lee_citizens_ho3"
    assert namespace["SETTINGS"] == expected_context.settings
    assert namespace["SCENARIO_AVAILABILITY"].status == "live-only"
    assert len(namespace["SCENARIO_AVAILABILITY_SUMMARIES"]) == 5


def test_prepare_notebook_scenario_uses_existing_context_without_bootstrap(monkeypatch):
    existing_context = BootstrapContext(repo_root=ROOT, settings=_settings(live_retrieval_enabled=True))
    namespace: dict[str, object] = {"BOOTSTRAP_CONTEXT": existing_context}
    bootstrap_called = False

    def _unexpected_bootstrap(**kwargs):
        nonlocal bootstrap_called
        bootstrap_called = True
        return existing_context

    monkeypatch.setattr("war_room.notebook_runtime.bootstrap_runtime", _unexpected_bootstrap)

    selection = prepare_notebook_scenario(
        "michael_bay_default_ho3",
        namespace=namespace,
        ensure_dirs=False,
    )

    assert bootstrap_called is False
    assert selection.live_retrieval_enabled is True
    assert selection.warning_message is None
    assert selection.scenario_availability.status == "live-only"
