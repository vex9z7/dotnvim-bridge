"""Helpers for bounded MCP responses."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TypeVar

T = TypeVar("T")


def clamp_non_negative(value: int, default: int) -> int:
    """Return *value* when positive, otherwise *default*."""

    return value if value > 0 else default


def tail_lines(lines: Sequence[T], limit: int) -> tuple[list[T], bool]:
    """Return at most the last *limit* lines and whether truncation happened."""

    if limit <= 0:
        return [], bool(lines)
    if len(lines) <= limit:
        return list(lines), False
    return list(lines[-limit:]), True


def split_lines(text: str) -> list[str]:
    """Split command output into display lines without preserving final empty line."""

    if not text:
        return []
    return text.splitlines()


def limit_text_lines(lines: Iterable[str], limit: int) -> dict[str, object]:
    """Create a JSON-safe bounded line response."""

    original = list(lines)
    bounded, truncated = tail_lines(original, limit)
    return {
        "lines": bounded,
        "line_count": len(original),
        "returned_line_count": len(bounded),
        "truncated": truncated,
    }
