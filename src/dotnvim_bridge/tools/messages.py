"""`:messages` collection tool."""

from __future__ import annotations

from dotnvim_bridge.limits import limit_text_lines, split_lines
from dotnvim_bridge.session import NvimSession
from dotnvim_bridge.settings import get_settings


async def get_messages(session: NvimSession, limit: int | None = None) -> dict[str, object]:
    """Return recent Neovim `:messages` output with bounded lines."""

    settings = get_settings()
    max_lines = limit if limit is not None else settings.default_messages_limit
    result = await session.command("messages")
    output = ""
    if isinstance(result, dict):
        output = str(result.get("output", ""))
    return {"messages": limit_text_lines(split_lines(output), max_lines)}
