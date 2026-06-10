"""General debug snapshot tool."""

from __future__ import annotations

from dotnvim_bridge.lua_snippets import RUNTIME_SNAPSHOT
from dotnvim_bridge.session import NvimSession
from dotnvim_bridge.tools.logs import get_logs_tail
from dotnvim_bridge.tools.lsp import get_lsp_snapshot
from dotnvim_bridge.tools.messages import get_messages


async def get_debug_snapshot(
    session: NvimSession,
    include_logs: bool = False,
    include_plugins: bool = True,
    include_lsp: bool = True,
    max_messages: int = 200,
    max_log_lines: int = 120,
) -> dict[str, object]:
    """Collect a broad read-oriented Neovim debug snapshot."""

    state = await session.get_state_brief()
    diagnostics = await session.get_diagnostics()
    runtime = await session.exec_lua(RUNTIME_SNAPSHOT)
    snapshot: dict[str, object] = {
        "state": state,
        "diagnostics": diagnostics,
        "messages": await get_messages(session, limit=max_messages),
        "runtime": runtime,
        "plugins": {"included": include_plugins, "available": False},
    }
    if include_lsp:
        snapshot["lsp"] = await get_lsp_snapshot(session, include_diagnostics=False)
    if include_logs:
        snapshot["logs"] = await get_logs_tail(session, lines=max_log_lines)
    return snapshot
