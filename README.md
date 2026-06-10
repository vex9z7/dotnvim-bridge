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

## Current status

The confirmed external baseline uses upstream `paulburgess1357/nvim-mcp` directly:

```text
Codex CLI inside container
  -> uvx nvim-mcp
  -> NVIM_ADDRESS=vex9z7.com:16667
  -> NPM Stream TCP 16667
  -> host Neovim --listen 0.0.0.0:16667
```

The repository now contains the first Python package scaffold for the wrapper MCP, with pinned `nvim-mcp==1.0.0`, initial high-level tools, tests, and package build validation. Direct upstream mode remains the rollback/baseline path.

## Read next

1. [Core requirements](docs/core-requirements.md)
2. [Current architecture](docs/architecture.md)
3. [Development tooling](docs/development-tooling.md)
4. [Roadmap](docs/roadmap.md)
5. [Project assessment](docs/project-assessment.md)
6. [Setup](docs/setup.md)
7. [Debug recipes](docs/debug-recipes.md)
8. [Capability boundary](docs/capability-boundary.md)
9. [Candidate three-layer Lua tool architecture](docs/notes-three-layer-lua-tool-architecture.md)

## Active OpenSpec change

```text
openspec/changes/add-wrapper-nvim-mcp-with-pinned-upstream
```
