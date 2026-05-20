"""Tests for the shared runtime settings layer."""

from pathlib import Path

import pytest

from war_room.settings import RuntimeEnvironment, load_settings


def test_demo_env_disables_live_retrieval(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("WAR_ROOM_ENV=demo\nUSE_CACHE=false\nALLOW_LIVE_RETRIEVAL=true\n", encoding="utf-8")

    settings = load_settings(repo_root=tmp_path, env_file=env_file)

    assert settings.app_env == RuntimeEnvironment.DEMO
    assert settings.use_cache is True
    assert settings.offline_demo is True
    assert settings.live_retrieval_enabled is False


def test_paths_resolve_relative_to_repo_root(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "CACHE_DIR=var/cache\nCACHE_SAMPLES_DIR=fixtures\nOUTPUT_DIR=artifacts/output\nRUNS_DIR=artifacts/runs\n",
        encoding="utf-8",
    )

    settings = load_settings(repo_root=tmp_path, env_file=env_file)

    assert settings.cache_dir == tmp_path / "var" / "cache"
    assert settings.cache_samples_dir == tmp_path / "fixtures"
    assert settings.output_dir == tmp_path / "artifacts" / "output"
    assert settings.runs_dir == tmp_path / "artifacts" / "runs"


def test_invalid_boolean_rejected(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("USE_CACHE=maybe\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_settings(repo_root=tmp_path, env_file=env_file)


def test_process_environment_overrides_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    env_file = tmp_path / ".env"
    env_file.write_text("WAR_ROOM_ENV=local\nALLOW_LIVE_RETRIEVAL=true\nEXA_API_KEY=file-key\n", encoding="utf-8")

    monkeypatch.setenv("WAR_ROOM_ENV", "demo")
    monkeypatch.setenv("ALLOW_LIVE_RETRIEVAL", "false")
    monkeypatch.setenv("EXA_API_KEY", "")

    settings = load_settings(repo_root=tmp_path, env_file=env_file)

    assert settings.app_env == RuntimeEnvironment.DEMO
    assert settings.live_retrieval_enabled is False
    assert settings.exa_api_key_value == ""
