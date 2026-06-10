from __future__ import annotations

from pathlib import Path

import tomllib


def test_nvim_mcp_dependency_is_pinned() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    dependencies = pyproject["project"]["dependencies"]
    assert "nvim-mcp==1.0.0" in dependencies


def test_console_script_is_dotnvim_bridge() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    assert pyproject["project"]["scripts"]["dotnvim-bridge"] == "dotnvim_bridge.server:main"
