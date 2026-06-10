"""Typed response shapes for public tool outputs."""

from __future__ import annotations

from typing import Any, TypedDict


class ErrorResponse(TypedDict):
    error: str
    code: str


class LinesResponse(TypedDict):
    lines: list[str]
    line_count: int
    returned_line_count: int
    truncated: bool


class MessagesResponse(TypedDict):
    messages: LinesResponse


JsonDict = dict[str, Any]
JsonList = list[Any]
JsonValue = JsonDict | JsonList | str | int | float | bool | None
