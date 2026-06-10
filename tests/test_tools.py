from __future__ import annotations

from typing import Any

import pytest

from dotnvim_bridge.tools.debug_snapshot import get_debug_snapshot
from dotnvim_bridge.tools.health import run_checkhealth
from dotnvim_bridge.tools.logs import get_logs_tail
from dotnvim_bridge.tools.lsp import get_lsp_snapshot
from dotnvim_bridge.tools.messages import get_messages
from tests.fixtures.sample_responses import DIAGNOSTICS, LOGS, LSP, RUNTIME, STATE_BRIEF


class FakeSession:
    async def command(self, command: str | list[str]) -> dict[str, Any]:
        if command == "messages":
            return {"output": "one\ntwo\nthree"}
        return {"output": "ok"}

    async def exec_lua(self, code: str, *args: Any) -> dict[str, Any]:
        if "nvim_log" in code:
            return dict(LOGS)
        if "vim.lsp.get_clients" in code:
            return dict(LSP)
        return dict(RUNTIME)

    async def read_buffer(
        self,
        file: str,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> dict[str, Any]:
        return {"lines": ["1: health ok", "2: done"], "total_lines": 2}

    async def get_state_brief(self) -> dict[str, Any]:
        return dict(STATE_BRIEF)

    async def get_diagnostics(self, file: str | None = None) -> list[dict[str, Any]]:
        return list(DIAGNOSTICS)


@pytest.mark.asyncio
async def test_get_messages_limits_output() -> None:
    result = await get_messages(FakeSession(), limit=2)  # type: ignore[arg-type]
    assert result["messages"] == {
        "lines": ["two", "three"],
        "line_count": 3,
        "returned_line_count": 2,
        "truncated": True,
    }


@pytest.mark.asyncio
async def test_get_logs_tail_can_exclude_lsp() -> None:
    result = await get_logs_tail(FakeSession(), lines=10, include_lsp=False)  # type: ignore[arg-type]
    assert "nvim_log" in result
    assert "lsp_log" not in result


@pytest.mark.asyncio
async def test_get_lsp_snapshot() -> None:
    result = await get_lsp_snapshot(FakeSession())  # type: ignore[arg-type]
    assert result["clients"] == []
    assert result["log_path"] == "/tmp/lsp.log"


@pytest.mark.asyncio
async def test_run_checkhealth_returns_health_lines() -> None:
    result = await run_checkhealth(FakeSession(), topic="vim.lsp", max_lines=10)  # type: ignore[arg-type]
    assert result["topic"] == "vim.lsp"
    assert result["buffer"] == "health://"
    assert result["health"] == {
        "lines": ["1: health ok", "2: done"],
        "line_count": 2,
        "returned_line_count": 2,
        "truncated": False,
    }


@pytest.mark.asyncio
async def test_get_debug_snapshot() -> None:
    result = await get_debug_snapshot(FakeSession(), include_logs=True)  # type: ignore[arg-type]
    assert result["state"] == STATE_BRIEF
    assert result["diagnostics"] == DIAGNOSTICS
    assert "messages" in result
    assert result["runtime"] == RUNTIME
    assert result["lsp"] == LSP
    assert result["logs"] == LOGS
