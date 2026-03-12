"""Tests for release scorecard artifact generation."""

from pathlib import Path

from war_room.release_scorecard import (
    DEFAULT_VERIFICATION_COMMAND,
    build_demo_release_scorecard,
    render_release_scorecard_markdown,
    write_release_scorecard_artifacts,
)


def test_build_demo_release_scorecard_uses_expected_baseline():
    scorecard = build_demo_release_scorecard(
        candidate="codex/local",
        verification_summary="170 passed",
        artifact_date="2026-03-11",
    )

    assert scorecard.target_release_level == "Demo-ready"
    assert scorecard.decision == "Ship"
    assert len(scorecard.dimensions) == 7
    assert scorecard.dimensions[0].name == "Reliability"
    assert scorecard.dimensions[0].score == 3
    assert scorecard.must_pass_gates[0].evidence == f"{DEFAULT_VERIFICATION_COMMAND} -> 170 passed"

    markdown = render_release_scorecard_markdown(scorecard)
    assert "# Release Scorecard" in markdown
    assert "codex/local" in markdown
    assert "| Reliability | 3 | Strong |" in markdown


def test_write_release_scorecard_artifacts_writes_json_and_markdown(tmp_path: Path):
    scorecard = build_demo_release_scorecard(
        candidate="Feature Branch 27",
        verification_summary="170 passed",
        artifact_date="2026-03-11",
        evaluators=["codex"],
        blocking_gaps=["Fixture breadth under #8 is still pending."],
        decision="No ship",
    )

    json_path, markdown_path = write_release_scorecard_artifacts(scorecard, output_dir=tmp_path / "scorecards")

    assert json_path.exists()
    assert markdown_path.exists()
    assert json_path.name == "2026-03-11_feature-branch-27.json"
    assert markdown_path.name == "2026-03-11_feature-branch-27.md"

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Fixture breadth under #8 is still pending." in markdown
    assert "- No ship" in markdown

    payload = json_path.read_text(encoding="utf-8")
    assert '"candidate": "Feature Branch 27"' in payload
    assert '"target_release_level": "Demo-ready"' in payload
