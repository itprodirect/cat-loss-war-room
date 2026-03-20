"""Tests for the deterministic offline demo preflight."""

from __future__ import annotations

import json
from pathlib import Path

from war_room.bootstrap import bootstrap_runtime, main as bootstrap_main
from war_room.preflight import render_demo_preflight_report, run_demo_preflight

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FIXTURE_FILES = ("weather.json", "carrier.json", "caselaw.json", "citation_verify.json")


def _expected_scenario_keys() -> list[str]:
    cache_samples_dir = ROOT / "cache_samples"
    return sorted(
        path.name
        for path in cache_samples_dir.iterdir()
        if path.is_dir() and all((path / filename).exists() for filename in REQUIRED_FIXTURE_FILES)
    )


def test_demo_preflight_smoke_covers_committed_scenarios():
    context = bootstrap_runtime(start_path=ROOT, ensure_dirs=False)

    report = run_demo_preflight(context)

    assert report.scenario_count == len(_expected_scenario_keys())
    assert report.passed is True

    scenario_keys = [scenario.case_key for scenario in report.scenarios]
    assert scenario_keys == _expected_scenario_keys()
    assert report.scenarios[scenario_keys.index("milton_citizens_pinellas")].intake_path == "scenario:milton_pinellas_citizens_ho3"

    for scenario in report.scenarios:
        assert scenario.availability.status == "offline-ready"
        check_names = {check.name for check in scenario.checks}
        assert "intake payload loads" in check_names
        assert "memo includes disclaimer language" in check_names
        assert "memo includes expected major sections" in check_names
        assert scenario.memo_length > 0
        assert len(scenario.memo_sections) == 10
    assert any("Registry scenario" in scenario.availability.detail for scenario in report.scenarios)
    assert any("No registry scenario maps" in scenario.availability.detail for scenario in report.scenarios)


def test_demo_preflight_rendering_includes_summary():
    context = bootstrap_runtime(start_path=ROOT, ensure_dirs=False)
    report = run_demo_preflight(context)

    rendered = render_demo_preflight_report(report)

    assert "# Demo Preflight" in rendered
    assert f"Scenario count: {len(_expected_scenario_keys())}" in rendered
    assert "ida_lloyds_orleans" in rendered
    assert "Passed: Yes" in rendered
    assert "Availability: offline-ready" in rendered
    assert "Registry scenario" in rendered


def test_bootstrap_cli_preflight_json_output(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)

    exit_code = bootstrap_main(["--preflight", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True
    assert payload["scenario_count"] == len(_expected_scenario_keys())
    assert len(payload["scenarios"]) == len(_expected_scenario_keys())
    assert payload["scenarios"][0]["availability"]["status"] == "offline-ready"
