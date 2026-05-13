"""Tests for the offline demo e2e gate."""

from __future__ import annotations

import json
from pathlib import Path

from war_room.bootstrap import bootstrap_runtime
from war_room.offline_e2e import (
    SCHEMA_VERSION,
    build_offline_demo_e2e_result,
    main as offline_e2e_main,
    run_offline_demo_e2e,
)
from war_room.preflight import DemoPreflightReport, PreflightCheck, PreflightScenarioReport
from war_room.scenarios import ScenarioAvailabilitySummary

ROOT = Path(__file__).resolve().parent.parent


def test_offline_demo_e2e_writes_structured_artifacts(tmp_path: Path):
    context = bootstrap_runtime(start_path=ROOT, ensure_dirs=False)

    result = run_offline_demo_e2e(context, output_dir=tmp_path / "offline_e2e")

    assert result.schema_version == SCHEMA_VERSION
    assert result.passed is True
    assert result.scenario_count == 4
    assert result.passed_scenario_count == 4
    assert Path(result.json_path).exists()
    assert Path(result.markdown_path).exists()
    assert Path(result.preflight_artifact_path).exists()

    payload = json.loads(Path(result.json_path).read_text(encoding="utf-8"))
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["passed"] is True
    assert payload["scenario_count"] == 4
    assert payload["preflight_artifact_path"] == result.preflight_artifact_path
    assert all(scenario["workflow_status"] == "completed" for scenario in payload["scenarios"])

    preflight_payload = json.loads(Path(result.preflight_artifact_path).read_text(encoding="utf-8"))
    assert preflight_payload["run_id"] == result.run_id
    assert preflight_payload["passed"] is True
    assert preflight_payload["scenario_count"] == result.scenario_count


def test_offline_demo_e2e_cli_check_writes_artifacts(tmp_path: Path, capsys):
    exit_code = offline_e2e_main(["--check", "--output-dir", str(tmp_path / "offline_e2e")])

    assert exit_code == 0
    rendered = capsys.readouterr().out
    assert "Offline e2e passed: 4/4 scenarios passed" in rendered
    assert list((tmp_path / "offline_e2e").glob("*.json"))
    assert list((tmp_path / "offline_e2e" / "preflight").glob("*.json"))


def test_offline_demo_e2e_assertions_report_actionable_failures(tmp_path: Path):
    report = _broken_preflight_report()
    preflight_artifact_path = tmp_path / "missing-preflight.json"
    result = build_offline_demo_e2e_result(
        report,
        preflight_artifact_path=preflight_artifact_path,
        json_path=tmp_path / "offline-e2e.json",
        markdown_path=tmp_path / "offline-e2e.md",
    )

    assert result.passed is False
    failed_assertions = [assertion.name for assertion in result.assertions if not assertion.passed]
    assert "offline preflight passed" in failed_assertions
    assert "committed fixture scenario coverage" in failed_assertions
    assert "preflight artifact is linked and structured" in failed_assertions
    assert result.scenarios[0].failed_checks == ["memo includes disclaimer language"]


def _broken_preflight_report() -> DemoPreflightReport:
    return DemoPreflightReport(
        created_at="2026-05-13T12:00:00+00:00",
        repo_root=str(ROOT),
        cache_samples_dir=str(ROOT / "cache_samples"),
        scenario_count=1,
        scenarios=[
            PreflightScenarioReport(
                case_key="broken_case",
                intake_path="eval/intakes/broken_case.json",
                availability=ScenarioAvailabilitySummary(
                    surface="preflight",
                    scenario_id="broken_case",
                    title="Broken Case",
                    case_key="broken_case",
                    status="offline-ready",
                    detail="Synthetic broken e2e case.",
                ),
                checks=[
                    PreflightCheck("intake payload loads", True, "ok"),
                    PreflightCheck("memo includes disclaimer language", False, "missing"),
                ],
                memo_length=0,
                memo_sections=[],
                workflow_status="failed",
                workflow_review_required=True,
                workflow_stage_statuses=["intake_validation=completed"],
                evidence_cluster_count=0,
                issue_count=0,
                memo_section_count=0,
                export_eligibility="blocked",
                export_artifact_count=0,
                export_delivery_state="",
            )
        ],
    )
