# dotnvim-bridge

Agent-side Neovim bridge for Codex and similar AI agents.

The project goal is to let an agent inspect, debug, reproduce, and repair a host-running Neovim configuration while keeping the bridge itself outside the mutable Neovim config under repair.

## Architecture direction

```text
Codex / agent side
  -> dotnvim-bridge MCP server
      -> thin stable bridge core
      -> agent-side pluggable tools
      -> Neovim msgpack-RPC session
  -> host Neovim --listen 0.0.0.0:16667
```

Core rule:

```text
Do not implement the project tool layer as Neovim-side dynamic tools.
```

Neovim-side Lua can be sent as ephemeral RPC snippets, but the durable tools live agent-side.

## Current baseline

The current working baseline uses upstream `paulburgess1357/nvim-mcp` directly:

```text
Codex CLI inside container
  -> uvx nvim-mcp
  -> NVIM_ADDRESS=vex9z7.com:16667
  -> NPM Stream TCP 16667
  -> host Neovim --listen 0.0.0.0:16667
```

The MVP target is a first-party wrapper MCP with pinned `nvim-mcp==1.0.0` and high-level agent-side tools.

## Read next

1. [Core requirements](docs/core-requirements.md)
2. [Roadmap](docs/roadmap.md)
3. [Project assessment](docs/project-assessment.md)
4. [Setup](docs/setup.md)
5. [Debug recipes](docs/debug-recipes.md)
6. [Capability boundary](docs/capability-boundary.md)

## Active OpenSpec change

```text
openspec/changes/add-wrapper-nvim-mcp-with-pinned-upstream
```
