"""Tests for the offline security hygiene gate."""

from __future__ import annotations

from pathlib import Path

from war_room.security_hygiene import (
    EXPECTED_ENV_EXAMPLE_KEYS,
    run_security_hygiene,
)


def test_security_hygiene_passes_for_current_repo():
    report = run_security_hygiene(Path(__file__).resolve().parent.parent)

    assert report.passed
    assert {check.check_id for check in report.checks} == {
        "committed-env-files",
        "obvious-secret-patterns",
        "env-example-expectations",
        "gitignore-secrets-policy",
        "runtime-artifact-commits",
        "documented-secrets-policy",
    }


def test_security_hygiene_accepts_minimal_compliant_repo(tmp_path: Path):
    tracked_files = _write_compliant_repo(tmp_path)

    report = run_security_hygiene(tmp_path, tracked_files=tracked_files)

    assert report.passed
    assert all(not check.findings for check in report.checks)


def test_security_hygiene_flags_committed_env_and_runtime_artifacts(tmp_path: Path):
    tracked_files = _write_compliant_repo(tmp_path)
    exa_key = "EXA_API" + "_KEY"
    _write(tmp_path / ".env", f"{exa_key}=\n")
    _write(tmp_path / "cache" / "weather.json", "{}\n")
    tracked_files.extend([".env", "cache/weather.json"])

    report = run_security_hygiene(tmp_path, tracked_files=tracked_files)

    assert not report.passed
    assert _check(report, "committed-env-files").findings[0].path == ".env"
    assert _check(report, "runtime-artifact-commits").findings[0].path == "cache/weather.json"


def test_security_hygiene_flags_non_placeholder_secret_assignment(tmp_path: Path):
    tracked_files = _write_compliant_repo(tmp_path)
    secret_name = "EXA_API" + "_KEY"
    secret_value = "locally_generated_private_value_123456"
    _write(tmp_path / "src" / "settings.py", f"{secret_name} = {secret_value!r}\n")
    tracked_files.append("src/settings.py")

    report = run_security_hygiene(tmp_path, tracked_files=tracked_files)

    assert not report.passed
    findings = _check(report, "obvious-secret-patterns").findings
    assert len(findings) == 1
    assert findings[0].path == "src/settings.py"
    assert findings[0].line == 1


def test_security_hygiene_flags_env_template_drift(tmp_path: Path):
    tracked_files = _write_compliant_repo(tmp_path)
    exa_key = "EXA_API" + "_KEY"
    _write(tmp_path / ".env.example", f"{exa_key}=\nUSE_CACHE=true\n")

    report = run_security_hygiene(tmp_path, tracked_files=tracked_files)

    assert not report.passed
    messages = [finding.message for finding in _check(report, "env-example-expectations").findings]
    assert "missing expected setting WAR_ROOM_ENV" in messages
    assert "missing expected setting RUNS_DIR" in messages


def _write_compliant_repo(root: Path) -> list[str]:
    _write(root / ".env.example", "\n".join(f"{key}=" for key in EXPECTED_ENV_EXAMPLE_KEYS))
    _write(root / ".gitignore", "\n".join([".env", "cache/", "output/", "runs/", ".exa_cache_live/"]))
    _write(
        root / "CLAUDE.md",
        "No secrets in code. `.env` is gitignored. Use `.env.example` for the template.\n",
    )
    _write(
        root / "docs" / "SAFETY_GUARDRAILS.md",
        "`.env` files with API keys are gitignored. Cache files may contain search results. "
        "`cache_samples/` contains only public demo data.\n",
    )
    _write(root / "src" / "app.py", "print('ok')\n")
    return [
        ".env.example",
        ".gitignore",
        "CLAUDE.md",
        "docs/SAFETY_GUARDRAILS.md",
        "src/app.py",
    ]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _check(report, check_id: str):
    return next(check for check in report.checks if check.check_id == check_id)
