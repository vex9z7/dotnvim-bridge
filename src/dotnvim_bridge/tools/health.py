"""`:checkhealth` runner tool."""

from __future__ import annotations

from dotnvim_bridge.limits import limit_text_lines
from dotnvim_bridge.session import NvimSession
from dotnvim_bridge.settings import get_settings


def _health_command(topic: str | None) -> str:
    if topic is None or not topic.strip():
        return "checkhealth"
    return f"checkhealth {topic.strip()}"


async def run_checkhealth(
    session: NvimSession,
    topic: str | None = None,
    max_lines: int | None = None,
) -> dict[str, object]:
    """Run `:checkhealth` and return bounded health buffer content."""

    settings = get_settings()
    limit = max_lines if max_lines is not None else settings.default_health_lines
    command_result = await session.command(_health_command(topic))
    buffer_result = await session.read_buffer("health://", 1, limit)
    raw_lines = buffer_result.get("lines", []) if isinstance(buffer_result, dict) else []
    lines = [str(line) for line in raw_lines]
    return {
        "topic": topic,
        "command": command_result,
        "buffer": "health://",
        "health": limit_text_lines(lines, limit),
    }
