"""Offline dependency hygiene checks for CI quality gates."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tomllib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from war_room.bootstrap import discover_repo_root

SCHEMA_VERSION = "dependency-hygiene.v1"

REQUIREMENTS_PATH = "requirements.txt"
PYPROJECT_PATH = "pyproject.toml"
SUPPORTED_DEPENDENCY_FILES = {REQUIREMENTS_PATH, PYPROJECT_PATH}
UNSUPPORTED_DEPENDENCY_FILENAMES = {
    "requirements-dev.in",
    "requirements-dev.txt",
    "requirements-test.in",
    "requirements-test.txt",
    "requirements.lock",
    "constraints.in",
    "constraints.txt",
    "pipfile",
    "pipfile.lock",
    "poetry.lock",
    "uv.lock",
    "pdm.lock",
    "setup.py",
    "setup.cfg",
    "environment.yml",
    "environment.yaml",
    "conda.yml",
    "conda.yaml",
}
DOCUMENTATION_EXPECTATIONS = {
    "README.md": ("dependency compatibility", "requirements.txt", "pin"),
    "CLAUDE.md": ("no new dependencies", "requirements.txt"),
}

PACKAGE_PATTERN = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9][A-Za-z0-9_.-]*)"
    r"(?P<extras>\[[^\]]+\])?"
    r"\s*(?P<specifier>===|==|~=|!=|<=|>=|<|>|=)?"
    r"(?P<rest>.*)$"
)


@dataclass(frozen=True)
class DependencyHygieneFinding:
    """One conservative dependency hygiene finding."""

    check_id: str
    severity: str
    path: str
    line: int | None
    message: str


@dataclass(frozen=True)
class DependencyHygieneCheck:
    """One named dependency hygiene check result."""

    check_id: str
    name: str
    passed: bool
    summary: str
    findings: list[DependencyHygieneFinding]


@dataclass(frozen=True)
class DependencyHygieneReport:
    """Machine-readable report for the dependency hygiene gate."""

    schema_version: str
    checked_at: str
    repo_root: str
    passed: bool
    checks: list[DependencyHygieneCheck]


@dataclass(frozen=True)
class _TrackedFile:
    path: str
    absolute_path: Path


@dataclass(frozen=True)
class _RequirementEntry:
    path: str
    line: int | None
    raw: str
    source_kind: str
    normalized_name: str | None
    canonical_requirement: str | None
    specifier: str | None
    specifier_value: str


def run_dependency_hygiene(
    repo_root: Path | None = None,
    *,
    tracked_files: Sequence[str | Path] | None = None,
) -> DependencyHygieneReport:
    """Run deterministic dependency hygiene checks."""

    resolved_root = (repo_root or discover_repo_root()).resolve()
    tracked = _resolve_tracked_files(resolved_root, tracked_files=tracked_files)
    requirements_entries = _read_requirements_entries(resolved_root / REQUIREMENTS_PATH)
    pyproject_entries, pyproject_findings = _read_pyproject_dependency_entries(resolved_root / PYPROJECT_PATH)
    checks = [
        _check_requirements_pinned(resolved_root, requirements_entries),
        _check_unsupported_requirement_sources(requirements_entries),
        _check_duplicate_dependencies(requirements_entries + pyproject_entries),
        _check_pyproject_dependency_drift(
            resolved_root,
            requirements_entries=requirements_entries,
            pyproject_entries=pyproject_entries,
            pyproject_findings=pyproject_findings,
        ),
        _check_unsupported_dependency_files(tracked),
        _check_documented_dependency_policy(resolved_root),
    ]
    return DependencyHygieneReport(
        schema_version=SCHEMA_VERSION,
        checked_at=datetime.now(UTC).isoformat(),
        repo_root=str(resolved_root),
        passed=all(check.passed for check in checks),
        checks=checks,
    )


def render_dependency_hygiene_report(report: DependencyHygieneReport) -> str:
    """Render a concise human-readable dependency hygiene report."""

    passed = sum(1 for check in report.checks if check.passed)
    lines = [
        "# Dependency Hygiene Check",
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
        "Dependency hygiene check "
        f"{'passed' if report.passed else 'failed'}: {passed}/{len(report.checks)} checks passed"
    )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for the offline dependency hygiene check."""

    parser = argparse.ArgumentParser(description="Run offline dependency hygiene checks")
    parser.add_argument("--repo-root", type=Path, help="Repository root to inspect. Defaults to discovery from cwd.")
    parser.add_argument("--check", action="store_true", help="Run the check and fail when findings are present.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    args = parser.parse_args(argv)

    report = run_dependency_hygiene(args.repo_root)
    if args.json:
        print(json.dumps(asdict(report), indent=2))
    else:
        print(render_dependency_hygiene_report(report), end="")
    return 0 if report.passed else 1


def _check_requirements_pinned(
    repo_root: Path,
    entries: Sequence[_RequirementEntry],
) -> DependencyHygieneCheck:
    findings: list[DependencyHygieneFinding] = []
    if not (repo_root / REQUIREMENTS_PATH).exists():
        findings.append(
            DependencyHygieneFinding(
                check_id="requirements-pinned",
                severity="high",
                path=REQUIREMENTS_PATH,
                line=None,
                message="requirements.txt is missing; keep one pinned dependency manifest for CI installs",
            )
        )
    for entry in entries:
        if entry.source_kind != "package":
            continue
        if not _is_exactly_pinned(entry):
            findings.append(
                DependencyHygieneFinding(
                    check_id="requirements-pinned",
                    severity="medium",
                    path=entry.path,
                    line=entry.line,
                    message="requirement must use an exact == version pin without wildcards or ranges",
                )
            )
    return _make_check(
        check_id="requirements-pinned",
        name="Pinned Requirements",
        findings=findings,
        passed_summary="requirements.txt exists and all package entries use exact == pins",
    )


def _check_unsupported_requirement_sources(
    entries: Sequence[_RequirementEntry],
) -> DependencyHygieneCheck:
    findings: list[DependencyHygieneFinding] = []
    messages = {
        "editable": "editable requirements are not supported in committed dependency manifests",
        "local-path": "local path requirements are not supported in committed dependency manifests",
        "direct-url": "direct URL or git requirements are not supported in committed dependency manifests",
        "requirements-option": "requirements indirection or installer options are not supported in committed manifests",
        "unknown": "requirement line is not a simple pinned package dependency",
    }
    for entry in entries:
        if entry.source_kind == "package":
            continue
        findings.append(
            DependencyHygieneFinding(
                check_id="unsupported-requirement-sources",
                severity="high",
                path=entry.path,
                line=entry.line,
                message=messages.get(entry.source_kind, messages["unknown"]),
            )
        )
    return _make_check(
        check_id="unsupported-requirement-sources",
        name="Unsupported Requirement Sources",
        findings=findings,
        passed_summary="requirements.txt has no editable, local path, direct URL, git, include, or installer-option entries",
    )


def _check_duplicate_dependencies(
    entries: Sequence[_RequirementEntry],
) -> DependencyHygieneCheck:
    findings: list[DependencyHygieneFinding] = []
    by_file: dict[str, dict[str, list[_RequirementEntry]]] = {}
    for entry in entries:
        if not entry.normalized_name:
            continue
        by_file.setdefault(entry.path, {}).setdefault(entry.normalized_name, []).append(entry)

    for path, entries_by_name in sorted(by_file.items()):
        for dependency_name, duplicates in sorted(entries_by_name.items()):
            if len(duplicates) < 2:
                continue
            canonical_values = {entry.canonical_requirement for entry in duplicates}
            severity = "high" if len(canonical_values) > 1 else "medium"
            kind = "conflicting" if len(canonical_values) > 1 else "duplicate"
            for entry in duplicates:
                findings.append(
                    DependencyHygieneFinding(
                        check_id="duplicate-dependency-entries",
                        severity=severity,
                        path=path,
                        line=entry.line,
                        message=f"{kind} dependency entry for {dependency_name}",
                    )
                )
    return _make_check(
        check_id="duplicate-dependency-entries",
        name="Duplicate Dependency Entries",
        findings=findings,
        passed_summary="no duplicate or conflicting dependency entries found inside dependency files",
    )


def _check_pyproject_dependency_drift(
    repo_root: Path,
    *,
    requirements_entries: Sequence[_RequirementEntry],
    pyproject_entries: Sequence[_RequirementEntry],
    pyproject_findings: Sequence[DependencyHygieneFinding],
) -> DependencyHygieneCheck:
    findings = list(pyproject_findings)
    pyproject_path = repo_root / PYPROJECT_PATH
    if not pyproject_path.exists():
        return _make_check(
            check_id="pyproject-requirements-drift",
            name="Pyproject Requirements Drift",
            findings=findings,
            passed_summary="pyproject.toml is absent; requirements.txt remains the dependency manifest",
        )

    requirements_by_name = _unique_package_map(requirements_entries)
    pyproject_by_name = _unique_package_map(pyproject_entries)
    if not pyproject_entries and not pyproject_findings:
        findings.append(
            DependencyHygieneFinding(
                check_id="pyproject-requirements-drift",
                severity="medium",
                path=PYPROJECT_PATH,
                line=None,
                message="[project].dependencies must mirror requirements.txt",
            )
        )

    for name in sorted(requirements_by_name.keys() - pyproject_by_name.keys()):
        findings.append(
            DependencyHygieneFinding(
                check_id="pyproject-requirements-drift",
                severity="medium",
                path=PYPROJECT_PATH,
                line=None,
                message=f"missing dependency from pyproject.toml: {name}",
            )
        )
    for name in sorted(pyproject_by_name.keys() - requirements_by_name.keys()):
        entry = pyproject_by_name[name]
        findings.append(
            DependencyHygieneFinding(
                check_id="pyproject-requirements-drift",
                severity="medium",
                path=entry.path,
                line=entry.line,
                message=f"dependency is present in pyproject.toml but not requirements.txt: {name}",
            )
        )
    for name in sorted(requirements_by_name.keys() & pyproject_by_name.keys()):
        requirements_entry = requirements_by_name[name]
        pyproject_entry = pyproject_by_name[name]
        if requirements_entry.canonical_requirement != pyproject_entry.canonical_requirement:
            findings.append(
                DependencyHygieneFinding(
                    check_id="pyproject-requirements-drift",
                    severity="high",
                    path=pyproject_entry.path,
                    line=pyproject_entry.line,
                    message=(
                        f"dependency pin for {name} differs from requirements.txt "
                        f"({requirements_entry.raw!r} != {pyproject_entry.raw!r})"
                    ),
                )
            )
    return _make_check(
        check_id="pyproject-requirements-drift",
        name="Pyproject Requirements Drift",
        findings=findings,
        passed_summary="pyproject.toml project dependencies mirror requirements.txt pins",
    )


def _check_unsupported_dependency_files(
    tracked: Sequence[_TrackedFile],
) -> DependencyHygieneCheck:
    findings: list[DependencyHygieneFinding] = []
    for tracked_file in tracked:
        normalized_path = tracked_file.path.lower()
        name = Path(normalized_path).name
        is_extra_requirements_file = (
            name.startswith("requirements")
            and normalized_path not in SUPPORTED_DEPENDENCY_FILES
            and Path(name).suffix in {".in", ".txt", ".lock"}
        )
        if name not in UNSUPPORTED_DEPENDENCY_FILENAMES and not is_extra_requirements_file:
            continue
        findings.append(
            DependencyHygieneFinding(
                check_id="unsupported-dependency-files",
                severity="medium",
                path=tracked_file.path,
                line=None,
                message="dependency declarations must stay in requirements.txt and pyproject.toml to avoid drift",
            )
        )
    return _make_check(
        check_id="unsupported-dependency-files",
        name="Unsupported Dependency Files",
        findings=findings,
        passed_summary="no unsupported dependency manifests or lockfiles are committed",
    )


def _check_documented_dependency_policy(repo_root: Path) -> DependencyHygieneCheck:
    findings: list[DependencyHygieneFinding] = []
    for relative_path, phrases in DOCUMENTATION_EXPECTATIONS.items():
        path = repo_root / relative_path
        if not path.exists():
            findings.append(
                DependencyHygieneFinding(
                    check_id="documented-dependency-policy",
                    severity="medium",
                    path=relative_path,
                    line=None,
                    message="dependency policy document is missing",
                )
            )
            continue
        normalized = _normalize_policy_text(path.read_text(encoding="utf-8"))
        for phrase in phrases:
            if phrase not in normalized:
                findings.append(
                    DependencyHygieneFinding(
                        check_id="documented-dependency-policy",
                        severity="medium",
                        path=relative_path,
                        line=None,
                        message=f"documented dependency policy no longer mentions {phrase!r}",
                    )
                )
    return _make_check(
        check_id="documented-dependency-policy",
        name="Documented Dependency Policy",
        findings=findings,
        passed_summary="dependency pinning and no-new-dependency policy remain documented",
    )


def _read_requirements_entries(path: Path) -> list[_RequirementEntry]:
    if not path.exists():
        return []
    entries: list[_RequirementEntry] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = _strip_inline_comment(line)
        if not stripped:
            continue
        entries.append(_parse_requirement_entry(REQUIREMENTS_PATH, line_number, stripped))
    return entries


def _read_pyproject_dependency_entries(path: Path) -> tuple[list[_RequirementEntry], list[DependencyHygieneFinding]]:
    if not path.exists():
        return [], []
    text = path.read_text(encoding="utf-8")
    try:
        payload = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        return [], [
            DependencyHygieneFinding(
                check_id="pyproject-requirements-drift",
                severity="high",
                path=PYPROJECT_PATH,
                line=getattr(exc, "lineno", None),
                message=f"pyproject.toml could not be parsed: {getattr(exc, 'msg', str(exc))}",
            )
        ]

    dependencies = payload.get("project", {}).get("dependencies", [])
    if not isinstance(dependencies, list):
        return [], [
            DependencyHygieneFinding(
                check_id="pyproject-requirements-drift",
                severity="medium",
                path=PYPROJECT_PATH,
                line=None,
                message="[project].dependencies must be a list of pinned dependency strings",
            )
        ]

    entries: list[_RequirementEntry] = []
    findings: list[DependencyHygieneFinding] = []
    for dependency in dependencies:
        if not isinstance(dependency, str):
            findings.append(
                DependencyHygieneFinding(
                    check_id="pyproject-requirements-drift",
                    severity="medium",
                    path=PYPROJECT_PATH,
                    line=None,
                    message="[project].dependencies contains a non-string dependency entry",
                )
            )
            continue
        entries.append(
            _parse_requirement_entry(
                PYPROJECT_PATH,
                _dependency_line_number(text, dependency),
                dependency.strip(),
            )
        )
    return entries, findings


def _parse_requirement_entry(path: str, line: int | None, raw: str) -> _RequirementEntry:
    source_kind = _requirement_source_kind(raw)
    match = PACKAGE_PATTERN.match(raw)
    normalized_name: str | None = None
    canonical_requirement: str | None = None
    specifier: str | None = None
    specifier_value = ""
    if match and not raw.lstrip().startswith("-") and source_kind != "local-path":
        normalized_name = _normalize_dependency_name(match.group("name"))
        specifier = match.group("specifier")
        specifier_value = _specifier_value(match.group("rest")) if specifier else ""
        canonical_requirement = _canonical_requirement_text(raw, match)
    elif source_kind == "package":
        source_kind = "unknown"
    return _RequirementEntry(
        path=path,
        line=line,
        raw=raw,
        source_kind=source_kind,
        normalized_name=normalized_name,
        canonical_requirement=canonical_requirement,
        specifier=specifier,
        specifier_value=specifier_value,
    )


def _requirement_source_kind(raw: str) -> str:
    lowered = raw.strip().lower()
    if lowered.startswith(("-e ", "--editable ")):
        return "editable"
    if lowered.startswith(("-r ", "--requirement ", "-c ", "--constraint ")):
        return "requirements-option"
    if lowered.startswith(("--index-url", "--extra-index-url", "--find-links", "-f ")):
        return "requirements-option"
    if "git+" in lowered or lowered.startswith(("http://", "https://")):
        return "direct-url"
    if re.search(r"\s@\s*(?:git\+|https?://|file:)", lowered):
        return "direct-url"
    if lowered.startswith("file:") or re.match(r"^(?:\.\.?[/\\]|[/\\]|~[/\\]|[a-z]:[/\\])", lowered):
        return "local-path"
    return "package"


def _is_exactly_pinned(entry: _RequirementEntry) -> bool:
    if entry.specifier != "==":
        return False
    value = entry.specifier_value
    return bool(value) and "," not in value and "*" not in value and not value.startswith("=")


def _specifier_value(rest: str) -> str:
    value = rest.split(";", 1)[0].strip()
    return re.sub(r"\s+", "", value)


def _canonical_requirement_text(raw: str, match: re.Match[str]) -> str:
    name = _normalize_dependency_name(match.group("name"))
    suffix = raw[match.end("name") :].strip().lower()
    suffix = re.sub(r"\s+", "", suffix)
    return f"{name}{suffix}"


def _unique_package_map(entries: Sequence[_RequirementEntry]) -> dict[str, _RequirementEntry]:
    packages: dict[str, _RequirementEntry] = {}
    for entry in entries:
        if entry.source_kind != "package" or not entry.normalized_name:
            continue
        packages.setdefault(entry.normalized_name, entry)
    return packages


def _strip_inline_comment(line: str) -> str:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return ""
    for index, char in enumerate(line):
        if char == "#" and (index == 0 or line[index - 1].isspace()):
            return line[:index].strip()
    return stripped


def _dependency_line_number(text: str, dependency: str) -> int | None:
    needle = dependency.strip()
    for line_number, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return line_number
    return None


def _normalize_dependency_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _normalize_policy_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("`", "")).strip()


def _make_check(
    *,
    check_id: str,
    name: str,
    findings: list[DependencyHygieneFinding],
    passed_summary: str,
) -> DependencyHygieneCheck:
    if findings:
        return DependencyHygieneCheck(
            check_id=check_id,
            name=name,
            passed=False,
            summary=f"{len(findings)} finding(s)",
            findings=findings,
        )
    return DependencyHygieneCheck(
        check_id=check_id,
        name=name,
        passed=True,
        summary=passed_summary,
        findings=[],
    )


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
