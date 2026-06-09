## Context

Core reliability requirement: the Neovim-agent bridge must stay available while the user config is broken or being edited. Neovim-side plugins and dynamic tool registration are out of scope for this project because the agent may modify the same config that loads them.

The project currently has a confirmed working chain:

```text
Codex CLI inside container
  -> uvx nvim-mcp
  -> NVIM_ADDRESS=vex9z7.com:16667
  -> NPM Stream TCP 16667
  -> host Neovim --listen 0.0.0.0:16667
```

Upstream `nvim-mcp` has a simple and useful architecture:

```text
src/nvim_mcp/server.py     FastMCP stdio server and @mcp.tool() declarations
src/nvim_mcp/manager.py    connection lifecycle, discovery, retry, and tool orchestration
src/nvim_mcp/client.py     synchronous raw Neovim msgpack-RPC client over Unix socket or TCP
src/nvim_mcp/discovery.py  NVIM_ADDRESS and local socket discovery
src/nvim_mcp/lua.py        Lua snippets executed through nvim_exec_lua
```

The inspected upstream package metadata reports `nvim-mcp` version `1.0.0`. The upstream repository baseline inspected for this proposal is commit `db73c3706c466a0f7740b693c3a23ea426287b97` from `https://github.com/paulburgess1357/nvim-mcp`, dated `2026-05-18T19:12:07-06:00`. The planning inspection clone for that baseline is `/tmp/nvim-mcp-upstream`. A separate persistent community reference clone is available at `/workspace/git/nvim-mcp`; it currently points to `https://github.com/linw1995/nvim-mcp` commit `0827b45db33a3b9f16c1d59467b08470e9c781aa`, so it must not be confused with the pinned upstream dependency baseline.

## Goals / Non-Goals

**Goals:**

- Build a first-party MCP wrapper package, named `dotnvim-bridge`.
- Use upstream `nvim-mcp==1.0.0` as a pinned dependency.
- Record the upstream source commit used for design/reference to reduce API-drift ambiguity.
- Expose the first high-level debug tools:
  - `get_debug_snapshot`
  - `get_messages`
  - `get_logs_tail`
  - `get_lsp_snapshot`
  - `run_checkhealth`
- Preserve the current `NVIM_ADDRESS` contract and container-to-host TCP topology.
- Keep high-level tools read-oriented by default.

**Non-Goals:**

- Do not implement the tool layer as Neovim-side dynamic tool registration from the mutable user config.
- Do not fork upstream `nvim-mcp` as the primary implementation path.
- Do not replace the msgpack-RPC client layer in this change.
- Do not support legacy/failed bridge routes or alternative community MCP servers.
- Do not introduce multiple endpoint selection in this change.
- Do not add a Neovim plugin.
- Do not publish to PyPI until local/package behavior is validated.

## Decisions

### Decision 1: Build a wrapper MCP, not a fork

The wrapper will expose our desired high-level surface while delegating low-level Neovim connectivity to upstream `nvim-mcp`. This gives us ownership over the agent-facing API without immediately owning the raw RPC implementation.

Alternative considered: fork upstream immediately and patch tools directly. Rejected for this stage because it increases maintenance burden before the high-level surface has stabilized.

### Decision 2: Pin `nvim-mcp==1.0.0`

The wrapper dependency must be pinned to `nvim-mcp==1.0.0`. Upstream internal classes such as `NeovimManager` and `NvimClient` are useful but not guaranteed as a stable public extension API. Pinning prevents accidental breakage from upstream API drift.

Alternative considered: use an unbounded dependency such as `nvim-mcp>=1.0.0`. Rejected because this wrapper may import internals and should only upgrade intentionally.

### Decision 3: Record upstream commit hash separately from package version

The proposal records commit `db73c3706c466a0f7740b693c3a23ea426287b97` as the inspected source baseline. The package version controls installation, while the commit hash gives maintainers a concrete source tree for debugging and future diffs.

Alternative considered: record only the PyPI version. Rejected because source-level architecture decisions rely on repository files and may need exact commit comparison.

### Decision 4: Reuse upstream nvim-mcp as much as practical during MVP, isolated behind our own adapter

For the MVP, the wrapper should maximize reuse of pinned upstream `nvim-mcp==1.0.0`. Do not prematurely reimplement Neovim msgpack-RPC, discovery, connection retry, state collection, diagnostics, command execution, or buffer reads when upstream already provides working primitives.

The wrapper should still avoid scattering direct upstream imports throughout tool implementations. Instead, create a small internal adapter/session layer that owns interaction with upstream `nvim-mcp` classes. High-level tools call the adapter.

Expected shape:

```text
src/dotnvim_bridge/server.py       FastMCP entrypoint and public tool declarations
src/dotnvim_bridge/session.py      adapter over upstream NeovimManager/NvimClient
src/dotnvim_bridge/lua_snippets.py high-level structured Lua snippets
src/dotnvim_bridge/schemas.py      response normalization helpers/types
```

This keeps the future replacement path clear: if upstream internals become unsuitable, only `session.py` should need major changes. Until that replacement phase, `session.py` should stay thin, boring, and mostly delegating; business behavior belongs in the project tool layer.

Alternative considered: each tool imports upstream `NeovimManager` directly. Rejected because it couples the high-level surface too tightly to upstream internals.

### Decision 5: Keep the communication layer thin and put product behavior in tools

The long-term architecture should keep the communication/RPC layer small and stable, while letting high-level debug/config tools evolve as plugins or tool modules. The durable product value of `dotnvim-bridge` is the agent-side tool layer, not a custom msgpack-RPC implementation. This borrows the useful dynamic-tool concept from `linw1995/nvim-mcp`, but applies it on the agent side. Neovim-side dynamic tools are not part of this project route.

Alternative considered: put all high-level tools directly into the bridge core. Rejected because it makes the critical communication layer change too often and increases the chance of breaking the rescue path.

### Decision 6: Use a Python `src/` layout with one module per first-batch tool

The wrapper will use this implementation layout:

```text
dotnvim-bridge/
├── pyproject.toml
├── src/
│   └── dotnvim_bridge/
│       ├── __init__.py
│       ├── __main__.py
│       ├── server.py
│       ├── settings.py
│       ├── session.py
│       ├── errors.py
│       ├── schemas.py
│       ├── limits.py
│       ├── lua_snippets.py
│       └── tools/
│           ├── __init__.py
│           ├── debug_snapshot.py
│           ├── messages.py
│           ├── logs.py
│           ├── lsp.py
│           └── health.py
└── tests/
    ├── test_dependency_pin.py
    ├── test_limits.py
    ├── test_server_tools.py
    └── test_session.py
```

Rationale:

- `src/` layout avoids accidental imports from the repository root and catches packaging mistakes earlier.
- `dotnvim_bridge` matches Python import naming conventions while keeping the distribution and command name `dotnvim-bridge`.
- `server.py` stays thin and owns MCP registration only.
- `session.py` is the only module that imports upstream `nvim_mcp` internals and should mostly delegate during MVP.
- `tools/` modules own high-level workflows and product behavior without owning transport/session setup.
- `limits.py`, `schemas.py`, and `lua_snippets.py` keep response bounding, output shape, and ephemeral Lua snippets reusable.

Alternative considered: flat root-level `dotnvim_bridge/`. Rejected because this project is intended to be packaged and tested as an installed/editable Python distribution.

Alternative considered: put all tools in `server.py`. Rejected because it would make tool growth harder to review and would blur MCP registration, session management, and workflow logic.

### Decision 7: Prefer structured Lua for rich snapshots

High-level tools should use JSON-safe Lua results for state that Neovim can provide structurally, and only fall back to text command output where that is the native interface, such as `:messages` and `:checkhealth`.

Alternative considered: parse human-oriented command output for everything. Rejected because it is brittle and harder for agents to consume reliably.

### Decision 8: Keep first-batch tools read-oriented

The first wrapper tools are for debugging and config iteration insight. They should not save buffers, quit Neovim, or execute host shell commands. Mutation can remain available through upstream primitive tools in direct mode or be designed later as explicit wrapper tools.

Alternative considered: include edit/save helpers immediately. Rejected to keep the first wrapper surface safe and focused.

## Risks / Trade-offs

- **Risk: Upstream internals are not stable public APIs** → Mitigation: pin `nvim-mcp==1.0.0`, record commit `db73c3706c466a0f7740b693c3a23ea426287b97`, and isolate imports in `session.py`.
- **Risk: Wrapper duplicates some upstream capabilities** → Mitigation: wrapper tools should only encode higher-level workflows, not re-expose every primitive one-for-one.
- **Risk: `:checkhealth` and `:messages` remain text-oriented** → Mitigation: return bounded text with metadata and keep structured Lua for state snapshots.
- **Risk: Large logs or health buffers produce excessive MCP responses** → Mitigation: expose line/byte limits with conservative defaults.
- **Risk: Dependency pin delays upstream fixes** → Mitigation: handle upgrades as explicit proposals/tasks with source diff review.

## Migration Plan

1. Scaffold the wrapper Python package locally.
2. Add package metadata with `nvim-mcp==1.0.0` pinned.
3. Implement the adapter/session layer over upstream `nvim-mcp`.
4. Implement first-batch high-level tools.
5. Add tests with mocked adapter responses and, where practical, integration tests against a test Neovim instance.
6. Add Codex config example for wrapper mode:

```toml
[mcp_servers.dotnvim-bridge]
command = "uvx"
args = ["--from", "<local-or-published-package>", "dotnvim-bridge"]

[mcp_servers.dotnvim-bridge.env]
NVIM_ADDRESS = "vex9z7.com:16667"
```

7. After validation, switch local Codex config from direct `nvim-mcp` to wrapper mode.

Rollback is simple: restore the existing direct upstream MCP config:

```toml
[mcp_servers.nvim-mcp]
command = "uvx"
args = ["nvim-mcp"]

[mcp_servers.nvim-mcp.env]
NVIM_ADDRESS = "vex9z7.com:16667"
```

## Open Questions

- Should wrapper mode also expose selected upstream primitive tools, or should Codex run both upstream and wrapper MCP servers during transition?
- What response size limits should be the defaults for logs, messages, and health output?
- Should the first implementation import `NeovimManager` directly, or use `NvimClient` plus our own minimal manager semantics?
