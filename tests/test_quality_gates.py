"""Tests for categorized CI quality-gate artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from war_room.quality_gates import (
    collect_quality_gate_results,
    main as quality_gate_main,
    render_quality_gate_summary,
    run_quality_gate,
    write_quality_gate_summary,
)

ROOT = Path(__file__).resolve().parent.parent


def test_run_quality_gate_writes_structured_artifacts(tmp_path: Path):
    result = run_quality_gate(
        gate_id="unit-tests",
        command=[sys.executable, "-c", "print('3 passed in 0.01s')"],
        output_dir=tmp_path,
        repo_root=ROOT,
    )

    assert result.status == "passed"
    assert result.exit_code == 0
    assert result.category == "unit"
    assert result.summary == "3 passed in 0.01s"
    assert Path(result.log_path).exists()
    assert Path(result.json_path).exists()
    assert Path(result.markdown_path).exists()

    payload = json.loads(Path(result.json_path).read_text(encoding="utf-8"))
    assert payload["schema_version"] == "ci-quality-gate.v1"
    assert payload["gate_id"] == "unit-tests"
    assert payload["status"] == "passed"


def test_run_quality_gate_records_failed_command_without_raising(tmp_path: Path):
    result = run_quality_gate(
        gate_id="golden-snapshot-check",
        command=[
            sys.executable,
            "-c",
            "import sys; print('Offline fixture snapshot differs from committed golden file.'); sys.exit(2)",
        ],
        output_dir=tmp_path,
        repo_root=ROOT,
    )

    assert result.status == "failed"
    assert result.exit_code == 2
    assert result.category == "golden_snapshot"
    assert "differs" in result.summary
    assert "Offline fixture snapshot differs" in Path(result.log_path).read_text(encoding="utf-8")


def test_security_hygiene_gate_is_categorized(tmp_path: Path):
    result = run_quality_gate(
        gate_id="security-hygiene-check",
        command=[sys.executable, "-c", "print('Security hygiene check passed: 6/6 checks passed')"],
        output_dir=tmp_path,
        repo_root=ROOT,
    )

    assert result.status == "passed"
    assert result.category == "security_hygiene"
    assert result.name == "Security Hygiene Gate"
    assert result.summary == "Security hygiene check passed: 6/6 checks passed"


def test_offline_e2e_gate_is_categorized(tmp_path: Path):
    result = run_quality_gate(
        gate_id="e2e-offline-demo",
        command=[
            sys.executable,
            "-c",
            "print('Offline e2e passed: 4/4 scenarios passed; artifacts: runs/offline_e2e/test.json')",
        ],
        output_dir=tmp_path,
        repo_root=ROOT,
    )

    assert result.status == "passed"
    assert result.category == "e2e_offline"
    assert result.name == "Offline E2E Demo Gate"
    assert "Offline e2e passed" in result.summary


def test_write_quality_gate_summary_groups_passed_and_failed_results(tmp_path: Path):
    run_quality_gate(
        gate_id="offline-fixture-tests",
        command=[sys.executable, "-c", "print('12 passed in 0.02s')"],
        output_dir=tmp_path,
        repo_root=ROOT,
    )
    run_quality_gate(
        gate_id="release-scorecard-validate",
        command=[sys.executable, "-c", "import sys; print('Release scorecard validation failed'); sys.exit(1)"],
        output_dir=tmp_path,
        repo_root=ROOT,
    )

    summary_path, results = write_quality_gate_summary(
        output_dir=tmp_path,
        summary_path=tmp_path / "summary.md",
    )
    rendered = summary_path.read_text(encoding="utf-8")

    assert len(results) == 2
    assert "Offline Fixture Gate" in rendered
    assert "Release Scorecard Validation Gate" in rendered
    assert "Failed Gates" in rendered
    assert "release_scorecard" in rendered


def test_quality_gate_cli_run_sets_github_output(tmp_path: Path, monkeypatch):
    github_output = tmp_path / "github_output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))

    exit_code = quality_gate_main(
        [
            "run",
            "--gate",
            "unit-tests",
            "--output-dir",
            str(tmp_path / "gates"),
            "--github-output-key",
            "verification_summary",
            "--",
            sys.executable,
            "-c",
            "print('4 passed in 0.03s')",
        ]
    )

    assert exit_code == 0
    assert "verification_summary<<EOF" in github_output.read_text(encoding="utf-8")
    assert collect_quality_gate_results(tmp_path / "gates")[0].summary == "4 passed in 0.03s"


def test_render_quality_gate_summary_handles_empty_results():
    rendered = render_quality_gate_summary([])

    assert "Total gates: 0" in rendered
    assert "Failed: 0" in rendered
