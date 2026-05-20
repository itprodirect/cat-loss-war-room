"""Typed runtime settings for the war room project."""

from __future__ import annotations

from enum import Enum
import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class RuntimeEnvironment(str, Enum):
    """Supported runtime lanes."""

    LOCAL = "local"
    DEMO = "demo"
    STAGING = "staging"
    PRODUCTION = "production"


class FeatureFlags(BaseModel):
    """Small set of explicit runtime feature flags."""

    model_config = ConfigDict(frozen=True)

    allow_live_retrieval: bool = True
    enable_notebook_surface: bool = True


class WarRoomSettings(BaseModel):
    """Resolved runtime settings derived from env plus repo defaults."""

    model_config = ConfigDict(frozen=True)

    app_env: RuntimeEnvironment = RuntimeEnvironment.LOCAL
    use_cache: bool = True
    schema_version: str = "v0-demo"
    exa_api_key: SecretStr | None = None
    cache_dir: Path
    cache_samples_dir: Path
    output_dir: Path
    runs_dir: Path
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("schema_version must be non-empty")
        return cleaned

    @property
    def offline_demo(self) -> bool:
        return self.app_env == RuntimeEnvironment.DEMO

    @property
    def live_retrieval_enabled(self) -> bool:
        return self.feature_flags.allow_live_retrieval and not self.offline_demo

    @property
    def exa_api_key_value(self) -> str:
        if self.exa_api_key is None:
            return ""
        return self.exa_api_key.get_secret_value()

    def display_summary(self) -> dict[str, Any]:
        """Return a safe, human-readable snapshot of the current runtime."""
        return {
            "app_env": self.app_env.value,
            "use_cache": self.use_cache,
            "schema_version": self.schema_version,
            "cache_dir": str(self.cache_dir),
            "cache_samples_dir": str(self.cache_samples_dir),
            "output_dir": str(self.output_dir),
            "runs_dir": str(self.runs_dir),
            "offline_demo": self.offline_demo,
            "live_retrieval_enabled": self.live_retrieval_enabled,
            "exa_api_key_set": bool(self.exa_api_key_value),
        }


def load_settings(*, repo_root: Path, env_file: Path | None = None) -> WarRoomSettings:
    """Load settings from `.env` plus process environment-style overrides."""
    values = _read_env_values(env_file or repo_root / ".env")
    app_env = RuntimeEnvironment(values.get("WAR_ROOM_ENV", RuntimeEnvironment.LOCAL.value).strip().lower())

    use_cache = _parse_bool(values.get("USE_CACHE"), default=True)
    if app_env == RuntimeEnvironment.DEMO:
        use_cache = True

    allow_live_retrieval = _parse_bool(
        values.get("ALLOW_LIVE_RETRIEVAL"),
        default=app_env not in {RuntimeEnvironment.DEMO, RuntimeEnvironment.PRODUCTION},
    )
    if app_env == RuntimeEnvironment.DEMO:
        allow_live_retrieval = False

    return WarRoomSettings(
        app_env=app_env,
        use_cache=use_cache,
        schema_version=values.get("SCHEMA_VERSION", "v0-demo"),
        exa_api_key=_secret_or_none(values.get("EXA_API_KEY")),
        cache_dir=_resolve_path(repo_root, values.get("CACHE_DIR", "cache")),
        cache_samples_dir=_resolve_path(repo_root, values.get("CACHE_SAMPLES_DIR", "cache_samples")),
        output_dir=_resolve_path(repo_root, values.get("OUTPUT_DIR", "output")),
        runs_dir=_resolve_path(repo_root, values.get("RUNS_DIR", "runs")),
        feature_flags=FeatureFlags(
            allow_live_retrieval=allow_live_retrieval,
            enable_notebook_surface=_parse_bool(values.get("ENABLE_NOTEBOOK_SURFACE"), default=True),
        ),
    )


def _read_env_values(env_file: Path) -> dict[str, str]:
    values: dict[str, str] = {}

    if env_file.exists():
        for key, value in dotenv_values(env_file).items():
            if value is not None:
                values[key] = value

    values.update(os.environ)
    return values


def _resolve_path(repo_root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def _parse_bool(raw_value: str | None, *, default: bool) -> bool:
    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {raw_value!r}")


def _secret_or_none(raw_value: str | None) -> SecretStr | None:
    if raw_value is None:
        return None
    cleaned = raw_value.strip()
    if not cleaned:
        return None
    return SecretStr(cleaned)
