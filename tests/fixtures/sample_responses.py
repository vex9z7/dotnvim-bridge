"""Shared test fixtures."""

from __future__ import annotations

STATE_BRIEF = {"cwd": "/tmp/project", "windows": [{"file": "init.lua"}]}
DIAGNOSTICS = [{"file": "init.lua", "line": 1, "severity": "warning", "message": "demo"}]
RUNTIME = {"cwd": "/tmp/project", "paths": {"config": "/tmp/nvim"}}
LSP = {"clients": [], "diagnostics": [], "log_path": "/tmp/lsp.log"}
LOGS = {
    "nvim_log": {"path": "/tmp/nvim.log", "readable": True, "tail": ["one"]},
    "lsp_log": {"path": "/tmp/lsp.log", "readable": True, "tail": []},
}
