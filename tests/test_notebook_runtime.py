"""Tests for stable notebook runtime and scenario preparation helpers."""

from __future__ import annotations

from pathlib import Path

from war_room.bootstrap import BootstrapContext
from war_room.notebook_runtime import (
    build_intake_from_scenario,
    build_notebook_citation_review,
    ensure_runtime_context,
    load_notebook_citation_fixture,
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
    scenario = load_scenario("irma_monroe_citizens_ho3", repo_root=ROOT)

    warning = scenario_warning_message(scenario, live_retrieval_enabled=False)

    assert warning is not None
    assert "irma_monroe_citizens_ho3" in warning
    assert "milton_pinellas_citizens_ho3" in warning


def test_scenario_warning_message_suppressed_when_live_retrieval_enabled():
    scenario = load_scenario("irma_monroe_citizens_ho3", repo_root=ROOT)

    assert scenario_warning_message(scenario, live_retrieval_enabled=True) is None


def test_scenario_availability_summary_distinguishes_offline_ready_and_live_only():
    milton = load_scenario("milton_pinellas_citizens_ho3", repo_root=ROOT)
    irma = load_scenario("irma_monroe_citizens_ho3", repo_root=ROOT)

    offline_ready = scenario_availability_summary(milton, live_retrieval_enabled=False)
    live_only = scenario_availability_summary(irma, live_retrieval_enabled=False)

    assert offline_ready.status == "offline-ready"
    assert "offline-demo-ready" in offline_ready.detail
    assert live_only.status == "live-only"
    assert "live-only" in live_only.detail


def test_scenario_catalog_availability_reports_current_notebook_statuses():
    summaries = scenario_catalog_availability(ROOT, live_retrieval_enabled=False)

    assert len(summaries) == 8
    assert summaries[0].status == "offline-ready"
    assert summaries[1].status == "offline-ready"
    assert summaries[1].scenario_id == "ida_orleans_lloyds_ho3"
    assert summaries[2].status == "offline-ready"
    assert summaries[2].scenario_id == "texas_hail_tarrant_allstate_hob"
    assert summaries[3].status == "offline-ready"
    assert summaries[3].scenario_id == "texas_hail_tarrant_allstate_dp3"
    assert summaries[4].status == "offline-ready"
    assert summaries[4].scenario_id == "ian_lee_citizens_ho3"
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


def test_load_notebook_citation_fixture_reads_scenario_fixture():
    citecheck = load_notebook_citation_fixture(
        "milton_citizens_pinellas",
        cache_samples_dir=ROOT / "cache_samples",
    )

    assert citecheck is not None
    assert citecheck["module"] == "citation_verify"
    assert citecheck["summary"]["total"] == 6
    assert citecheck["summary"]["verified"] >= 1


def test_build_notebook_citation_review_uses_offline_fixture_with_null_client(monkeypatch):
    caselaw = {
        "issues": [
            {
                "issue": "Coverage",
                "cases": [{"name": "Doe v. Ins", "citation": "123 So.3d 456"}],
            }
        ],
    }

    def _unexpected_live_check(*args, **kwargs):
        raise AssertionError("offline notebook path should not call live citation spot-checking")

    monkeypatch.setattr("war_room.notebook_runtime.spot_check_citations", _unexpected_live_check)

    citecheck = build_notebook_citation_review(
        caselaw,
        None,
        case_key="milton_citizens_pinellas",
        use_cache=True,
        live_retrieval_enabled=False,
        cache_samples_dir=ROOT / "cache_samples",
    )

    assert citecheck["module"] == "citation_verify"
    assert citecheck["summary"]["total"] == 6
    assert citecheck["summary"]["verified"] >= 1


def test_build_notebook_citation_review_preserves_live_spot_check_when_client_exists(monkeypatch, tmp_path):
    caselaw = {
        "issues": [
            {
                "issue": "Coverage",
                "cases": [{"name": "Doe v. Ins", "citation": "123 So.3d 456"}],
            }
        ],
    }
    observed: dict[str, object] = {}
    client = object()

    def _live_check(caselaw_pack, client_arg, **kwargs):
        observed["caselaw_pack"] = caselaw_pack
        observed["client"] = client_arg
        observed["kwargs"] = kwargs
        return {
            "module": "citation_verify",
            "disclaimer": "CITATION SPOT-CHECK ONLY - review required.",
            "checks": [],
            "summary": {"total": 0, "verified": 0, "uncertain": 0, "not_found": 0},
        }

    monkeypatch.setattr("war_room.notebook_runtime.spot_check_citations", _live_check)

    citecheck = build_notebook_citation_review(
        caselaw,
        client,
        case_key="missing_fixture",
        use_cache=True,
        live_retrieval_enabled=True,
        cache_dir=tmp_path / "cache",
        cache_samples_dir=tmp_path / "cache_samples",
    )

    assert citecheck["module"] == "citation_verify"
    assert observed["caselaw_pack"] == caselaw
    assert observed["client"] is client
    assert observed["kwargs"] == {
        "use_cache": True,
        "cache_dir": tmp_path / "cache",
        "cache_samples_dir": tmp_path / "cache_samples",
        "max_checks": 6,
    }


def test_build_notebook_citation_review_returns_safe_payload_when_offline_fixture_missing(tmp_path):
    caselaw = {
        "issues": [
            {
                "issue": "Coverage",
                "cases": [
                    {"name": "Doe v. Ins", "citation": "123 So.3d 456"},
                    {"name": "Blank v. Case", "citation": ""},
                ],
            }
        ],
    }

    citecheck = build_notebook_citation_review(
        caselaw,
        None,
        case_key="missing_fixture",
        use_cache=True,
        live_retrieval_enabled=False,
        cache_samples_dir=tmp_path,
    )

    assert citecheck["module"] == "citation_verify"
    assert citecheck["summary"] == {
        "total": 1,
        "verified": 0,
        "uncertain": 1,
        "not_found": 0,
    }
    assert citecheck["checks"][0]["case_name"] == "Doe v. Ins"
    assert citecheck["checks"][0]["status"] == "uncertain"
    assert citecheck["checks"][0]["badge"] == "warning"
    assert citecheck["checks"][0]["status_reason"] == "offline_fixture_missing"
    assert "review citations manually" in citecheck["checks"][0]["note"]
    assert "CITATION SPOT-CHECK ONLY" in citecheck["disclaimer"]


def test_prepare_notebook_scenario_returns_full_contract_and_warning(monkeypatch):
    namespace: dict[str, object] = {}
    expected_context = BootstrapContext(repo_root=ROOT, settings=_settings(live_retrieval_enabled=False))

    monkeypatch.setattr(
        "war_room.notebook_runtime.bootstrap_runtime",
        lambda **kwargs: expected_context,
    )

    selection = prepare_notebook_scenario(
        "irma_monroe_citizens_ho3",
        overrides={"coverage_issues": ["scope of repair"]},
        namespace=namespace,
        ensure_dirs=False,
    )

    assert selection.selected_slug == "irma_monroe_citizens_ho3"
    assert selection.scenario.title == "Hurricane Irma (Monroe mature/legal benchmark)"
    assert selection.case_key == "irma_monroe_citizens_ho3"
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
    assert namespace["CASE_KEY"] == "irma_monroe_citizens_ho3"
    assert namespace["SETTINGS"] == expected_context.settings
    assert namespace["SCENARIO_AVAILABILITY"].status == "live-only"
    assert len(namespace["SCENARIO_AVAILABILITY_SUMMARIES"]) == 8


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
