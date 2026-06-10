# Architecture and Directory Structure

Date: 2026-06-10
Status: current MVP architecture and accepted implementation constraints

This document describes the current `dotnvim-bridge` MVP implementation. Exploratory long-term ideas, especially the Lua-tool architecture, live in separate notes and are not active implementation requirements unless promoted through OpenSpec.

## Project purpose

`dotnvim-bridge` is an agent-side MCP server for inspecting and debugging a host-running Neovim instance.

Primary goal:

```text
Codex / agent
  -> dotnvim-bridge MCP server
  -> pinned upstream nvim-mcp==1.0.0
  -> remote Neovim msgpack-RPC endpoint
  -> host Neovim
```

Reliability rule:

```text
The durable bridge must live outside the mutable Neovim config under repair.
```

This is why the MVP does not require a Neovim plugin and does not register persistent Neovim-side tools.

## Naming

Use one name across the repository, package metadata, and command:

```text
repository:        dotnvim-bridge
distribution name: dotnvim-bridge
console command:   dotnvim-bridge
Python package:    dotnvim_bridge
```

The hyphenated name is used for the repository, Python distribution, and executable command. The underscored name is used for Python imports.

## MVP release goal

The MVP goal is a publishable Python package that provides a working MCP server and the first batch of high-level Neovim debug tools.

The package should support normal Python package flows:

```bash
uv run dotnvim-bridge
uv build
# later, after publication:
uvx dotnvim-bridge
```

MVP success is not a complete custom Neovim client. MVP success is:

- installable Python distribution;
- `dotnvim-bridge` console command;
- pinned `nvim-mcp==1.0.0` dependency;
- first-batch MCP tools that are useful immediately;
- tests for dependency pinning, boundaries, limits, and tool behavior;
- package build artifacts can be produced with `uv build`.

## Current implementation layout

```text
dotnvim-bridge/
├── pyproject.toml
├── uv.lock
├── README.md
├── LICENSE
├── Makefile
├── .pre-commit-config.yaml
├── .env.example
├── .gitignore
│
├── src/
│   └── dotnvim_bridge/
│       ├── __init__.py
│       ├── __main__.py             # python -m dotnvim_bridge
│       ├── py.typed
│       ├── server.py               # FastMCP server and public MCP tool registration
│       ├── session.py              # only module importing upstream nvim_mcp internals
│       ├── settings.py             # environment/default settings
│       ├── errors.py               # structured bridge errors
│       ├── limits.py               # response truncation helpers
│       ├── schemas.py              # typed response aliases / schema helpers
│       ├── lua_snippets.py         # MVP ephemeral Lua snippets used by tools
│       └── tools/
│           ├── __init__.py
│           ├── debug_snapshot.py
│           ├── messages.py
│           ├── logs.py
│           ├── lsp.py
│           └── health.py
│
├── tests/
│   ├── __init__.py
│   ├── test_dependency_pin.py
│   ├── test_limits.py
│   ├── test_session_boundaries.py
│   ├── test_tools.py
│   ├── test_live_integration.py    # skipped unless RUN_LIVE_NVIM_TESTS=1
│   └── fixtures/
│       └── sample_responses.py
│
├── docs/
├── examples/
├── scripts/
└── openspec/
```

## Current runtime dependency strategy

The MVP intentionally maximizes reuse of pinned upstream `nvim-mcp==1.0.0`.

`nvim-mcp` currently provides the low-level Neovim access we do not want to reimplement yet:

- Neovim msgpack-RPC client;
- TCP / socket connection support;
- `NVIM_ADDRESS` discovery behavior;
- connection management and retry behavior;
- existing primitives for state, diagnostics, commands, and buffer reads;
- access to `nvim_exec_lua` through its internal client.

Local code should implement only the project-specific wrapper behavior:

- MCP-facing tool surface;
- thin session adapter;
- error normalization;
- response limits;
- higher-level debug/config workflows;
- tests and package metadata.

Future replacement of upstream internals should happen behind `session.py` so MCP tools do not need to change.

## Current layer boundaries

### `server.py`: MCP adapter

Responsibilities:

- create the FastMCP server;
- register MCP tools;
- keep tool docstrings and argument types visible to MCP clients;
- instantiate the project session adapter;
- convert unexpected exceptions into structured error responses.

Non-responsibilities:

- no direct `nvim_mcp` imports;
- no low-level RPC implementation;
- no large Neovim-specific workflow logic.

### `session.py`: upstream adapter / communication seam

Responsibilities:

- be the only module that imports upstream `nvim_mcp` internals;
- preserve the `NVIM_ADDRESS` contract;
- expose small project-local methods such as:
  - `command(...)`
  - `exec_lua(...)`
  - `get_state(...)`
  - `get_state_brief(...)`
  - `get_diagnostics(...)`
  - `read_buffer(...)`
- normalize low-level Neovim/RPC errors into `BridgeError`;
- remain replaceable if the project later owns the RPC/client layer.

Boundary rule:

```text
No module outside session.py should import nvim_mcp.
```

This rule is enforced by `tests/test_session_boundaries.py`.

### `tools/`: first-batch high-level workflows

Each tool module owns one workflow:

```text
tools/messages.py        -> get_messages
tools/logs.py            -> get_logs_tail
tools/lsp.py             -> get_lsp_snapshot
tools/health.py          -> run_checkhealth
tools/debug_snapshot.py  -> get_debug_snapshot
```

Tool modules may call `session.py`, `limits.py`, and MVP Lua snippets, but they must not import upstream `nvim_mcp` internals directly.

### `lua_snippets.py`: MVP implementation detail

`lua_snippets.py` contains read-oriented ephemeral Lua snippets used by the first-batch tools.

Current snippets:

- `LOGS_TAIL`
- `LSP_SNAPSHOT`
- `RUNTIME_SNAPSHOT`

Important clarification:

```text
These snippets are not Neovim-side dynamic tools.
They are not installed into user config.
They are sent ephemerally through RPC and executed in the remote Neovim process.
```

This file is an MVP convenience. It is not a final long-term architecture decision. The candidate long-term direction is to move from Python-held snippets toward packaged portable Lua tools with generated schemas; see `docs/notes-three-layer-lua-tool-architecture.md`.

### `limits.py`, `settings.py`, `errors.py`, `schemas.py`

These modules keep common behavior out of tool functions:

- `limits.py`: line/response truncation helpers;
- `settings.py`: environment-derived defaults;
- `errors.py`: `BridgeError` and error normalization;
- `schemas.py`: typed aliases for JSON-safe/public response shapes.

## Public MCP tools in the MVP

The current MCP server exposes:

```text
bridge_info
get_messages
get_logs_tail
get_lsp_snapshot
run_checkhealth
get_debug_snapshot
```

Tool behavior is read-oriented by default. First-batch tools should not save files, quit Neovim, or invoke host shell commands.

## Testing and validation

Default local checks:

```bash
uv run ruff check .
uv run basedpyright
uv run pytest
uv build
openspec validate add-wrapper-nvim-mcp-with-pinned-upstream --strict
```

Current test categories:

- dependency pin and console script tests;
- response limit tests;
- high-level tool tests with mocked session responses;
- import-boundary test preventing `nvim_mcp` imports outside `session.py`;
- optional live Neovim integration test.

Live test command:

```bash
NVIM_ADDRESS=vex9z7.com:16667 RUN_LIVE_NVIM_TESTS=1 uv run pytest tests/test_live_integration.py
```

## Current decisions

Accepted for the MVP:

1. Publish a Python package named `dotnvim-bridge`.
2. Use a `src/` layout and Python import package `dotnvim_bridge`.
3. Pin `nvim-mcp==1.0.0` and isolate its internals in `session.py`.
4. Keep the communication/session layer thin and replaceable.
5. Expose first-batch read-oriented MCP tools.
6. Use ephemeral Lua snippets only as an MVP implementation detail.
7. Use `uv`, `hatchling`, `ruff`, `pytest`, `pytest-asyncio`, `pytest-cov`, `basedpyright`, and `pre-commit` for development.

Not accepted as final implementation yet:

- generated Lua tool schemas;
- portable Lua tool package layout;
- a separate runtime worker process;
- dynamic internal Lua tool discovery;
- exposing arbitrary Lua evaluation as a normal product tool.

Those ideas are recorded as candidate architecture in `docs/notes-three-layer-lua-tool-architecture.md`.
