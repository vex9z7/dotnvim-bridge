"""Error helpers for dotnvim-bridge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class BridgeError(Exception):
    """Structured bridge error that can be returned through MCP tools."""

    message: str
    code: str = "bridge_error"
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"error": self.message, "code": self.code}
        if self.details:
            payload["details"] = self.details
        return payload


def normalize_error(exc: BaseException, *, code: str = "bridge_error") -> dict[str, Any]:
    """Convert an exception into a small JSON-safe error shape."""

    if isinstance(exc, BridgeError):
        return exc.to_dict()
    return {"error": str(exc), "code": code}
