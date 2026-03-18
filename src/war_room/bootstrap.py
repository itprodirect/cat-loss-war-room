"""Project bootstrap helpers for scripts, notebooks, and tests."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from war_room.settings import WarRoomSettings, load_settings


@dataclass(frozen=True)
class BootstrapContext:
    """Resolved bootstrap context for the current repo checkout."""

    repo_root: Path
    settings: WarRoomSettings


def discover_repo_root(start_path: Path | None = None) -> Path:
    """Find the repo root by walking upward until pyproject.toml is found."""
    current = (start_path or Path.cwd()).resolve()

    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate

    raise FileNotFoundError("Could not locate repo root from current path")


def bootstrap_runtime(
    *,
    start_path: Path | None = None,
    env_file: Path | None = None,
    ensure_dirs: bool = True,
) -> BootstrapContext:
    """Resolve repo root, load settings, and optionally ensure runtime dirs exist."""
    repo_root = discover_repo_root(start_path)
    settings = load_settings(repo_root=repo_root, env_file=env_file)

    if ensure_dirs:
        for path in (settings.cache_dir, settings.cache_samples_dir, settings.output_dir, settings.runs_dir):
            path.mkdir(parents=True, exist_ok=True)

    return BootstrapContext(repo_root=repo_root, settings=settings)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for verifying bootstrap behavior or running demo preflight."""
    parser = argparse.ArgumentParser(description="Resolve CAT-Loss War Room runtime settings")
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Run the deterministic offline demo smoke instead of printing bootstrap settings",
    )
    parser.add_argument("--json", action="store_true", help="Print the resolved settings as JSON")
    args = parser.parse_args(argv)

    context = bootstrap_runtime()
    summary = context.settings.display_summary() | {"repo_root": str(context.repo_root)}

    if args.preflight:
        from war_room.preflight import render_demo_preflight_report, report_to_payload, run_demo_preflight

        report = run_demo_preflight(context)
        if args.json:
            print(json.dumps(report_to_payload(report), indent=2))
        else:
            print(render_demo_preflight_report(report), end="")
        return 0 if report.passed else 1

    if args.json:
        print(json.dumps(summary, indent=2))
        return 0

    print("CAT-Loss War Room Bootstrap")
    print("=" * 32)
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
