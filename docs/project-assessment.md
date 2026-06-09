# nvim-mcp Project Assessment

Date: 2026-06-09

## Current decision

Use `paulburgess1357/nvim-mcp` as the current runtime baseline and pinned dependency candidate for a first-party wrapper MCP.

This is not the final product shape. It is the confirmed thin bridge/control layer we can build on while keeping the minimum debug/rescue path outside the mutable Neovim config.

## Project assessed

- GitHub: <https://github.com/paulburgess1357/nvim-mcp>
- PyPI package: `nvim-mcp`
- Pinned version for wrapper proposal: `nvim-mcp==1.0.0`
- Inspected upstream commit: `db73c3706c466a0f7740b693c3a23ea426287b97`
- Reference clone used during planning: `/tmp/nvim-mcp-upstream`

## Why this remains the baseline

`paulburgess1357/nvim-mcp` fits the core reliability requirement:

- runs as an external MCP server, outside the Neovim config under repair;
- requires no Neovim plugin for the minimum bridge path;
- connects directly to TCP via `NVIM_ADDRESS=host:port`;
- starts simply with `uvx nvim-mcp`;
- exposes enough primitive controls to inspect and repair Neovim through raw RPC and ad hoc Lua snippets.

Confirmed endpoint:

```text
NVIM_ADDRESS=vex9z7.com:16667
```

Confirmed runtime chain:

```text
Codex CLI inside container
  -> uvx nvim-mcp
  -> NVIM_ADDRESS=vex9z7.com:16667
  -> NPM Stream TCP 16667
  -> host Neovim --listen 0.0.0.0:16667
```

## Capability summary

Observed tools include:

- `connect`
- `get_state_brief`
- `get_state`
- `read_full_buf`
- `read_buf_range`
- `find_and_replace_buf`
- `write_full_buf`
- `send_command`
- `send_keys`
- `get_all_diagnostics`
- `get_buf_diagnostics`
- `highlight_range`
- `highlight_ranges`
- `clear_highlights`
- `add_virtual_text`
- `add_virtual_texts`
- `clear_virtual_texts`

This covers:

- state inspection;
- buffer read/edit;
- diagnostics;
- Ex commands;
- Lua execution through `:lua`;
- `:messages`;
- `:checkhealth` plus `health://` buffer reads;
- log reads through Lua/readfile;
- normal-mode keystrokes;
- visual annotations.

## Main limitation

The tool surface is low-level. It lacks first-class high-level config/debug tools such as:

- `get_debug_snapshot`
- `get_messages`
- `get_logs_tail`
- `get_lsp_snapshot`
- `run_checkhealth`
- `get_plugin_snapshot`
- `get_runtime_snapshot`
- `get_keymaps_snapshot`
- `get_options_snapshot`

Today these workflows are possible only by composing primitive tools and Lua snippets. That is acceptable for the baseline, but it is exactly what the wrapper/tool-layer proposal should fix.

## Comparison note: linw1995/nvim-mcp

A separate local clone exists at:

```text
/workspace/git/nvim-mcp
```

It points to:

```text
https://github.com/linw1995/nvim-mcp
HEAD 0827b45db33a3b9f16c1d59467b08470e9c781aa
```

That project has attractive ideas:

- stdio and Streamable HTTP transport;
- connection-aware multi-instance model;
- broader LSP/code-intelligence tools;
- dynamic tool registration concept.

However, its Neovim-side dynamic tool model conflicts with this project's reliability requirement if used as the core tool layer. This project should borrow the modular tool architecture idea, but keep core tools agent-side and outside the mutable Neovim config.

## Install model: current baseline

Codex config:

```toml
[mcp_servers.nvim-mcp]
command = "uvx"
args = ["nvim-mcp"]

[mcp_servers.nvim-mcp.env]
NVIM_ADDRESS = "vex9z7.com:16667"
```

Equivalent command:

```bash
codex mcp add nvim-mcp \
  --env NVIM_ADDRESS=vex9z7.com:16667 \
  -- uvx nvim-mcp
```

## Wrapper proposal

The current implementation proposal is:

```text
openspec/changes/add-wrapper-nvim-mcp-with-pinned-upstream
```

Decision summary:

- build a first-party wrapper MCP package;
- pin upstream dependency to `nvim-mcp==1.0.0`;
- record commit `db73c3706c466a0f7740b693c3a23ea426287b97` as the inspected source baseline;
- keep the bridge core thin and stable;
- implement high-level tools as agent-side pluggable modules;
- do not implement the project tool layer as Neovim-side dynamic tools.

## Recommendation

Continue using direct upstream `uvx nvim-mcp` only as the working baseline while implementing the wrapper.

The desired end state is not a recipe-only workflow. The desired end state is a reliable agent-side bridge with stable primitive RPC access and high-level debug/config tools layered above it.
