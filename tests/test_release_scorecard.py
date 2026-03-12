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


def test_collect_fixture_coverage_reads_committed_scenarios():
    summary = collect_fixture_coverage(CACHE_SAMPLES_DIR)

    assert summary.scenario_count >= 3
    assert {"FL", "TX", "LA"}.issubset(set(summary.states))
    assert "milton_citizens_pinellas" in summary.scenario_keys
    assert "tx_hail_allstate_tarrant" in summary.scenario_keys
    assert "ida_lloyds_orleans" in summary.scenario_keys


def test_build_demo_release_scorecard_uses_fixture_calibration():
    summary = collect_fixture_coverage(CACHE_SAMPLES_DIR)
    scorecard = build_demo_release_scorecard(
        candidate="codex/local",
        verification_summary="178 passed",
        artifact_date="2026-03-11",
        fixture_coverage=summary,
    )

    assert scorecard.target_release_level == "Demo-ready"
    assert scorecard.decision == "Ship"
    assert len(scorecard.dimensions) == 7
    assert scorecard.dimensions[0].name == "Reliability"
    assert scorecard.dimensions[0].score == 3
    assert scorecard.must_pass_gates[0].evidence == f"{DEFAULT_VERIFICATION_COMMAND} -> 178 passed"
    assert scorecard.fixture_coverage is not None
    assert scorecard.fixture_coverage.scenario_count >= 3

    markdown = render_release_scorecard_markdown(scorecard)
    assert "# Release Scorecard" in markdown
    assert "codex/local" in markdown
    assert "## Fixture Coverage" in markdown
    assert "ida_lloyds_orleans" in markdown


def test_write_release_scorecard_artifacts_writes_json_and_markdown(tmp_path: Path):
    summary = collect_fixture_coverage(CACHE_SAMPLES_DIR)
    scorecard = build_demo_release_scorecard(
        candidate="Feature Branch 27",
        verification_summary="178 passed",
        artifact_date="2026-03-11",
        evaluators=["codex"],
        blocking_gaps=["Scenario pass/fail thresholds are still not calibrated."],
        decision="No ship",
        fixture_coverage=summary,
    )

    json_path, markdown_path = write_release_scorecard_artifacts(scorecard, output_dir=tmp_path / "scorecards")

    assert json_path.exists()
    assert markdown_path.exists()
    assert json_path.name == "2026-03-11_feature-branch-27.json"
    assert markdown_path.name == "2026-03-11_feature-branch-27.md"

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Scenario pass/fail thresholds are still not calibrated." in markdown
    assert "- No ship" in markdown
    assert "Scenario count:" in markdown

    payload = json_path.read_text(encoding="utf-8")
    assert '"candidate": "Feature Branch 27"' in payload
    assert '"target_release_level": "Demo-ready"' in payload
    assert '"fixture_coverage"' in payload
