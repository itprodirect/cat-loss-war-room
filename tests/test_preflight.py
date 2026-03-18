"""Tests for the deterministic offline demo preflight."""

from __future__ import annotations

import json
from pathlib import Path

from war_room.bootstrap import bootstrap_runtime, main as bootstrap_main
from war_room.preflight import render_demo_preflight_report, run_demo_preflight
from tests.test_offline_demo_pack import SCENARIOS

ROOT = Path(__file__).resolve().parent.parent


def test_demo_preflight_smoke_covers_committed_scenarios():
    context = bootstrap_runtime(start_path=ROOT, ensure_dirs=False)

    report = run_demo_preflight(context)

    assert report.scenario_count == len(SCENARIOS)
    assert report.passed is True

    scenario_keys = [scenario.case_key for scenario in report.scenarios]
    assert scenario_keys == sorted(SCENARIOS)

    for scenario in report.scenarios:
        check_names = {check.name for check in scenario.checks}
        assert "intake payload loads" in check_names
        assert "memo includes disclaimer language" in check_names
        assert "memo includes expected major sections" in check_names
        assert scenario.memo_length > 0
        assert len(scenario.memo_sections) == 10


def test_demo_preflight_rendering_includes_summary():
    context = bootstrap_runtime(start_path=ROOT, ensure_dirs=False)
    report = run_demo_preflight(context)

    rendered = render_demo_preflight_report(report)

    assert "# Demo Preflight" in rendered
    assert f"Scenario count: {len(SCENARIOS)}" in rendered
    assert "ida_lloyds_orleans" in rendered
    assert "Passed: Yes" in rendered


def test_bootstrap_cli_preflight_json_output(monkeypatch, capsys):
    monkeypatch.chdir(ROOT)

    exit_code = bootstrap_main(["--preflight", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True
    assert payload["scenario_count"] == len(SCENARIOS)
    assert len(payload["scenarios"]) == len(SCENARIOS)
