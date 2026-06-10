"""Neovim log tail tool."""

from __future__ import annotations

from dotnvim_bridge.lua_snippets import LOGS_TAIL
from dotnvim_bridge.session import NvimSession
from dotnvim_bridge.settings import get_settings


async def get_logs_tail(
    session: NvimSession,
    lines: int | None = None,
    include_lsp: bool = True,
) -> dict[str, object]:
    """Return bounded tails for known Neovim logs."""

    settings = get_settings()
    max_lines = lines if lines is not None else settings.default_log_lines
    result = await session.exec_lua(LOGS_TAIL, max_lines)
    if not isinstance(result, dict):
        return {"error": "Unexpected log snapshot response", "code": "invalid_response"}
    if not include_lsp:
        result.pop("lsp_log", None)
    return result
