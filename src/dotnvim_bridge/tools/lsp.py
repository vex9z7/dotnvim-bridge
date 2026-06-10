"""LSP snapshot tool."""

from __future__ import annotations

from dotnvim_bridge.lua_snippets import LSP_SNAPSHOT
from dotnvim_bridge.session import NvimSession


async def get_lsp_snapshot(
    session: NvimSession,
    include_diagnostics: bool = True,
) -> dict[str, object]:
    """Return active LSP clients, associations, diagnostics, and log metadata."""

    result = await session.exec_lua(LSP_SNAPSHOT, include_diagnostics)
    if not isinstance(result, dict):
        return {"error": "Unexpected LSP snapshot response", "code": "invalid_response"}
    return result
