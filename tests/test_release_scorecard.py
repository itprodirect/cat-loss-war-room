"""Tests for release scorecard artifact generation."""

from pathlib import Path

from war_room.release_scorecard import (
    DEFAULT_VERIFICATION_COMMAND,
    build_demo_release_scorecard,
    collect_fixture_coverage,
    render_release_scorecard_markdown,
    write_release_scorecard_artifacts,
)

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


def test_default_verification_command_matches_supported_path():
    assert DEFAULT_VERIFICATION_COMMAND == "pytest -q"


def test_build_demo_release_scorecard_uses_fixture_calibration():
    summary = collect_fixture_coverage(CACHE_SAMPLES_DIR)
    scorecard = build_demo_release_scorecard(
        candidate="codex/local",
        verification_summary="179 passed",
        artifact_date="2026-03-11",
        fixture_coverage=summary,
    )

    assert scorecard.target_release_level == "Demo-ready"
    assert scorecard.decision == "Ship"
    assert len(scorecard.dimensions) == 7
    assert len(scorecard.calibration_thresholds) == 5
    assert all(threshold.passed for threshold in scorecard.calibration_thresholds)
    assert scorecard.dimensions[0].name == "Reliability"
    assert scorecard.dimensions[0].score == 3
    assert scorecard.dimensions[1].name == "Evidence Quality"
    assert scorecard.dimensions[1].score == 2
    assert scorecard.must_pass_gates[0].evidence == f"{DEFAULT_VERIFICATION_COMMAND} -> 179 passed"
    assert scorecard.must_pass_gates[2].passed is True
    assert scorecard.fixture_coverage is not None
    assert scorecard.fixture_coverage.scenario_count == len(_expected_scenario_keys())

    markdown = render_release_scorecard_markdown(scorecard)
    assert "# Release Scorecard" in markdown
    assert "codex/local" in markdown
    assert "## Fixture Coverage" in markdown
    assert "## Threshold Calibration" in markdown
    assert "ida_lloyds_orleans" in markdown


def test_write_release_scorecard_artifacts_writes_json_and_markdown(tmp_path: Path):
    summary = collect_fixture_coverage(CACHE_SAMPLES_DIR)
    scorecard = build_demo_release_scorecard(
        candidate="Feature Branch 27",
        verification_summary="179 passed",
        artifact_date="2026-03-11",
        evaluators=["codex"],
        blocking_gaps=["CI release-evidence automation is still pending."],
        decision="No ship",
        fixture_coverage=summary,
    )

    json_path, markdown_path = write_release_scorecard_artifacts(scorecard, output_dir=tmp_path / "scorecards")

    assert json_path.exists()
    assert markdown_path.exists()
    assert json_path.name == "2026-03-11_feature-branch-27.json"
    assert markdown_path.name == "2026-03-11_feature-branch-27.md"

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "CI release-evidence automation is still pending." in markdown
    assert "- No ship" in markdown
    assert "Scenario count:" in markdown
    assert "Threshold Calibration" in markdown

    payload = json_path.read_text(encoding="utf-8")
    assert '"candidate": "Feature Branch 27"' in payload
    assert '"target_release_level": "Demo-ready"' in payload
    assert '"fixture_coverage"' in payload
    assert '"calibration_thresholds"' in payload


def test_build_demo_release_scorecard_marks_failed_verification_gate():
    summary = collect_fixture_coverage(CACHE_SAMPLES_DIR)
    scorecard = build_demo_release_scorecard(
        candidate="codex/local",
        verification_summary="1 failed, 178 passed",
        artifact_date="2026-03-18",
        fixture_coverage=summary,
    )

    assert scorecard.dimensions[0].score == 0
    assert scorecard.must_pass_gates[0].passed is False
