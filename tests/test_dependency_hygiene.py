"""Tests for the offline dependency hygiene gate."""

from __future__ import annotations

from pathlib import Path

from war_room.dependency_hygiene import run_dependency_hygiene

ROOT = Path(__file__).resolve().parent.parent
DEPENDENCIES = (
    "python-dotenv==1.0.1",
    "nbformat==5.10.4",
    "exa-py==2.0.2",
    "pytest==8.3.4",
    "pydantic==2.11.7",
)


def test_dependency_hygiene_passes_for_current_repo():
    report = run_dependency_hygiene(ROOT)

    assert report.passed
    assert {check.check_id for check in report.checks} == {
        "requirements-pinned",
        "unsupported-requirement-sources",
        "duplicate-dependency-entries",
        "pyproject-requirements-drift",
        "unsupported-dependency-files",
        "documented-dependency-policy",
    }


def test_dependency_hygiene_accepts_minimal_compliant_repo(tmp_path: Path):
    tracked_files = _write_compliant_repo(tmp_path)

    report = run_dependency_hygiene(tmp_path, tracked_files=tracked_files)

    assert report.passed
    assert all(not check.findings for check in report.checks)


def test_dependency_hygiene_flags_unpinned_and_unsupported_requirement_sources(tmp_path: Path):
    tracked_files = _write_compliant_repo(tmp_path)
    _write(
        tmp_path / "requirements.txt",
        "\n".join(
            [
                "python-dotenv>=1.0",
                "-e ../local-package",
                "demo-package @ git+https://example.invalid/demo-package.git",
            ]
        ),
    )

    report = run_dependency_hygiene(tmp_path, tracked_files=tracked_files)

    assert not report.passed
    pinned_findings = _check(report, "requirements-pinned").findings
    source_findings = _check(report, "unsupported-requirement-sources").findings
    assert pinned_findings[0].path == "requirements.txt"
    assert {finding.line for finding in source_findings} == {2, 3}


def test_dependency_hygiene_flags_duplicate_entries_and_pyproject_drift(tmp_path: Path):
    tracked_files = _write_compliant_repo(tmp_path)
    _write(
        tmp_path / "requirements.txt",
        "\n".join(
            [
                "python-dotenv==1.0.1",
                "exa-py==2.0.2",
                "exa_py==1.0.0",
            ]
        ),
    )
    _write(
        tmp_path / "pyproject.toml",
        _pyproject_dependencies(
            [
                "python-dotenv==1.0.1",
                "exa-py==2.0.2",
                "pydantic==2.11.7",
            ]
        ),
    )

    report = run_dependency_hygiene(tmp_path, tracked_files=tracked_files)

    assert not report.passed
    duplicate_messages = [finding.message for finding in _check(report, "duplicate-dependency-entries").findings]
    drift_messages = [finding.message for finding in _check(report, "pyproject-requirements-drift").findings]
    assert any("conflicting dependency entry for exa-py" in message for message in duplicate_messages)
    assert any("dependency is present in pyproject.toml but not requirements.txt: pydantic" in message for message in drift_messages)


def test_dependency_hygiene_flags_unsupported_dependency_file_and_doc_drift(tmp_path: Path):
    tracked_files = _write_compliant_repo(tmp_path)
    _write(tmp_path / "requirements-dev.txt", "pytest==8.3.4\n")
    _write(tmp_path / "README.md", "Quickstart only.\n")
    tracked_files.append("requirements-dev.txt")

    report = run_dependency_hygiene(tmp_path, tracked_files=tracked_files)

    assert not report.passed
    assert _check(report, "unsupported-dependency-files").findings[0].path == "requirements-dev.txt"
    doc_findings = _check(report, "documented-dependency-policy").findings
    assert any(finding.path == "README.md" for finding in doc_findings)


def test_dependency_hygiene_flags_nested_pyproject_manifest(tmp_path: Path):
    tracked_files = _write_compliant_repo(tmp_path)
    _write(tmp_path / "packages" / "demo" / "pyproject.toml", _pyproject_dependencies(["pytest==8.3.4"]))
    tracked_files.append("packages/demo/pyproject.toml")

    report = run_dependency_hygiene(tmp_path, tracked_files=tracked_files)

    assert not report.passed
    findings = _check(report, "unsupported-dependency-files").findings
    assert [finding.path for finding in findings] == ["packages/demo/pyproject.toml"]


def test_dependency_hygiene_flags_nested_requirements_manifest(tmp_path: Path):
    tracked_files = _write_compliant_repo(tmp_path)
    _write(tmp_path / "apps" / "demo" / "requirements.txt", "pytest==8.3.4\n")
    tracked_files.append("apps/demo/requirements.txt")

    report = run_dependency_hygiene(tmp_path, tracked_files=tracked_files)

    assert not report.passed
    findings = _check(report, "unsupported-dependency-files").findings
    assert [finding.path for finding in findings] == ["apps/demo/requirements.txt"]


def _write_compliant_repo(root: Path) -> list[str]:
    _write(root / "requirements.txt", "\n".join(DEPENDENCIES) + "\n")
    _write(root / "pyproject.toml", _pyproject_dependencies(DEPENDENCIES))
    _write(
        root / "README.md",
        "## Dependency Compatibility\n"
        "The repo pins dependencies in requirements.txt for reproducible installs.\n",
    )
    _write(
        root / "CLAUDE.md",
        "No new dependencies without explicit approval. "
        "Never install packages not in requirements.txt without asking.\n",
    )
    return ["requirements.txt", "pyproject.toml", "README.md", "CLAUDE.md"]


def _pyproject_dependencies(dependencies) -> str:
    dependency_lines = "\n".join(f'    "{dependency}",' for dependency in dependencies)
    return (
        "[project]\n"
        'name = "dependency-fixture"\n'
        'version = "0.1.0"\n'
        "dependencies = [\n"
        f"{dependency_lines}\n"
        "]\n"
    )


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _check(report, check_id: str):
    return next(check for check in report.checks if check.check_id == check_id)
