"""FastMCP server entrypoint for dotnvim-bridge."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from dotnvim_bridge import __version__
from dotnvim_bridge.errors import normalize_error
from dotnvim_bridge.session import create_session
from dotnvim_bridge.tools.debug_snapshot import get_debug_snapshot as tool_get_debug_snapshot
from dotnvim_bridge.tools.health import run_checkhealth as tool_run_checkhealth
from dotnvim_bridge.tools.logs import get_logs_tail as tool_get_logs_tail
from dotnvim_bridge.tools.lsp import get_lsp_snapshot as tool_get_lsp_snapshot
from dotnvim_bridge.tools.messages import get_messages as tool_get_messages

mcp = FastMCP("dotnvim-bridge")
session = create_session()


async def _safe(call):  # type: ignore[no-untyped-def]
    try:
        return await call()
    except Exception as exc:  # MCP tools should return structured failures.
        return normalize_error(exc)


@mcp.tool()
async def bridge_info() -> dict[str, Any]:
    """Return dotnvim-bridge package and runtime information."""

    return {"name": "dotnvim-bridge", "version": __version__}


@mcp.tool()
async def get_messages(limit: int | None = None) -> dict[str, Any]:
    """Return recent `:messages` output in a bounded structured response."""

    return await _safe(lambda: tool_get_messages(session, limit=limit))


@mcp.tool()
async def get_logs_tail(lines: int | None = None, include_lsp: bool = True) -> dict[str, Any]:
    """Return bounded tails for Neovim logs."""

    return await _safe(lambda: tool_get_logs_tail(session, lines=lines, include_lsp=include_lsp))


@mcp.tool()
async def get_lsp_snapshot(include_diagnostics: bool = True) -> dict[str, Any]:
    """Return active LSP clients, diagnostics, and LSP log metadata."""

    return await _safe(
        lambda: tool_get_lsp_snapshot(session, include_diagnostics=include_diagnostics)
    )


@mcp.tool()
async def run_checkhealth(topic: str | None = None, max_lines: int | None = None) -> dict[str, Any]:
    """Run `:checkhealth` and return bounded health output."""

    return await _safe(lambda: tool_run_checkhealth(session, topic=topic, max_lines=max_lines))


@mcp.tool()
async def get_debug_snapshot(
    include_logs: bool = False,
    include_plugins: bool = True,
    include_lsp: bool = True,
    max_messages: int = 200,
    max_log_lines: int = 120,
) -> dict[str, Any]:
    """Return a broad read-oriented Neovim debug snapshot."""

    return await _safe(
        lambda: tool_get_debug_snapshot(
            session,
            include_logs=include_logs,
            include_plugins=include_plugins,
            include_lsp=include_lsp,
            max_messages=max_messages,
            max_log_lines=max_log_lines,
        )
    )


def main() -> None:
    """Run the stdio MCP server."""

    mcp.run()


if __name__ == "__main__":
    main()
