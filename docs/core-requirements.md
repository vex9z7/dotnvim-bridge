# Core Requirements: Neovim ↔ Agent Bridge

## Purpose

Build a reliable bridge between a host-running Neovim instance and Codex or similar AI agents, so the agent can help iterate on Neovim configuration safely and efficiently.

The bridge is for config work, not only code intelligence. Primary workflows include:

- inspecting current Neovim/editor state;
- debugging broken or outdated Neovim configuration;
- reproducing plugin/LSP/runtime problems;
- reading diagnostics, `:messages`, `:checkhealth`, logs, runtime paths, options, keymaps, autocmds, and plugin state;
- proposing minimal config changes;
- applying targeted in-memory edits and saving only when explicitly requested.

## Key Constraint: Keep the Bridge Isolated from the Config Under Repair

The bridge must remain usable even while the user's Neovim configuration is broken or being actively edited by the agent.

This is the central reliability requirement.

A design is risky if the bridge's core availability depends on Neovim-side plugin code that lives inside the same config being modified. If the agent breaks plugin loading, `runtimepath`, lazy-loading, Lua module resolution, or the bridge plugin configuration itself, the agent may lose the ability to inspect and repair the editor.

Therefore, prefer an architecture where the durable bridge runs outside Neovim config:

```text
Codex / agent side
  -> external MCP server / wrapper / bridge
  -> raw Neovim msgpack-RPC endpoint
  -> host Neovim
```

Neovim-side dynamic tools are out of scope for this project. They may remain an external reference concept, but the project architecture should not rely on implementing tools inside the mutable Neovim config.

## Implication for linw1995/nvim-mcp

`linw1995/nvim-mcp` has an attractive dynamic tool model: custom tools can be registered from Neovim-side Lua and exposed to MCP clients. For this project, that model is useful as an architectural reference only; it is not an implementation route.

However, for this project it has a critical reliability concern:

- many integrations live on the Neovim side;
- the core use case is for the agent to modify/debug that same Neovim config;
- if the bridge plugin or its custom tool registration is broken by config edits, the agent can lose the bridge it needs to recover.

So `linw1995/nvim-mcp` remains useful as a reference for the dynamic-tool idea and broader MCP surface, but this project should not adopt Neovim-side dynamic tools as an implementation route.

## Preferred Direction

Prefer a separated, agent-side bridge:

- the MCP server runs in the agent/container environment;
- the bridge connects to Neovim through `--listen` / msgpack-RPC over TCP or socket;
- high-level debug/config tools are implemented outside the mutable Neovim config;
- any Neovim-side Lua is sent ad hoc through RPC as ephemeral snippets, not installed or registered as persistent Neovim-side tools;
- the setup should degrade gracefully: even if plugins fail, the bridge can still inspect state and run basic Lua/Ex commands.

This keeps the agent's repair tools separate from the system being repaired.

## Non-Goals

- Do not implement the project's tool layer as Neovim-side dynamic tools.
- Do not make the bridge depend on a Neovim plugin installed in the user's editable config.
- Do not require dynamic tool registration from the Neovim config for any core debug/rescue workflow.
- Do not treat LSP/code-intelligence features as the only success criterion; config/debug/recovery reliability is more important.

## Architectural Direction: Thin Stable Bridge + Pluggable Tools

The dynamic-tool idea is valuable and should influence the long-term architecture.

Preferred shape:

```text
stable bridge core
  -> minimal MCP server lifecycle
  -> stable Neovim msgpack-RPC session management
  -> small set of rescue primitives: exec_lua, command, read buffer, diagnostics, state

pluggable tool layer
  -> high-level debug/config tools
  -> project-specific recipes
  -> independently versioned/replaceable agent-side tool packs
```

The bridge core should stay thin, boring, and hard to break. It should focus on transport, connection management, raw RPC execution, bounded responses, and failure reporting.

High-level capabilities should live in a plugin-like architecture so they can evolve quickly without destabilizing the communication layer. Examples:

- `get_debug_snapshot`
- `get_messages`
- `get_logs_tail`
- `run_checkhealth`
- `get_lsp_snapshot`
- plugin-manager-specific snapshots
- config-specific debug recipes

Important distinction:

- **Agent-side tool plugins** are the project direction because they live outside the mutable Neovim config.
- **Neovim-side dynamic tools** are not part of the project implementation route. They are only a reference point for the idea that tools should be modular and discoverable.

This means the long-term project can borrow the dynamic-tool architecture concept from `linw1995/nvim-mcp` without implementing tools through Neovim-side plugin registration.
