"""Tests for repo bootstrap helpers."""

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from war_room.bootstrap import (
    _extract_pytest_summary,
    _write_latest_verify_pointer,
    _write_verify_manifest,
    _resolve_release_candidate,
    bootstrap_runtime,
    discover_repo_root,
    main as bootstrap_main,
)
from war_room.preflight import preflight_run_id, run_demo_preflight, write_preflight_artifact
from war_room.release_scorecard import (
    build_demo_release_scorecard,
    collect_fixture_coverage,
    collect_scenario_registry_coverage,
    summarize_preflight_report,
    write_release_scorecard_artifacts,
)
from war_room.settings import RuntimeEnvironment

ROOT = Path(__file__).resolve().parent.parent


def test_discover_repo_root_from_nested_directory():
    nested = Path(__file__).resolve().parent / "fixtures" / "nested"
    root = discover_repo_root(nested)
    assert (root / "pyproject.toml").exists()


def test_bootstrap_runtime_creates_runtime_directories(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "WAR_ROOM_ENV=local",
                "CACHE_DIR=.runtime/cache",
                "CACHE_SAMPLES_DIR=.runtime/cache_samples",
                "OUTPUT_DIR=.runtime/output",
                "RUNS_DIR=.runtime/runs",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\nversion='0.0.0'\n", encoding="utf-8")

    context = bootstrap_runtime(start_path=tmp_path, env_file=env_file)

    assert context.settings.app_env == RuntimeEnvironment.LOCAL
    assert context.settings.cache_dir.exists()
    assert context.settings.cache_samples_dir.exists()
    assert context.settings.output_dir.exists()
    assert context.settings.runs_dir.exists()


def test_bootstrap_verify_runs_supported_test_command(monkeypatch, capsys):
    commands: list[list[str]] = []
    written_scorecards: list[tuple[str, str]] = []
    written_preflight_artifacts: list[tuple[str, int, str]] = []
    written_manifests: list[tuple[str, str]] = []
    written_latest_pointers: list[tuple[str, str]] = []

    def _fake_run(
        command: list[str],
        cwd: Path,
        capture_output: bool,
        check: bool,
        text: bool,
    ) -> SimpleNamespace:
        commands.append(command)
        assert cwd == Path(__file__).resolve().parent.parent
        assert capture_output is True
        assert check is False
        assert text is True
        return SimpleNamespace(returncode=0, stdout=".....\n5 passed in 0.12s\n", stderr="")

    def _fake_write_preflight(*_args, candidate: str, preflight_report, run_id: str, **_kwargs):
        written_preflight_artifacts.append((candidate, preflight_report.scenario_count, run_id))
        return Path("runs/preflight/test.json")

    def _fake_write_scorecard(
        *_args,
        candidate: str,
        run_id: str,
        verification_summary: str,
        preflight_report,
        preflight_artifact_path,
        **_kwargs,
    ):
        written_scorecards.append((candidate, verification_summary, preflight_report.scenario_count))
        assert run_id == "20260418T120000Z"
        assert preflight_artifact_path == Path("runs/preflight/test.json")
        return (Path("runs/release_scorecards/test.json"), Path("runs/release_scorecards/test.md"))

    def _fake_write_manifest(*_args, run_id: str, verification_summary: str, **_kwargs):
        written_manifests.append((run_id, verification_summary))
        return Path("runs/verify/test.json")

    def _fake_write_latest(*_args, run_id: str, verify_manifest_path: Path, **_kwargs):
        written_latest_pointers.append((run_id, str(verify_manifest_path)))
        return Path("runs/verify/latest.json")

    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    monkeypatch.setattr(subprocess, "run", _fake_run)
    monkeypatch.setattr("war_room.bootstrap._resolve_release_candidate", lambda *_args, **_kwargs: "codex/local")
    monkeypatch.setattr("war_room.bootstrap._resolve_verify_run_id", lambda *_args, **_kwargs: "20260418T120000Z")
    monkeypatch.setattr("war_room.bootstrap._write_verify_preflight_artifact", _fake_write_preflight)
    monkeypatch.setattr("war_room.bootstrap._write_verify_release_scorecard", _fake_write_scorecard)
    monkeypatch.setattr("war_room.bootstrap._write_verify_manifest", _fake_write_manifest)
    monkeypatch.setattr("war_room.bootstrap._write_latest_verify_pointer", _fake_write_latest)

    exit_code = bootstrap_main(["--verify"])

    assert exit_code == 0
    assert commands == [[sys.executable, "-m", "pytest", "-q"]]
    assert written_preflight_artifacts == [("codex/local", 4, "20260418T120000Z")]
    assert written_scorecards == [("codex/local", "5 passed in 0.12s", 4)]
    assert written_manifests == [("20260418T120000Z", "5 passed in 0.12s")]
    assert written_latest_pointers == [("20260418T120000Z", str(Path("runs/verify/test.json")))]
    output = capsys.readouterr().out
    assert "CAT-Loss War Room Verification" in output
    assert "## Verify Manifest" in output
    assert f"Latest: {Path('runs/verify/latest.json')}" in output
    assert "## Preflight Artifact" in output
    assert "Run id: 20260418T120000Z" in output
    assert "## Release Scorecard" in output
    assert "Verification passed." in output


def test_bootstrap_verify_returns_nonzero_when_tests_fail(monkeypatch):
    wrote_scorecard = False
    wrote_preflight_artifact = False
    wrote_manifest = False
    wrote_latest_pointer = False

    def _fake_run(
        command: list[str],
        cwd: Path,
        capture_output: bool,
        check: bool,
        text: bool,
    ) -> SimpleNamespace:
        return SimpleNamespace(returncode=3, stdout="1 failed, 4 passed in 0.12s\n", stderr="")

    def _fake_write_scorecard(*_args, **_kwargs):
        nonlocal wrote_scorecard
        wrote_scorecard = True
        return (Path("runs/release_scorecards/test.json"), Path("runs/release_scorecards/test.md"))

    def _fake_write_preflight(*_args, **_kwargs):
        nonlocal wrote_preflight_artifact
        wrote_preflight_artifact = True
        return Path("runs/preflight/test.json")

    def _fake_write_manifest(*_args, **_kwargs):
        nonlocal wrote_manifest
        wrote_manifest = True
        return Path("runs/verify/test.json")

    def _fake_write_latest(*_args, **_kwargs):
        nonlocal wrote_latest_pointer
        wrote_latest_pointer = True
        return Path("runs/verify/latest.json")

    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    monkeypatch.setattr(subprocess, "run", _fake_run)
    monkeypatch.setattr("war_room.bootstrap._write_verify_preflight_artifact", _fake_write_preflight)
    monkeypatch.setattr("war_room.bootstrap._write_verify_release_scorecard", _fake_write_scorecard)
    monkeypatch.setattr("war_room.bootstrap._write_verify_manifest", _fake_write_manifest)
    monkeypatch.setattr("war_room.bootstrap._write_latest_verify_pointer", _fake_write_latest)

    exit_code = bootstrap_main(["--verify"])

    assert exit_code == 3
    assert wrote_scorecard is False
    assert wrote_preflight_artifact is False
    assert wrote_manifest is False
    assert wrote_latest_pointer is False


def test_bootstrap_verify_honors_release_candidate_override(monkeypatch):
    written_scorecards: list[str] = []
    written_manifests: list[str] = []
    written_latest_pointers: list[str] = []

    def _fake_run(
        command: list[str],
        cwd: Path,
        capture_output: bool,
        check: bool,
        text: bool,
    ) -> SimpleNamespace:
        return SimpleNamespace(returncode=0, stdout="5 passed in 0.12s\n", stderr="")

    def _fake_write_preflight(*_args, candidate: str, run_id: str, **_kwargs):
        return Path(f"runs/preflight/{candidate}-{run_id}.json")

    def _fake_write_scorecard(*_args, candidate: str, run_id: str, preflight_report, preflight_artifact_path, **_kwargs):
        written_scorecards.append(f"{candidate}:{preflight_report.scenario_count}")
        assert run_id == "20260418T120500Z"
        assert preflight_artifact_path == Path("runs/preflight/manual-candidate-20260418T120500Z.json")
        return (Path("runs/release_scorecards/test.json"), Path("runs/release_scorecards/test.md"))

    def _fake_write_manifest(*_args, candidate: str, run_id: str, **_kwargs):
        written_manifests.append(f"{candidate}:{run_id}")
        return Path("runs/verify/test.json")

    def _fake_write_latest(*_args, candidate: str, run_id: str, verify_manifest_path: Path, **_kwargs):
        written_latest_pointers.append(f"{candidate}:{run_id}:{verify_manifest_path}")
        return Path("runs/verify/latest.json")

    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    monkeypatch.setattr(subprocess, "run", _fake_run)
    monkeypatch.setattr("war_room.bootstrap._resolve_verify_run_id", lambda *_args, **_kwargs: "20260418T120500Z")
    monkeypatch.setattr("war_room.bootstrap._write_verify_preflight_artifact", _fake_write_preflight)
    monkeypatch.setattr("war_room.bootstrap._write_verify_release_scorecard", _fake_write_scorecard)
    monkeypatch.setattr("war_room.bootstrap._write_verify_manifest", _fake_write_manifest)
    monkeypatch.setattr("war_room.bootstrap._write_latest_verify_pointer", _fake_write_latest)

    exit_code = bootstrap_main(["--verify", "--release-candidate", "manual-candidate"])

    assert exit_code == 0
    assert written_scorecards == ["manual-candidate:4"]
    assert written_manifests == ["manual-candidate:20260418T120500Z"]
    assert written_latest_pointers == [
        f"manual-candidate:20260418T120500Z:{Path('runs/verify/test.json')}"
    ]


def test_write_latest_verify_pointer_persists_manifest_reference(tmp_path: Path):
    runs_dir = tmp_path / "runs"
    context = SimpleNamespace(settings=SimpleNamespace(runs_dir=runs_dir))

    output_path = _write_latest_verify_pointer(
        context,
        run_id="20260418T163443Z",
        created_at="2026-04-18T16:34:43.652387+00:00",
        candidate="local-verify",
        verify_manifest_path=Path("runs/verify/2026-04-18_local-verify_20260418t163443z.json"),
    )

    assert output_path == runs_dir / "verify" / "latest.json"
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload == {
        "run_id": "20260418T163443Z",
        "created_at": "2026-04-18T16:34:43.652387+00:00",
        "candidate": "local-verify",
        "verify_manifest_path": str(Path("runs/verify/2026-04-18_local-verify_20260418t163443z.json")),
    }


def test_write_verify_manifest_links_existing_artifacts_with_shared_run_id(tmp_path: Path):
    context = bootstrap_runtime(start_path=ROOT, ensure_dirs=False)
    preflight_report = run_demo_preflight(context)
    run_id = preflight_run_id(preflight_report)
    runs_dir = tmp_path / "runs"

    preflight_artifact_path = write_preflight_artifact(
        preflight_report,
        output_dir=runs_dir / "preflight",
        artifact_label="local-verify",
        run_id=run_id,
    )
    fixture_coverage = collect_fixture_coverage(context.settings.cache_samples_dir)
    scenario_registry = collect_scenario_registry_coverage(ROOT, context.settings.cache_samples_dir)
    scorecard = build_demo_release_scorecard(
        run_id=run_id,
        candidate="local-verify",
        verification_summary="5 passed in 0.12s",
        artifact_date=preflight_report.created_at[:10],
        preflight_artifact_path=str(preflight_artifact_path),
        preflight_summary=summarize_preflight_report(preflight_report),
        fixture_coverage=fixture_coverage,
        scenario_registry=scenario_registry,
    )
    scorecard_json_path, scorecard_markdown_path = write_release_scorecard_artifacts(
        scorecard,
        output_dir=runs_dir / "release_scorecards",
    )
    verify_context = SimpleNamespace(repo_root=ROOT, settings=SimpleNamespace(runs_dir=runs_dir))

    manifest_path = _write_verify_manifest(
        verify_context,
        run_id=run_id,
        created_at=preflight_report.created_at,
        candidate="local-verify",
        verification_summary="5 passed in 0.12s",
        preflight_artifact_path=preflight_artifact_path,
        release_scorecard_json_path=scorecard_json_path,
        release_scorecard_markdown_path=scorecard_markdown_path,
    )

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    preflight_payload_path = Path(manifest_payload["preflight_artifact_path"])
    scorecard_payload_path = Path(manifest_payload["release_scorecard_json_path"])
    scorecard_markdown_payload_path = Path(manifest_payload["release_scorecard_markdown_path"])

    assert preflight_payload_path.exists()
    assert scorecard_payload_path.exists()
    assert scorecard_markdown_payload_path.exists()

    preflight_payload = json.loads(preflight_payload_path.read_text(encoding="utf-8"))
    scorecard_payload = json.loads(scorecard_payload_path.read_text(encoding="utf-8"))

    assert manifest_payload["run_id"] == run_id
    assert preflight_payload["run_id"] == run_id
    assert scorecard_payload["run_id"] == run_id
    assert scorecard_payload["preflight_artifact_path"] == manifest_payload["preflight_artifact_path"]


def test_resolve_release_candidate_uses_git_branch(monkeypatch):
    repo_root = Path(__file__).resolve().parent.parent

    def _fake_run(
        command: list[str],
        cwd: Path,
        capture_output: bool,
        check: bool,
        text: bool,
    ) -> SimpleNamespace:
        assert command == [
            "git",
            "-c",
            f"safe.directory={repo_root}",
            "rev-parse",
            "--abbrev-ref",
            "HEAD",
        ]
        assert cwd == repo_root
        return SimpleNamespace(returncode=0, stdout="codex/demo-verify\n", stderr="")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    candidate = _resolve_release_candidate(SimpleNamespace(repo_root=repo_root))

    assert candidate == "codex/demo-verify"


def test_resolve_release_candidate_falls_back_when_branch_is_unavailable(monkeypatch):
    repo_root = Path(__file__).resolve().parent.parent

    def _fake_run(
        command: list[str],
        cwd: Path,
        capture_output: bool,
        check: bool,
        text: bool,
    ) -> SimpleNamespace:
        return SimpleNamespace(returncode=0, stdout="HEAD\n", stderr="")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    candidate = _resolve_release_candidate(SimpleNamespace(repo_root=repo_root))

    assert candidate == "local-verify"


def test_extract_pytest_summary_returns_final_result_line():
    summary = _extract_pytest_summary(
        "tests/test_bootstrap.py .....                                     [100%]\n5 passed in 0.12s\n",
        "",
    )

    assert summary == "5 passed in 0.12s"
