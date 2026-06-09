## Why

The bridge must remain usable even while the Neovim config under repair is broken or being modified. Core debug and recovery capability should therefore live outside the mutable Neovim config where practical, instead of depending primarily on a Neovim-side plugin that the agent might break.

The current recipe-based `nvim-mcp` workflow proves that Codex can inspect and control host Neovim, but repeated debug flows still depend on the agent manually composing primitive tools and Lua snippets. We should turn the stable flows into a first-party wrapper MCP package while reusing upstream `nvim-mcp` as the pinned transport/control layer, so we get high-level tools now without immediately owning the full Neovim msgpack-RPC implementation.

## What Changes

- Introduce a new first-party Python wrapper MCP package, named `dotnvim-bridge`, intended to become a publishable package with a `dotnvim-bridge` console command.
- Implement the wrapper using **方案 A**: depend on upstream `nvim-mcp` and reuse its Python manager/client layer instead of forking or replacing the bottom layer at this stage. The MVP should stay thin and implement only the wrapper/tool behavior that is necessary.
- Pin the upstream dependency to a known-good release:
  - package: `nvim-mcp==1.0.0`
  - upstream repository: `https://github.com/paulburgess1357/nvim-mcp`
  - reference commit: `db73c3706c466a0f7740b693c3a23ea426287b97`
  - reference commit date: `2026-05-18T19:12:07-06:00`
  - planning inspection clone: `/tmp/nvim-mcp-upstream`
  - additional local community reference clone: `/workspace/git/nvim-mcp` (`https://github.com/linw1995/nvim-mcp`, HEAD `0827b45db33a3b9f16c1d59467b08470e9c781aa`); this is **not** the pinned upstream package baseline
- Adopt the architectural direction of a thin stable bridge core plus a pluggable high-level tool layer. The core bridge remains responsible for MCP lifecycle, Neovim RPC connectivity, rescue primitives, and bounded responses; higher-level debug/config workflows are implemented as replaceable tool modules.
- Expose high-level MCP tools that wrap common Neovim config-debug flows:
  - `get_debug_snapshot`
  - `get_messages`
  - `get_logs_tail`
  - `get_lsp_snapshot`
  - `run_checkhealth`
- Keep the current host communication model unchanged:
  - Codex/agent runs inside the container.
  - Neovim runs outside the container.
  - Connection uses `NVIM_ADDRESS`, currently `vex9z7.com:16667`.
  - Neovim listens with raw msgpack-RPC over TCP.
- Document the pinned upstream reference so future maintainers can compare code behavior before upgrading or replacing the underlying implementation.
- Do not include legacy routes, alternative MCP bridge projects, endpoint auto-discovery, or immediate bottom-layer replacement in this proposal.
- Do not implement the project tool layer as Neovim-side dynamic tools; borrow the modular tool idea, but keep core tools agent-side and outside the mutable Neovim config.

## Capabilities

### New Capabilities

- `pinned-upstream-nvim-wrapper`: Defines a first-party wrapper MCP package that exposes high-level Neovim debug tools while depending on a pinned upstream `nvim-mcp` release and recorded repository commit.

### Modified Capabilities

- None.

## Impact

- Affected future code area:
  - new Python distribution / command name `dotnvim-bridge`;
  - Python import package directory `dotnvim_bridge`;
  - package metadata with `nvim-mcp==1.0.0` pinned;
  - MCP server entrypoint exposing high-level tools;
  - tests around wrapper behavior and dependency pinning.
- Affected runtime config:
  - Codex MCP config will eventually point to the wrapper command instead of directly running `uvx nvim-mcp`.
  - `NVIM_ADDRESS=vex9z7.com:16667` remains the primary connection setting.
- Affected documentation:
  - setup docs should explain direct upstream mode vs wrapper mode;
  - extension roadmap should identify `nvim-mcp==1.0.0` and commit `db73c3706c466a0f7740b693c3a23ea426287b97` as the pinned baseline.
- No Neovim plugin is required.
- No change is required on the host Neovim side beyond the existing `--listen` TCP setup.
