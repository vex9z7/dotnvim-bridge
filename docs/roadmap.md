# nvim-mcp Extension Roadmap

Date: 2026-06-09

## 1. Current positioning

This project is building a Neovim ↔ Codex/agent bridge for config debugging, reproduction, and repair.

The core bridge must remain usable even when the Neovim config under repair is broken. Therefore, the durable tool layer belongs outside Neovim config, on the agent/MCP-server side.

Current baseline:

```text
Codex CLI inside container
  -> uvx nvim-mcp
  -> NVIM_ADDRESS=vex9z7.com:16667
  -> host Neovim raw msgpack-RPC listener
```

Current target:

```text
Codex CLI
  -> first-party wrapper MCP
      -> thin stable bridge/session layer
      -> agent-side pluggable high-level tools
      -> pinned upstream nvim-mcp / compatible Neovim RPC layer
      -> host Neovim
```

## 2. Architecture principles

### 2.1 Thin stable bridge core

The bridge core should be boring and hard to break. It owns:

- MCP server lifecycle;
- connection/session management;
- `NVIM_ADDRESS` handling;
- raw Neovim msgpack-RPC access;
- bounded command/Lua responses;
- structured error reporting;
- rescue primitives.

Minimum rescue primitives:

- execute Lua;
- run Ex commands;
- read buffers/ranges;
- collect state;
- collect diagnostics;
- perform targeted in-memory edits.

### 2.2 Agent-side pluggable tools

High-level workflows should be implemented as replaceable agent-side tool modules, not as Neovim-side dynamic tools.

Initial modules/tools:

- `get_debug_snapshot`
- `get_messages`
- `get_logs_tail`
- `get_lsp_snapshot`
- `run_checkhealth`

Later modules/tools:

- `get_plugin_snapshot`
- `get_runtime_snapshot`
- `get_keymaps_snapshot`
- `get_options_snapshot`
- `get_autocmds_snapshot`
- `create_debug_buffer`

### 2.3 No Neovim-side dynamic tools

Do not implement the project tool layer as Neovim-side dynamic tools.

We can borrow the modular/discoverable tool concept from `linw1995/nvim-mcp`, but the implementation route for this project is agent-side. Neovim-side Lua may still be sent as ephemeral RPC snippets, but it should not be installed or registered as persistent tools in the user's editable config.

## 3. Dependency baseline

Current wrapper proposal pins:

```text
package: nvim-mcp==1.0.0
repo: https://github.com/paulburgess1357/nvim-mcp
commit: db73c3706c466a0f7740b693c3a23ea426287b97
```

Reason:

- avoids API drift while importing/reusing upstream Python internals;
- keeps implementation fast;
- preserves an escape hatch to replace the low-level RPC/session layer later.

## 4. First-batch tool contracts

### 4.1 `get_debug_snapshot`

Input:

```json
{
  "include_logs": false,
  "include_plugins": true,
  "include_lsp": true,
  "max_messages": 200,
  "max_log_lines": 120
}
```

Output shape:

```json
{
  "state": {},
  "diagnostics": [],
  "messages": [],
  "runtime": {
    "version": "...",
    "cwd": "...",
    "paths": {
      "config": "...",
      "state": "...",
      "log": "..."
    }
  },
  "lsp": {},
  "plugins": {},
  "logs": {}
}
```

### 4.2 `get_messages`

Input:

```json
{
  "limit": 200
}
```

Output:

```json
{
  "messages": ["..."]
}
```

### 4.3 `get_logs_tail`

Input:

```json
{
  "lines": 120,
  "include_lsp": true
}
```

Output:

```json
{
  "nvim_log": {
    "path": ".../nvim.log",
    "readable": true,
    "tail": []
  },
  "lsp_log": {
    "path": ".../lsp.log",
    "readable": true,
    "tail": []
  }
}
```

### 4.4 `get_lsp_snapshot`

Input:

```json
{
  "include_diagnostics": true
}
```

Output:

```json
{
  "clients": [],
  "diagnostics": [],
  "log_path": ".../lsp.log",
  "log_level": "WARN"
}
```

### 4.5 `run_checkhealth`

Input:

```json
{
  "topic": "vim.lsp",
  "max_lines": 300
}
```

Output:

```json
{
  "topic": "vim.lsp",
  "buffer": "health://...",
  "lines": []
}
```

## 5. Implementation phases

### Phase 1: wrapper scaffold

- Create wrapper package.
- Pin `nvim-mcp==1.0.0`.
- Isolate upstream imports in a small adapter/session layer.
- Keep `NVIM_ADDRESS` contract unchanged.

### Phase 2: first high-level tools

- Implement first-batch tools as agent-side modules.
- Keep tools read-oriented by default.
- Add line/byte limits for messages, logs, and health output.
- Return structured errors for unreachable Neovim or failed RPC calls.

### Phase 3: validation and Codex switch

- Test with `NVIM_ADDRESS=vex9z7.com:16667`.
- Update Codex config to launch the wrapper instead of direct upstream.
- Keep rollback to `uvx nvim-mcp` documented.

### Phase 4: optional low-level replacement

If upstream internals become limiting, replace the low-level session/RPC implementation behind the same high-level tool contracts.

The stable boundary is the high-level agent-facing tool surface, not the first internal implementation.

## 6. Codex config examples

Current direct baseline:

```toml
[mcp_servers.nvim-mcp]
command = "uvx"
args = ["nvim-mcp"]

[mcp_servers.nvim-mcp.env]
NVIM_ADDRESS = "vex9z7.com:16667"
```

Future wrapper mode:

```toml
[mcp_servers.dotnvim-bridge]
command = "uv"
args = ["run", "--directory", "/workspace/git/dotnvim-bridge", "dotnvim-bridge"]

[mcp_servers.dotnvim-bridge.env]
NVIM_ADDRESS = "vex9z7.com:16667"
```

Published wrapper mode:

```toml
[mcp_servers.dotnvim-bridge]
command = "uvx"
args = ["dotnvim-bridge"]

[mcp_servers.dotnvim-bridge.env]
NVIM_ADDRESS = "vex9z7.com:16667"
```

## 7. Active OpenSpec

Implementation planning is tracked in:

```text
openspec/changes/add-wrapper-nvim-mcp-with-pinned-upstream
```
