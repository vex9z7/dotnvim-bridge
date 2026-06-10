# Candidate Architecture: Three-Layer Lua Tool System

Date: 2026-06-10
Status: candidate design notes, not an accepted implementation decision

This document consolidates exploratory design discussions about a possible long-term architecture for `dotnvim-bridge`. It is intentionally separate from `docs/architecture.md`, which describes the current MVP implementation.

Nothing in this document is an active requirement until promoted through a follow-up OpenSpec change.

## Executive summary

The candidate direction is:

```text
Layer 1: Remote Neovim Lua Runtime
Layer 2: Portable Lua Tool Layer
Layer 3: Python MCP Adapter
```

The key idea is:

> Python should expose the real remote Neovim Lua runtime and adapt it to MCP; Neovim-specific business logic should live in portable Lua tools with generated schemas.

This does not mean Python should emulate Neovim locally. It means Python should provide a thin interface to the actual remote Neovim Lua runtime.

## Why consider this architecture?

The current MVP has Python tool modules plus Python-held Lua snippets. That is useful as a fast baseline, but it blurs two concerns:

```text
Python MCP / communication code
  vs.
Neovim-domain workflow logic
```

Neovim-domain logic naturally uses Neovim Lua APIs:

```lua
vim.api
vim.fn
vim.lsp
vim.diagnostic
vim.bo / vim.wo / vim.o
runtimepath
package.loaded
```

A longer-term design could make Lua tools the product layer and keep Python mostly as:

- remote runtime adapter;
- schema reader/dispatcher;
- MCP protocol adapter;
- package/CLI integration.

## Design principles under consideration

1. **Expose the real remote runtime, do not emulate it locally.**
   Python should call into the remote Neovim process, not recreate `vim.*` behavior.

2. **Make Lua tools portable.**
   A tool should run through `dotnvim-bridge` and, where practical, directly inside Neovim.

3. **Generate static schemas from the Lua tool layer.**
   MCP `tools/list` should not depend on a live Neovim connection.

4. **Use schemas as the Layer 2 / Layer 3 contract.**
   Python MCP code should not duplicate Lua tool business logic.

5. **Keep process boundaries optional at first.**
   Three logical layers do not require three processes on day one.

6. **Preserve the bridge isolation rule.**
   Packaged Lua tools may be sent ephemerally to Neovim, but should not require installation into the user's mutable Neovim config.

## Layer 1: Remote Neovim Lua Runtime

Layer 1 is the runtime/communication layer.

Responsibilities:

- connect to the remote Neovim instance;
- execute Lua in the remote Neovim process;
- pass JSON-safe arguments into Lua;
- return JSON-safe results;
- normalize transport/RPC errors;
- load or inject packaged Lua support code;
- provide a stable call surface for Layer 3.

Non-responsibilities:

- no MCP protocol;
- no MCP schema generation;
- no Neovim-domain business logic;
- no hardcoded LSP/log/checkhealth workflows except as generic runtime support.

Possible interface:

```python
class RemoteNvimLuaRuntime:
    async def eval(self, code: str, *args) -> JsonValue:
        ...

    async def eval_file(self, path: str, *args) -> JsonValue:
        ...

    async def call_tool(self, name: str, arguments: dict[str, object]) -> JsonValue:
        ...

    async def call_module_function(
        self,
        module_name: str,
        function_name: str,
        arguments: dict[str, object],
    ) -> JsonValue:
        ...
```

For the MVP generation of this architecture, Layer 1 could still delegate to pinned upstream `nvim-mcp==1.0.0`. Direct upstream imports should remain isolated in the low-level adapter.

## Layer 1.5: Loader, dispatcher, and contract support

Most Lua plugin systems have more than just a runtime. They also need:

```text
loader
contract helper
dispatcher
registry
error normalization
```

This support code is conceptually between the runtime and the actual tools.

Potential Lua modules:

```text
dotnvim_bridge.tool          # compact spec/schema helper
dotnvim_bridge.dispatcher    # call_tool implementation
dotnvim_bridge.registry      # tool name -> module mapping
```

Dispatcher responsibilities:

1. map tool name to module name;
2. load the Lua tool module;
3. validate arguments if validation is available;
4. call `tool.run(args)`;
5. normalize Lua errors into structured error tables;
6. return JSON-safe results.

Conceptual dispatcher shape:

```lua
local M = {}

local registry = {
  get_lsp_snapshot = "dotnvim_bridge.tools.get_lsp_snapshot",
  get_logs_tail = "dotnvim_bridge.tools.get_logs_tail",
}

function M.call_tool(name, args)
  local module_name = registry[name]
  if not module_name then
    return { ok = false, error = { code = "unknown_tool", message = name } }
  end

  local ok_load, tool_or_err = pcall(require, module_name)
  if not ok_load then
    return { ok = false, error = { code = "load_error", message = tostring(tool_or_err) } }
  end

  local ok_run, result_or_err = pcall(tool_or_err.run, args or {})
  if not ok_run then
    return { ok = false, error = { code = "tool_error", message = tostring(result_or_err) } }
  end

  return { ok = true, result = result_or_err }
end

return M
```

## Layer 2: Portable Lua Tool Layer

Layer 2 owns Neovim-specific tool behavior.

Responsibilities:

- implement debug/config workflows with Neovim Lua APIs;
- define compact parameter specs;
- be the source of truth for generated schemas;
- return JSON-safe values;
- run through Layer 1's remote runtime;
- ideally run directly inside Neovim as normal Lua modules.

Non-responsibilities:

- no MCP protocol;
- no Python packaging behavior;
- no worker transport protocol;
- no client-specific behavior.

Possible Lua tool authoring shape:

```lua
local tool = require("dotnvim_bridge.tool")

return tool.define({
  name = "get_lsp_snapshot",
  description = "Return active LSP clients and diagnostics.",
  params = {
    include_diagnostics = tool.boolean({
      default = true,
      description = "Include current diagnostics.",
    }),
  },
  run = function(args)
    local include_diagnostics = args.include_diagnostics ~= false

    local result = {
      clients = vim.tbl_map(function(c)
        return {
          id = c.id,
          name = c.name,
          root_dir = c.config and c.config.root_dir or nil,
          filetypes = c.config and c.config.filetypes or nil,
          attached_buffers = vim.tbl_keys(c.attached_buffers or {}),
        }
      end, vim.lsp.get_clients()),
      log_path = vim.lsp.get_log_path(),
    }

    if include_diagnostics then
      result.diagnostics = vim.diagnostic.get(nil)
    end

    return result
  end,
})
```

Direct Neovim execution should remain possible where practical:

```lua
local t = require("dotnvim_bridge.tools.get_lsp_snapshot")
print(vim.inspect(t.run({ include_diagnostics = true })))
```

## Layer 3: Python MCP Adapter

Layer 3 owns the MCP-facing protocol behavior.

Responsibilities:

- expose MCP tools;
- answer MCP `tools/list` from generated static schemas;
- receive MCP `tools/call` arguments;
- call Layer 1 via a narrow runtime interface;
- map runtime results/errors into MCP responses;
- manage CLI/package/server startup.

Non-responsibilities:

- no Neovim-specific workflow implementation;
- no direct `nvim_mcp` imports;
- no direct Lua business logic;
- no duplicated tool schemas where avoidable.

Layer 3 should not call Layer 2 directly. It should call Layer 1:

```text
MCP tools/call
  -> Layer 3 MCP adapter
  -> RuntimeClient.call_tool(name, args)
  -> Layer 1 runtime executes Layer 2 Lua tool
  -> Layer 2 returns result
  -> Layer 3 returns MCP response
```

## Schema generation and contract

The desired contract between Layer 2 and Layer 3 is generated static schema.

Preferred long-term shape:

```text
Lua tool compact spec
  -> schema generator
  -> generated/tool_schemas.json
  -> Python MCP adapter tools/list
```

The Lua tool layer remains the source of truth. Python should not manually duplicate descriptions, parameters, defaults, and schemas for each tool.

Potential generated metadata record:

```json
{
  "name": "get_lsp_snapshot",
  "description": "Return active LSP clients, diagnostics, and LSP log metadata.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "include_diagnostics": {
        "type": "boolean",
        "default": true
      }
    }
  },
  "source": {
    "kind": "package_lua_module",
    "module": "dotnvim_bridge.tools.get_lsp_snapshot",
    "path": "lua/dotnvim_bridge/tools/get_lsp_snapshot.lua"
  },
  "call": {
    "kind": "lua_tool",
    "module": "dotnvim_bridge.tools.get_lsp_snapshot",
    "function": "run"
  }
}
```

Layer usage:

```text
Layer 3:
  uses name / description / inputSchema for MCP tools/list
  uses call metadata to invoke RuntimeClient.call_tool(...)

Layer 1:
  uses call metadata to load/execute Lua tool modules

Source-inspection tools:
  use source metadata to show implementation files
```

Open questions:

- Should generated schema artifacts be committed or produced during package build?
- Should schema generation use standalone Lua, headless Neovim, or a constrained Python parser?
- Is output schema required or optional?
- How are schema versions tracked?
- Should Lua validate arguments at runtime using the same compact spec?

## Module loading strategy

Lua's standard module system uses `require` and `package`:

```text
require("module.name")
  -> checks package.loaded first
  -> asks package.searchers to find a loader
  -> runs the loader
  -> caches the returned module in package.loaded
```

Neovim extends this by making `lua/` directories on `runtimepath` available to `require`.

`dotnvim-bridge` should not require a persistent Neovim plugin install, so the relevant loading strategies are ephemeral.

### Option A: self-contained Lua chunk per call

Python builds one Lua chunk containing the needed helper/dispatcher/tool code and sends it through `nvim_exec_lua`.

Pros:

- stateless;
- easy to reason about;
- does not modify `package.loaded` or `package.preload`;
- always uses the packaged code from the current Python package.

Cons:

- sends more code per call;
- less like normal Lua module loading;
- shared helpers are less natural.

### Option B: inject modules with `package.preload`

Python registers packaged Lua modules as preload functions:

```lua
package.preload["dotnvim_bridge.tool"] = function()
  local M = {}
  return M
end

package.preload["dotnvim_bridge.tools.get_lsp_snapshot"] = function()
  local tool = require("dotnvim_bridge.tool")
  return tool.define({ ... })
end
```

Then dispatcher code can use normal `require`:

```lua
local mod = require("dotnvim_bridge.tools.get_lsp_snapshot")
return mod.run(args)
```

Pros:

- close to standard Lua plugin/module systems;
- shared helpers and registries are natural;
- repeated calls can be smaller;
- tools look like normal Lua modules.

Cons:

- creates remote Neovim runtime state;
- needs version/reload/reset behavior;
- bad cache state needs recovery;
- namespacing must avoid collisions.

### Option C: mutate `runtimepath` or `package.path`

This would make packaged Lua files discoverable through normal Neovim file lookup.

This is least attractive because the Python package may live in a container while Neovim lives on the host, and because it risks coupling the bridge to user runtimepath/config state.

### Current candidate preference

For a refactor path:

```text
Start with Option A for simplicity and statelessness.
Move to Option B if module reuse, performance, or direct Lua-module semantics become important.
Avoid Option C for the core bridge.
```

## Source, invocation, and tool surfaces

A strong long-term design should support three related surfaces.

### Source surface

Agent can inspect implementation source:

```text
list_packaged_lua_tools
read_packaged_lua_tool_source
list_remote_runtime_paths
find_remote_lua_module_source
read_remote_runtime_file
list_loaded_lua_modules
list_neovim_plugins
read_neovim_plugin_file
```

Two source categories matter:

1. packaged `dotnvim-bridge` Lua tool source;
2. remote Neovim/plugin/user config source.

Remote source discovery may use Neovim APIs such as:

```lua
vim.api.nvim_list_runtime_paths()
vim.api.nvim_get_runtime_file(...)
package.loaded
package.searchpath(...)
```

### Invocation surface

Agent or MCP adapter can invoke runtime capabilities:

```python
runtime.call_tool(name, args)
runtime.call_module_function(module_name, function_name, args)
runtime.eval(code, *args)
runtime.command(command)
runtime.read_buffer(name, start_line=None, end_line=None)
```

Not every invocation capability must become a public MCP product tool. General `eval_lua` may remain a debug/rescue primitive.

### Tool surface

Stable MCP-facing tools remain the product API:

```text
get_debug_snapshot
get_messages
get_logs_tail
get_lsp_snapshot
run_checkhealth
```

The tool surface should be generated from Layer 2 schemas rather than duplicated manually in Python.

## Process model: modular monolith vs worker split

The architecture has three logical layers. It does not necessarily need three processes immediately.

Candidate principle:

```text
Separate interfaces now.
Separate processes later only if needed.
```

### Candidate A: modular monolith first

Single Python process:

```text
MCP adapter
  -> RuntimeClient interface
  -> in-process RemoteNvimLuaRuntime
  -> nvim-mcp / remote Neovim
```

Benefits:

- less lifecycle complexity;
- easier testing/debugging;
- no internal JSON-line protocol yet;
- no subprocess crash/restart behavior;
- still preserves future extraction if Layer 3 depends only on a runtime interface.

Potential in-process module layout:

```text
src/dotnvim_bridge/
├── cli.py
├── mcp_server.py
├── runtime.py
├── session.py
├── tool_registry.py
├── generated/
│   └── tool_schemas.json
└── lua/
    └── dotnvim_bridge/
        ├── tool.lua
        ├── dispatcher.lua
        └── tools/
```

### Candidate B: separate runtime worker process

Two Python processes:

```text
MCP adapter process
  -> thin internal protocol
  -> runtime worker process
  -> nvim-mcp / remote Neovim
```

Minimal internal protocol:

```text
call_tool(name, arguments) -> result | error
```

Example request:

```json
{
  "id": "1",
  "method": "call_tool",
  "params": {
    "name": "get_lsp_snapshot",
    "arguments": { "include_diagnostics": true }
  }
}
```

Example response:

```json
{
  "id": "1",
  "ok": true,
  "result": { "clients": [], "diagnostics": [] }
}
```

Benefits:

- clear process isolation;
- MCP adapter does not own Neovim connection state;
- runtime worker could later become long-lived or shared.

Costs:

- subprocess lifecycle;
- framing/protocol versioning;
- request ids;
- timeout propagation;
- split logs;
- cleanup in tests;
- more packaging complexity.

Current candidate preference is **modular monolith first**, with a runtime interface that could later be implemented by a worker client.

## Relationship to common Lua plugin systems

Common Lua plugin systems generally have:

```text
host runtime
host API exposed into Lua
module loader
plugin contract
lifecycle/dispatcher
metadata/schema
```

Examples:

- Neovim exposes `vim.*`, loads Lua modules from `runtimepath`, and uses `require`.
- Kong Lua plugins return tables with known lifecycle functions and have schemas.
- Game/mod systems expose game APIs, load scripts from manifests/directories, and call known hooks/events.

The candidate `dotnvim-bridge` model is similar:

```text
remote Neovim runtime
  -> loader/dispatcher support
  -> Lua tool contract/helper
  -> Lua tool modules
  -> generated schema metadata
  -> Python MCP adapter
```

The key difference is that `dotnvim-bridge` should keep its Lua tools packaged with the Python distribution and load them ephemerally, not require persistent installation into the user's Neovim config.

## Open questions

Before turning this into a real OpenSpec proposal, resolve:

1. What is the first refactor target: self-contained chunks or `package.preload` module injection?
2. How exactly are static schemas generated from Lua compact specs?
3. Are generated schemas committed or built during packaging?
4. Which source-surface tools are MVP-worthy?
5. Should `call_lua_module_function` be public or internal-only?
6. How should Lua structured errors map into MCP responses?
7. How should direct Neovim execution of packaged tools be tested?
8. Should runtime worker extraction be explicitly postponed?
9. How should schema/call/source metadata be versioned?
10. Can generated metadata also drive documentation generation?

## Current non-decision

This document is a candidate architecture note only.

Current MVP remains the Python wrapper described in `docs/architecture.md`.

If this candidate direction is adopted, create a new OpenSpec change that states:

- three logical layers;
- generated static schemas from Lua tool definitions;
- Layer 3 calls Layer 1, not Layer 2 directly;
- Layer 1 executes Layer 2 tools in the real remote Neovim Lua runtime;
- process split is optional and should probably follow a modular monolith first approach;
- current Python-held snippets should be migrated toward packaged Lua tools.
