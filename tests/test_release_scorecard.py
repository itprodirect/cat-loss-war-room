"""Tests for release scorecard artifact generation."""

import os
from dataclasses import asdict
from pathlib import Path

from war_room.bootstrap import bootstrap_runtime
from war_room.preflight import DemoPreflightReport, PreflightCheck, PreflightScenarioReport, run_demo_preflight
from war_room.release_scorecard import (
    DEFAULT_VERIFICATION_COMMAND,
    build_demo_release_scorecard,
    collect_fixture_coverage,
    collect_scenario_registry_coverage,
    render_release_scorecard_markdown,
    summarize_preflight_report,
    validate_latest_release_scorecard_artifact,
    validate_release_scorecard_payload,
    write_release_scorecard_artifacts,
)
from war_room.scenarios import ScenarioAvailabilitySummary

ROOT = Path(__file__).resolve().parent.parent
CACHE_SAMPLES_DIR = ROOT / "cache_samples"
REQUIRED_FIXTURE_FILES = ("weather.json", "carrier.json", "caselaw.json", "citation_verify.json")


def _expected_scenario_keys() -> list[str]:
    return sorted(
        path.name
        for path in CACHE_SAMPLES_DIR.iterdir()
        if path.is_dir() and all((path / filename).exists() for filename in REQUIRED_FIXTURE_FILES)
    )


def test_collect_fixture_coverage_reads_committed_scenarios():
    summary = collect_fixture_coverage(CACHE_SAMPLES_DIR)

    assert summary.scenario_count == len(_expected_scenario_keys())
    assert summary.scenario_keys == _expected_scenario_keys()
    assert {"FL", "TX", "LA"} == set(summary.states)
    assert all(len(scenario.module_files) == 4 for scenario in summary.scenarios)


def test_collect_fixture_coverage_ignores_incomplete_scenarios(tmp_path: Path):
    scenario_dir = tmp_path / "partial_case"
    scenario_dir.mkdir()
    (scenario_dir / "weather.json").write_text('{"module": "weather"}', encoding="utf-8")

    summary = collect_fixture_coverage(tmp_path)

    assert summary.scenario_count == 0
    assert summary.scenario_keys == []
    assert summary.states == []


def test_collect_scenario_registry_coverage_reads_curated_registry():
    summary = collect_scenario_registry_coverage(ROOT, CACHE_SAMPLES_DIR)

    assert summary.scenario_count == 8
    assert summary.offline_ready_count == 5
    assert summary.fixture_ready_count == 5
    assert summary.default_scenario_id == "milton_pinellas_citizens_ho3"
    assert summary.states == ["FL", "LA", "TX"]
    assert [scenario.slug for scenario in summary.scenarios] == [
        "milton_pinellas_citizens_ho3",
        "ida_orleans_lloyds_ho3",
        "texas_hail_tarrant_allstate_hob",
        "texas_hail_tarrant_allstate_dp3",
        "ian_lee_citizens_ho3",
        "irma_monroe_citizens_ho3",
        "michael_bay_default_ho3",
        "idalia_taylor_default_ho3",
    ]
    assert summary.scenarios[0].offline_demo_ready is True
    assert summary.scenarios[0].has_committed_fixture_bundle is True
    assert summary.scenarios[1].offline_demo_ready is True
    assert summary.scenarios[1].has_committed_fixture_bundle is True
    assert summary.scenarios[2].offline_demo_ready is True
    assert summary.scenarios[2].has_committed_fixture_bundle is True
    assert summary.scenarios[3].offline_demo_ready is True
    assert summary.scenarios[3].has_committed_fixture_bundle is True
    assert summary.scenarios[4].offline_demo_ready is True
    assert summary.scenarios[4].has_committed_fixture_bundle is True
    assert all(not scenario.offline_demo_ready for scenario in summary.scenarios[5:])
    assert all(not scenario.has_committed_fixture_bundle for scenario in summary.scenarios[5:])


def test_default_verification_command_matches_supported_path():
    assert DEFAULT_VERIFICATION_COMMAND == "pytest -q"


def test_build_demo_release_scorecard_uses_fixture_calibration():
    summary = collect_fixture_coverage(CACHE_SAMPLES_DIR)
    registry = collect_scenario_registry_coverage(ROOT, CACHE_SAMPLES_DIR)
    preflight_summary = summarize_preflight_report(
        run_demo_preflight(bootstrap_runtime(start_path=ROOT, ensure_dirs=False))
    )
    scorecard = build_demo_release_scorecard(
        run_id="20260311T101530Z",
        candidate="codex/local",
        verification_summary="179 passed",
        artifact_date="2026-03-11",
        preflight_artifact_path="runs/preflight/2026-03-11_codex-local_20260311t101530z.json",
        preflight_summary=preflight_summary,
        fixture_coverage=summary,
        scenario_registry=registry,
    )

    assert scorecard.target_release_level == "Demo-ready"
    assert scorecard.decision == "Ship"
    assert scorecard.readiness_posture.target_release_level == "Demo-ready"
    assert scorecard.readiness_posture.demo_ready == "passes"
    assert scorecard.readiness_posture.pilot_ready == "not claimed"
    assert scorecard.readiness_posture.release_ready == "passes for Demo-ready target"
    assert scorecard.readiness_posture.blocking_metric_failed_count == 0
    assert scorecard.readiness_posture.advisory_attention_count == 3
    assert scorecard.readiness_posture.blocking_failures == []
    assert all(threshold.readiness_category == "blocking" for threshold in scorecard.calibration_thresholds)
    assert all(gate.readiness_category == "blocking" for gate in scorecard.must_pass_gates)
    assert all(dimension.readiness_category == "advisory" for dimension in scorecard.dimensions)
    assert len(scorecard.dimensions) == 7
    assert len(scorecard.calibration_thresholds) == 5
    assert all(threshold.passed for threshold in scorecard.calibration_thresholds)
    assert scorecard.dimensions[0].name == "Reliability"
    assert scorecard.dimensions[0].score == 3
    assert scorecard.dimensions[1].name == "Evidence Quality"
    assert scorecard.dimensions[1].score == 2
    assert scorecard.must_pass_gates[0].evidence == f"{DEFAULT_VERIFICATION_COMMAND} -> 179 passed"
    assert scorecard.must_pass_gates[1].passed is True
    assert scorecard.must_pass_gates[2].passed is True
    assert scorecard.run_id == "20260311T101530Z"
    assert scorecard.preflight_summary is not None
    assert scorecard.preflight_artifact_path == "runs/preflight/2026-03-11_codex-local_20260311t101530z.json"
    assert scorecard.preflight_summary.passed is True
    assert scorecard.preflight_summary.scenario_count == len(_expected_scenario_keys())
    assert scorecard.fixture_coverage is not None
    assert scorecard.fixture_coverage.scenario_count == len(_expected_scenario_keys())
    assert scorecard.scenario_registry is not None
    assert scorecard.scenario_registry.scenario_count == 8
    assert scorecard.scenario_registry.offline_ready_count == 5
    assert scorecard.scenario_registry.fixture_ready_count == 5
    assert any("Scenario registry:" in entry for entry in scorecard.evidence_bundle)

    markdown = render_release_scorecard_markdown(scorecard)
    assert "# Release Scorecard" in markdown
    assert "Run id: 20260311T101530Z" in markdown
    assert "codex/local" in markdown
    assert "Preflight artifact: runs/preflight/2026-03-11_codex-local_20260311t101530z.json" in markdown
    assert "## Dashboard Readiness Summary" in markdown
    assert "Demo-ready posture: passes" in markdown
    assert "Pilot-ready posture: not claimed" in markdown
    assert "Blocking metrics: " in markdown
    assert "[blocking][Demo-ready]" in markdown
    assert "## Offline Preflight" in markdown
    assert "## Fixture Coverage" in markdown
    assert "## Scenario Registry" in markdown
    assert "## Threshold Calibration" in markdown
    assert "ida_lloyds_orleans" in markdown
    assert "ian_citizens_lee" in markdown
    assert "milton_pinellas_citizens_ho3" in markdown
    assert "texas_hail_tarrant_allstate_dp3" in markdown
    assert "texas_hail_tarrant_allstate_hob" in markdown


def test_write_release_scorecard_artifacts_writes_json_and_markdown(tmp_path: Path):
    summary = collect_fixture_coverage(CACHE_SAMPLES_DIR)
    registry = collect_scenario_registry_coverage(ROOT, CACHE_SAMPLES_DIR)
    scorecard = build_demo_release_scorecard(
        run_id="20260311T101530Z",
        candidate="Feature Branch 27",
        verification_summary="179 passed",
        artifact_date="2026-03-11",
        evaluators=["codex"],
        blocking_gaps=["CI release-evidence automation is still pending."],
        decision="No ship",
        fixture_coverage=summary,
        scenario_registry=registry,
    )

    json_path, markdown_path = write_release_scorecard_artifacts(scorecard, output_dir=tmp_path / "scorecards")

    assert json_path.exists()
    assert markdown_path.exists()
    assert json_path.name == "2026-03-11_feature-branch-27_20260311t101530z.json"
    assert markdown_path.name == "2026-03-11_feature-branch-27_20260311t101530z.md"

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "CI release-evidence automation is still pending." in markdown
    assert "- No ship" in markdown
    assert "Scenario count:" in markdown
    assert "Scenario Registry" in markdown
    assert "Threshold Calibration" in markdown

    payload = json_path.read_text(encoding="utf-8")
    assert '"run_id": "20260311T101530Z"' in payload
    assert '"candidate": "Feature Branch 27"' in payload
    assert '"target_release_level": "Demo-ready"' in payload
    assert '"readiness_posture"' in payload
    assert '"readiness_category": "blocking"' in payload
    assert '"readiness_category": "advisory"' in payload
    assert '"preflight_artifact_path": null' in payload
    assert '"fixture_coverage"' in payload
    assert '"scenario_registry"' in payload
    assert '"calibration_thresholds"' in payload


def test_validate_release_scorecard_payload_accepts_demo_ready_artifact():
    summary = collect_fixture_coverage(CACHE_SAMPLES_DIR)
    registry = collect_scenario_registry_coverage(ROOT, CACHE_SAMPLES_DIR)
    scorecard = build_demo_release_scorecard(
        run_id="20260418T120000Z",
        candidate="codex/local",
        verification_summary="179 passed",
        artifact_date="2026-04-18",
        fixture_coverage=summary,
        scenario_registry=registry,
    )

    assert validate_release_scorecard_payload(asdict(scorecard)) == []


def test_validate_release_scorecard_payload_reports_actionable_failures():
    payload = {
        "calibration_thresholds": [
            {"name": "Fixture scenario count", "passed": False},
        ],
        "must_pass_gates": [
            {"name": "Committed fixture coverage meets demo-ready threshold", "passed": False},
        ],
        "decision": "No ship",
    }

    failures = validate_release_scorecard_payload(payload)

    assert any("dashboard readiness posture" in failure for failure in failures)
    assert any("Fixture scenario count" in failure for failure in failures)
    assert any("Committed fixture coverage meets demo-ready threshold" in failure for failure in failures)
    assert any("No ship" in failure for failure in failures)


def test_validate_release_scorecard_payload_requires_dashboard_categories():
    summary = collect_fixture_coverage(CACHE_SAMPLES_DIR)
    registry = collect_scenario_registry_coverage(ROOT, CACHE_SAMPLES_DIR)
    scorecard = build_demo_release_scorecard(
        run_id="20260418T120000Z",
        candidate="codex/local",
        verification_summary="179 passed",
        artifact_date="2026-04-18",
        fixture_coverage=summary,
        scenario_registry=registry,
    )
    payload = asdict(scorecard)
    payload["calibration_thresholds"][0].pop("readiness_category")
    payload["must_pass_gates"][0].pop("readiness_category")
    payload["dimensions"][0].pop("readiness_category")

    failures = validate_release_scorecard_payload(payload)

    assert any("thresholds are missing readiness categories" in failure for failure in failures)
    assert any("gates are missing readiness categories" in failure for failure in failures)
    assert any("dimensions are missing readiness categories" in failure for failure in failures)


def test_validate_latest_release_scorecard_artifact_reads_newest_json(tmp_path: Path):
    summary = collect_fixture_coverage(CACHE_SAMPLES_DIR)
    registry = collect_scenario_registry_coverage(ROOT, CACHE_SAMPLES_DIR)
    scorecard = build_demo_release_scorecard(
        run_id="20260418T120000Z",
        candidate="codex/local",
        verification_summary="179 passed",
        artifact_date="2026-04-18",
        fixture_coverage=summary,
        scenario_registry=registry,
    )
    json_path, _markdown_path = write_release_scorecard_artifacts(scorecard, output_dir=tmp_path)

    artifact_path, failures = validate_latest_release_scorecard_artifact(tmp_path)

    assert artifact_path == json_path
    assert failures == []


def test_validate_latest_release_scorecard_artifact_uses_newest_modified_file(tmp_path: Path):
    summary = collect_fixture_coverage(CACHE_SAMPLES_DIR)
    registry = collect_scenario_registry_coverage(ROOT, CACHE_SAMPLES_DIR)
    older_scorecard = build_demo_release_scorecard(
        run_id="20260418T120000Z",
        candidate="zz-old-name",
        verification_summary="179 passed",
        artifact_date="2026-04-18",
        fixture_coverage=summary,
        scenario_registry=registry,
    )
    newer_scorecard = build_demo_release_scorecard(
        run_id="20260418T120100Z",
        candidate="aa-new-name",
        verification_summary="179 passed",
        artifact_date="2026-04-18",
        fixture_coverage=summary,
        scenario_registry=registry,
    )
    older_json_path, _older_markdown_path = write_release_scorecard_artifacts(older_scorecard, output_dir=tmp_path)
    newer_json_path, _newer_markdown_path = write_release_scorecard_artifacts(newer_scorecard, output_dir=tmp_path)
    os.utime(older_json_path, (100, 100))
    os.utime(newer_json_path, (200, 200))

    artifact_path, failures = validate_latest_release_scorecard_artifact(tmp_path)

    assert older_json_path.name > newer_json_path.name
    assert artifact_path == newer_json_path
    assert failures == []


def test_build_demo_release_scorecard_marks_failed_verification_gate():
    summary = collect_fixture_coverage(CACHE_SAMPLES_DIR)
    registry = collect_scenario_registry_coverage(ROOT, CACHE_SAMPLES_DIR)
    scorecard = build_demo_release_scorecard(
        run_id="20260418T120000Z",
        candidate="codex/local",
        verification_summary="1 failed, 178 passed",
        artifact_date="2026-03-18",
        fixture_coverage=summary,
        scenario_registry=registry,
    )

    assert scorecard.dimensions[0].score == 0
    assert scorecard.must_pass_gates[0].passed is False
    assert scorecard.readiness_posture.demo_ready == "blocked"
    assert scorecard.readiness_posture.blocking_metric_failed_count == 2
    assert "Supported test path is green" in scorecard.readiness_posture.blocking_failures
    assert any("Blocked quality dimensions" in failure for failure in scorecard.readiness_posture.blocking_failures)


def test_summarize_preflight_report_captures_failed_scenarios():
    report = DemoPreflightReport(
        created_at="2026-04-18T12:00:00+00:00",
        repo_root=str(ROOT),
        cache_samples_dir=str(CACHE_SAMPLES_DIR),
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
                    detail="Synthetic test fixture.",
                ),
                checks=[
                    PreflightCheck(name="intake payload loads", passed=True, evidence="ok"),
                    PreflightCheck(name="memo includes disclaimer language", passed=False, evidence="missing"),
                ],
                workflow_status="failed",
                workflow_review_required=True,
            )
        ],
    )

    summary = summarize_preflight_report(report)

    assert summary.passed is False
    assert summary.scenario_count == 1
    assert summary.passed_scenario_count == 0
    assert summary.scenario_keys == ["broken_case"]
    assert summary.scenarios[0].failed_checks == ["memo includes disclaimer language"]


def test_build_demo_release_scorecard_marks_failed_preflight_gate():
    summary = collect_fixture_coverage(CACHE_SAMPLES_DIR)
    registry = collect_scenario_registry_coverage(ROOT, CACHE_SAMPLES_DIR)
    preflight_summary = summarize_preflight_report(
        DemoPreflightReport(
            created_at="2026-04-18T12:00:00+00:00",
            repo_root=str(ROOT),
            cache_samples_dir=str(CACHE_SAMPLES_DIR),
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
                        detail="Synthetic test fixture.",
                    ),
                    checks=[
                        PreflightCheck(name="offline smoke execution", passed=False, evidence="RuntimeError: boom"),
                    ],
                    workflow_status="failed",
                    workflow_review_required=True,
                )
            ],
        )
    )
    scorecard = build_demo_release_scorecard(
        run_id="20260418T120000Z",
        candidate="codex/local",
        verification_summary="179 passed",
        artifact_date="2026-04-18",
        preflight_summary=preflight_summary,
        fixture_coverage=summary,
        scenario_registry=registry,
    )

    assert scorecard.dimensions[0].score == 1
    assert scorecard.dimensions[0].verdict == "Weak"
    assert scorecard.must_pass_gates[1].passed is False
    assert "0/1 scenarios passed" in scorecard.must_pass_gates[1].evidence
    assert scorecard.readiness_posture.demo_ready == "blocked"
    assert scorecard.readiness_posture.blocking_metric_failed_count == 1
