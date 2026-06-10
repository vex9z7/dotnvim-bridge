"""Optional live tests against a running Neovim --listen endpoint."""

from __future__ import annotations

import os

import pytest

from dotnvim_bridge.session import NvimSession

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_LIVE_NVIM_TESTS") != "1",
    reason="set RUN_LIVE_NVIM_TESTS=1 and NVIM_ADDRESS to run live Neovim tests",
)


@pytest.mark.asyncio
async def test_live_session_can_read_state_brief() -> None:
    session = NvimSession()
    try:
        state = await session.get_state_brief()
    finally:
        await session.shutdown()
    assert "cwd" in state
