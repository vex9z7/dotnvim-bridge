"""Runtime settings for dotnvim-bridge."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return max(0, int(value))
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class Settings:
    """Configuration derived from environment variables."""

    nvim_address: str | None = os.environ.get("NVIM_ADDRESS")
    default_messages_limit: int = _env_int("DOTNVIM_BRIDGE_MESSAGES_LIMIT", 200)
    default_log_lines: int = _env_int("DOTNVIM_BRIDGE_LOG_LINES", 120)
    default_health_lines: int = _env_int("DOTNVIM_BRIDGE_HEALTH_LINES", 300)


def get_settings() -> Settings:
    """Return current process settings."""

    return Settings()
