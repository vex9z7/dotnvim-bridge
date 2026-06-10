from __future__ import annotations

from pathlib import Path


def test_only_session_imports_upstream_nvim_mcp() -> None:
    offenders: list[str] = []
    for path in Path("src/dotnvim_bridge").rglob("*.py"):
        text = path.read_text()
        if "nvim_mcp" in text and path.name != "session.py":
            offenders.append(str(path))
    assert offenders == []
