"""Thin adapter over pinned upstream nvim-mcp internals.

This is intentionally the only module that imports ``nvim_mcp``. During the
MVP it mostly delegates to upstream primitives and preserves a replacement seam
for a future first-party low-level implementation.
"""

from __future__ import annotations

from typing import Any

from nvim_mcp.manager import NeovimManager
from nvim_mcp.types import NvimError

from dotnvim_bridge.errors import BridgeError


class NvimSession:
    """Project-local adapter for Neovim operations."""

    def __init__(self, manager: NeovimManager | None = None) -> None:
        self._manager = manager or NeovimManager()

    async def connect(self, socket_path: str | None = None) -> dict[str, Any]:
        """Connect to Neovim, relying on upstream discovery/NVIM_ADDRESS semantics."""

        result = await self._manager.connect(socket_path=socket_path)
        self._raise_if_error(result)
        return result

    async def command(self, command: str | list[str]) -> dict[str, Any] | list[dict[str, Any]]:
        """Run one or more Ex commands through upstream nvim-mcp."""

        return await self._wrap(lambda: self._manager.send_command(command))

    async def get_state(self) -> dict[str, Any]:
        """Return upstream's full state snapshot."""

        return await self._wrap(self._manager.get_state)

    async def get_state_brief(self) -> dict[str, Any]:
        """Return upstream's brief state snapshot."""

        return await self._wrap(self._manager.get_state_brief)

    async def get_diagnostics(self, file: str | None = None) -> list[Any]:
        """Return diagnostics for all buffers or one buffer."""

        return await self._wrap(lambda: self._manager.get_diagnostics(file=file))

    async def read_buffer(
        self,
        file: str,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> dict[str, Any]:
        """Read a Neovim buffer using upstream buffer primitives."""

        return await self._wrap(
            lambda: self._manager.read_buffer(
                file=file,
                start_line=start_line,
                end_line=end_line,
            )
        )

    async def exec_lua(self, code: str, *args: Any) -> Any:
        """Execute ephemeral Lua through the upstream connection.

        Upstream exposes this capability internally via ``NvimClient.exec_lua``.
        We keep this private access isolated here so tool modules do not depend
        on upstream internals.
        """

        return await self._wrap(
            lambda: self._manager._with_retry(self._exec_lua_sync, code, *args, raise_on_error=True)
        )  # noqa: SLF001

    def _exec_lua_sync(self, code: str, *args: Any) -> Any:
        nvim = self._manager._nvim  # noqa: SLF001
        if nvim is None:
            raise BridgeError("Neovim is not connected", code="not_connected")
        return nvim.exec_lua(code, *args)

    async def shutdown(self) -> None:
        """Close upstream connection state."""

        await self._manager.shutdown()

    @staticmethod
    def _raise_if_error(result: Any) -> None:
        if isinstance(result, dict) and "error" in result:
            raise BridgeError(str(result["error"]), code="nvim_error")

    async def _wrap(self, call):  # type: ignore[no-untyped-def]
        try:
            result = await call()
            self._raise_if_error(result)
            return result
        except BridgeError:
            raise
        except (NvimError, RuntimeError, OSError, TimeoutError) as exc:
            raise BridgeError(str(exc), code="nvim_error") from exc


def create_session() -> NvimSession:
    """Factory used by the MCP server."""

    return NvimSession()
