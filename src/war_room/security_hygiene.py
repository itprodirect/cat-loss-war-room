"""Offline repository security hygiene checks for CI quality gates."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from war_room.bootstrap import discover_repo_root

SCHEMA_VERSION = "security-hygiene.v1"

EXPECTED_ENV_EXAMPLE_KEYS = (
    "WAR_ROOM_ENV",
    "EXA_API_KEY",
    "USE_CACHE",
    "ALLOW_LIVE_RETRIEVAL",
    "CACHE_DIR",
    "CACHE_SAMPLES_DIR",
    "OUTPUT_DIR",
    "RUNS_DIR",
    "SCHEMA_VERSION",
)
GITIGNORE_EXPECTATIONS = (
    ".env",
    "cache/",
    "output/",
    "runs/",
    ".exa_cache_live/",
)
RUNTIME_ARTIFACT_ROOTS = ("cache", "output", "runs", ".exa_cache_live")
SECRET_ASSIGNMENT_NAMES = (
    "EXA_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
)
ALLOWLIST_MARKERS = (
    "security-hygiene: allow",
    "pragma: allowlist secret",
)
MAX_SCAN_BYTES = 512_000

SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"\b(?P<name>"
    + "|".join(re.escape(name) for name in SECRET_ASSIGNMENT_NAMES)
    + r")\b\s*(?P<sep>[:=])\s*(?P<quote>['\"]?)(?P<value>[^'\"\s#,}]+)",
    re.IGNORECASE,
)
RAW_SECRET_PATTERNS = (
    ("openai-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
)


@dataclass(frozen=True)
class SecurityHygieneFinding:
    """One conservative repository security hygiene finding."""

    check_id: str
    severity: str
    path: str
    line: int | None
    message: str


@dataclass(frozen=True)
class SecurityHygieneCheck:
    """One named security hygiene check result."""

    check_id: str
    name: str
    passed: bool
    summary: str
    findings: list[SecurityHygieneFinding]


@dataclass(frozen=True)
class SecurityHygieneReport:
    """Machine-readable report for the security hygiene gate."""

    schema_version: str
    checked_at: str
    repo_root: str
    passed: bool
    checks: list[SecurityHygieneCheck]


@dataclass(frozen=True)
class _TrackedFile:
    path: str
    absolute_path: Path


def run_security_hygiene(
    repo_root: Path | None = None,
    *,
    tracked_files: Sequence[str | Path] | None = None,
) -> SecurityHygieneReport:
    """Run deterministic repository security hygiene checks."""

    resolved_root = (repo_root or discover_repo_root()).resolve()
    tracked = _resolve_tracked_files(resolved_root, tracked_files=tracked_files)
    checks = [
        _check_committed_env_files(tracked),
        _check_secret_patterns(tracked),
        _check_env_example(resolved_root, tracked),
        _check_gitignore_policy(resolved_root),
        _check_runtime_artifact_commits(tracked),
        _check_documented_policy(resolved_root),
    ]
    return SecurityHygieneReport(
        schema_version=SCHEMA_VERSION,
        checked_at=datetime.now(UTC).isoformat(),
        repo_root=str(resolved_root),
        passed=all(check.passed for check in checks),
        checks=checks,
    )


def render_security_hygiene_report(report: SecurityHygieneReport) -> str:
    """Render a concise human-readable security hygiene report."""

    passed = sum(1 for check in report.checks if check.passed)
    lines = [
        "# Security Hygiene Check",
        "",
        f"- Status: {'passed' if report.passed else 'failed'}",
        f"- Checks passed: {passed}/{len(report.checks)}",
        f"- Repository: `{report.repo_root}`",
        "",
    ]
    for check in report.checks:
        status = "passed" if check.passed else "failed"
        lines.extend(
            [
                f"## {check.name}",
                "",
                f"- Check id: `{check.check_id}`",
                f"- Status: `{status}`",
                f"- Summary: {check.summary}",
            ]
        )
        for finding in check.findings:
            location = finding.path
            if finding.line is not None:
                location = f"{location}:{finding.line}"
            lines.append(f"- {finding.severity}: `{location}` - {finding.message}")
        lines.append("")
    lines.append(
        "Security hygiene check "
        f"{'passed' if report.passed else 'failed'}: {passed}/{len(report.checks)} checks passed"
    )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for the offline security hygiene check."""

    parser = argparse.ArgumentParser(description="Run offline repository security hygiene checks")
    parser.add_argument("--repo-root", type=Path, help="Repository root to inspect. Defaults to discovery from cwd.")
    parser.add_argument("--check", action="store_true", help="Run the check and fail when findings are present.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    args = parser.parse_args(argv)

    report = run_security_hygiene(args.repo_root)
    if args.json:
        print(json.dumps(asdict(report), indent=2))
    else:
        print(render_security_hygiene_report(report), end="")
    return 0 if report.passed else 1


def _resolve_tracked_files(
    repo_root: Path,
    *,
    tracked_files: Sequence[str | Path] | None,
) -> list[_TrackedFile]:
    if tracked_files is None:
        tracked_files = _git_tracked_files(repo_root)

    resolved: list[_TrackedFile] = []
    for item in tracked_files:
        candidate = Path(str(item))
        if candidate.is_absolute():
            absolute_path = candidate.resolve()
            if not _is_within_repo(repo_root, absolute_path):
                continue
            relative = absolute_path.relative_to(repo_root).as_posix()
        else:
            relative = _normalize_relative_path(item)
            absolute_path = (repo_root / relative).resolve()
        if not relative:
            continue
        if _is_within_repo(repo_root, absolute_path):
            resolved.append(_TrackedFile(path=relative, absolute_path=absolute_path))
    return resolved


def _git_tracked_files(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={repo_root}", "ls-files"],
        cwd=repo_root,
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode:
        return _filesystem_files(repo_root)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _filesystem_files(repo_root: Path) -> list[str]:
    paths: list[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        paths.append(path.relative_to(repo_root).as_posix())
    return sorted(paths)


def _check_committed_env_files(tracked: Sequence[_TrackedFile]) -> SecurityHygieneCheck:
    findings: list[SecurityHygieneFinding] = []
    for tracked_file in tracked:
        name = Path(tracked_file.path).name
        if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
            findings.append(
                SecurityHygieneFinding(
                    check_id="committed-env-files",
                    severity="high",
                    path=tracked_file.path,
                    line=None,
                    message="tracked environment files must stay out of the repository; keep .env.example only",
                )
            )
    return _make_check(
        check_id="committed-env-files",
        name="Committed .env Files",
        findings=findings,
        passed_summary="no tracked .env files found",
    )


def _check_secret_patterns(tracked: Sequence[_TrackedFile]) -> SecurityHygieneCheck:
    findings: list[SecurityHygieneFinding] = []
    for tracked_file in tracked:
        text = _read_scannable_text(tracked_file.absolute_path)
        if text is None:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if _line_has_allowlist_marker(line):
                continue
            for match in SECRET_ASSIGNMENT_PATTERN.finditer(line):
                if _looks_like_python_type_annotation(tracked_file.path, line, match):
                    continue
                if _looks_like_not_set_status(line, match):
                    continue
                value = match.group("value").strip().strip("'\"")
                if _is_placeholder_secret_value(value):
                    continue
                findings.append(
                    SecurityHygieneFinding(
                        check_id="obvious-secret-patterns",
                        severity="high",
                        path=tracked_file.path,
                        line=line_number,
                        message=f"{match.group('name')} appears to have a committed non-placeholder value",
                    )
                )
            for pattern_name, pattern in RAW_SECRET_PATTERNS:
                if not pattern.search(line):
                    continue
                findings.append(
                    SecurityHygieneFinding(
                        check_id="obvious-secret-patterns",
                        severity="high",
                        path=tracked_file.path,
                        line=line_number,
                        message=f"line matches obvious {pattern_name} token shape",
                    )
                )
    return _make_check(
        check_id="obvious-secret-patterns",
        name="Obvious Secret Patterns",
        findings=findings,
        passed_summary="no obvious API key or token patterns found in tracked text files",
    )


def _check_env_example(repo_root: Path, tracked: Sequence[_TrackedFile]) -> SecurityHygieneCheck:
    tracked_paths = {tracked_file.path for tracked_file in tracked}
    env_example_path = repo_root / ".env.example"
    findings: list[SecurityHygieneFinding] = []
    if ".env.example" not in tracked_paths:
        findings.append(
            SecurityHygieneFinding(
                check_id="env-example-expectations",
                severity="medium",
                path=".env.example",
                line=None,
                message=".env.example must be committed as the secrets-safe runtime template",
            )
        )
    if not env_example_path.exists():
        findings.append(
            SecurityHygieneFinding(
                check_id="env-example-expectations",
                severity="medium",
                path=".env.example",
                line=None,
                message=".env.example is missing",
            )
        )
        return _make_check(
            check_id="env-example-expectations",
            name=".env.example Expectations",
            findings=findings,
            passed_summary=".env.example includes expected offline-demo settings",
        )

    env_keys = _parse_env_keys(env_example_path.read_text(encoding="utf-8"))
    missing = [key for key in EXPECTED_ENV_EXAMPLE_KEYS if key not in env_keys]
    for key in missing:
        findings.append(
            SecurityHygieneFinding(
                check_id="env-example-expectations",
                severity="medium",
                path=".env.example",
                line=None,
                message=f"missing expected setting {key}",
            )
        )
    return _make_check(
        check_id="env-example-expectations",
        name=".env.example Expectations",
        findings=findings,
        passed_summary=".env.example is committed and includes expected offline-demo settings",
    )


def _check_gitignore_policy(repo_root: Path) -> SecurityHygieneCheck:
    gitignore_path = repo_root / ".gitignore"
    findings: list[SecurityHygieneFinding] = []
    if not gitignore_path.exists():
        findings.append(
            SecurityHygieneFinding(
                check_id="gitignore-secrets-policy",
                severity="medium",
                path=".gitignore",
                line=None,
                message=".gitignore is missing",
            )
        )
        return _make_check(
            check_id="gitignore-secrets-policy",
            name=".gitignore Secrets Policy",
            findings=findings,
            passed_summary=".gitignore covers secrets and runtime artifacts",
        )

    entries = _parse_gitignore_entries(gitignore_path.read_text(encoding="utf-8"))
    missing = [entry for entry in GITIGNORE_EXPECTATIONS if entry not in entries]
    for entry in missing:
        findings.append(
            SecurityHygieneFinding(
                check_id="gitignore-secrets-policy",
                severity="medium",
                path=".gitignore",
                line=None,
                message=f"missing ignore rule {entry}",
            )
        )
    return _make_check(
        check_id="gitignore-secrets-policy",
        name=".gitignore Secrets Policy",
        findings=findings,
        passed_summary=".gitignore covers secrets and runtime artifacts",
    )


def _check_runtime_artifact_commits(tracked: Sequence[_TrackedFile]) -> SecurityHygieneCheck:
    findings: list[SecurityHygieneFinding] = []
    for tracked_file in tracked:
        root = tracked_file.path.split("/", 1)[0]
        if root not in RUNTIME_ARTIFACT_ROOTS:
            continue
        findings.append(
            SecurityHygieneFinding(
                check_id="runtime-artifact-commits",
                severity="medium",
                path=tracked_file.path,
                line=None,
                message="runtime cache/output artifacts must stay out of source control",
            )
        )
    return _make_check(
        check_id="runtime-artifact-commits",
        name="Runtime Artifact Commits",
        findings=findings,
        passed_summary="no tracked cache, output, runs, or live retrieval artifacts found",
    )


def _check_documented_policy(repo_root: Path) -> SecurityHygieneCheck:
    expectations = {
        "CLAUDE.md": ("no secrets in code", ".env is gitignored", ".env.example"),
        "docs/SAFETY_GUARDRAILS.md": (".env files with api keys are gitignored", "cache files", "cache_samples"),
    }
    findings: list[SecurityHygieneFinding] = []
    for relative_path, phrases in expectations.items():
        path = repo_root / relative_path
        if not path.exists():
            findings.append(
                SecurityHygieneFinding(
                    check_id="documented-secrets-policy",
                    severity="medium",
                    path=relative_path,
                    line=None,
                    message="secrets and cache policy document is missing",
                )
            )
            continue
        normalized = _normalize_policy_text(path.read_text(encoding="utf-8"))
        for phrase in phrases:
            if phrase not in normalized:
                findings.append(
                    SecurityHygieneFinding(
                        check_id="documented-secrets-policy",
                        severity="medium",
                        path=relative_path,
                        line=None,
                        message=f"documented policy no longer mentions {phrase!r}",
                    )
                )
    return _make_check(
        check_id="documented-secrets-policy",
        name="Documented Secrets Policy",
        findings=findings,
        passed_summary="secrets, .env, and cache handling remain documented",
    )


def _make_check(
    *,
    check_id: str,
    name: str,
    findings: list[SecurityHygieneFinding],
    passed_summary: str,
) -> SecurityHygieneCheck:
    if findings:
        return SecurityHygieneCheck(
            check_id=check_id,
            name=name,
            passed=False,
            summary=f"{len(findings)} finding(s)",
            findings=findings,
        )
    return SecurityHygieneCheck(
        check_id=check_id,
        name=name,
        passed=True,
        summary=passed_summary,
        findings=[],
    )


def _read_scannable_text(path: Path) -> str | None:
    if not path.exists() or path.stat().st_size > MAX_SCAN_BYTES:
        return None
    data = path.read_bytes()
    if b"\x00" in data[:2048]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _parse_env_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if key:
            keys.add(key)
    return keys


def _parse_gitignore_entries(text: str) -> set[str]:
    return {
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def _is_placeholder_secret_value(value: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if not normalized:
        return True
    placeholder_tokens = (
        "your",
        "example",
        "placeholder",
        "dummy",
        "test",
        "changeme",
        "change_me",
        "replace",
        "redacted",
        "none",
        "null",
        "todo",
    )
    if normalized in {"true", "false", "0", "1", "xxx", "xxxx"}:
        return True
    return any(token in normalized for token in placeholder_tokens)


def _line_has_allowlist_marker(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in ALLOWLIST_MARKERS)


def _looks_like_python_type_annotation(path: str, line: str, match: re.Match[str]) -> bool:
    if match.group("sep") != ":":
        return False
    if Path(path).suffix != ".py":
        return False
    return bool(re.match(r"\s*[A-Za-z_][A-Za-z0-9_\[\],| .]*\s*=", line[match.start("value") :]))


def _looks_like_not_set_status(line: str, match: re.Match[str]) -> bool:
    suffix = line[match.start("value") :].strip().strip("'\"")
    return bool(re.match(r"not\s+set\b", suffix, flags=re.IGNORECASE))


def _normalize_policy_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("`", "")).strip()


def _normalize_relative_path(path: str | Path) -> str:
    raw = str(path).replace("\\", "/").strip()
    if not raw:
        return ""
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate.resolve().as_posix()
    return raw[2:] if raw.startswith("./") else raw


def _is_within_repo(repo_root: Path, path: Path) -> bool:
    try:
        path.relative_to(repo_root)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
