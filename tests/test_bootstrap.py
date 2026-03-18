"""Tests for repo bootstrap helpers."""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from war_room.bootstrap import bootstrap_runtime, discover_repo_root, main as bootstrap_main
from war_room.settings import RuntimeEnvironment


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

    def _fake_run(command: list[str], cwd: Path, check: bool) -> SimpleNamespace:
        commands.append(command)
        assert cwd == Path(__file__).resolve().parent.parent
        assert check is False
        return SimpleNamespace(returncode=0)

    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    monkeypatch.setattr(subprocess, "run", _fake_run)

    exit_code = bootstrap_main(["--verify"])

    assert exit_code == 0
    assert commands == [[sys.executable, "-m", "pytest", "-q"]]
    output = capsys.readouterr().out
    assert "CAT-Loss War Room Verification" in output
    assert "Verification passed." in output


def test_bootstrap_verify_returns_nonzero_when_tests_fail(monkeypatch):
    def _fake_run(command: list[str], cwd: Path, check: bool) -> SimpleNamespace:
        return SimpleNamespace(returncode=3)

    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    monkeypatch.setattr(subprocess, "run", _fake_run)

    exit_code = bootstrap_main(["--verify"])

    assert exit_code == 3
