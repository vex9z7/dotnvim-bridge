## ADDED Requirements


### Requirement: MVP is publishable as a Python package
The system SHALL produce an installable Python distribution named `dotnvim-bridge` with a console command named `dotnvim-bridge`.

#### Scenario: Package exposes a runnable MCP server
- **WHEN** the package is installed in a Python environment
- **THEN** the `dotnvim-bridge` command is available
- **AND** running the command starts the wrapper MCP server

#### Scenario: MVP implementation remains intentionally thin
- **WHEN** a low-level behavior is already handled by pinned upstream `nvim-mcp==1.0.0`
- **THEN** the MVP delegates that behavior rather than reimplementing it locally
- **AND** local implementation focuses on adapter boundaries, limits, error normalization, schemas, and high-level tool workflows

### Requirement: Wrapper MCP server uses pinned upstream nvim-mcp
The system SHALL provide a first-party wrapper MCP server that depends on upstream `nvim-mcp==1.0.0` and records the corresponding upstream repository commit `db73c3706c466a0f7740b693c3a23ea426287b97` as the source-code reference baseline.

#### Scenario: Dependency is installed reproducibly
- **WHEN** the wrapper package dependencies are installed
- **THEN** the dependency resolver uses `nvim-mcp==1.0.0` rather than an unbounded or floating `nvim-mcp` version

#### Scenario: Upstream source reference is available
- **WHEN** a maintainer investigates wrapper behavior or prepares an upstream upgrade
- **THEN** the project documentation identifies `https://github.com/paulburgess1357/nvim-mcp` commit `db73c3706c466a0f7740b693c3a23ea426287b97` as the inspected baseline

### Requirement: Wrapper MCP server uses the documented Python package layout
The system SHALL implement the wrapper as Python distribution `dotnvim-bridge` with console command `dotnvim-bridge` and import package `dotnvim_bridge` under `src/`.

#### Scenario: Package layout is scaffolded
- **WHEN** the implementation scaffold is created
- **THEN** repository code intended for import lives under `src/dotnvim_bridge/`
- **AND** MCP registration is owned by `src/dotnvim_bridge/server.py`
- **AND** upstream `nvim_mcp` internals are isolated behind `src/dotnvim_bridge/session.py`
- **AND** first-batch high-level tool implementations live under `src/dotnvim_bridge/tools/`

#### Scenario: Tool modules remain decoupled from upstream internals
- **WHEN** a high-level tool module such as `tools/messages.py` or `tools/lsp.py` is implemented
- **THEN** it uses the local session adapter rather than importing upstream `nvim_mcp` internals directly


### Requirement: MVP delegates low-level Neovim communication to pinned upstream nvim-mcp
The system SHALL maximize reuse of pinned upstream `nvim-mcp==1.0.0` for low-level Neovim communication primitives during the MVP while keeping those imports isolated behind the local session adapter.

#### Scenario: Communication layer remains thin
- **WHEN** the MVP implements connection, command execution, Lua execution, state collection, diagnostics, or buffer reads
- **THEN** it delegates to upstream `nvim-mcp` primitives where practical
- **AND** local code only adapts inputs/outputs, applies limits, normalizes errors, and preserves the future replacement seam

#### Scenario: Product behavior lives in high-level tools
- **WHEN** a high-level workflow such as `get_debug_snapshot`, `get_logs_tail`, or `run_checkhealth` is implemented
- **THEN** the workflow logic lives in `src/dotnvim_bridge/tools/` or shared local helper modules
- **AND** it does not expand the communication/session layer beyond stable adapter responsibilities

### Requirement: Wrapper MCP server preserves existing Neovim connection model
The system SHALL use the same `NVIM_ADDRESS`-driven connection model as upstream `nvim-mcp` so the existing container-to-host TCP topology continues to work.

#### Scenario: Wrapper connects through existing endpoint
- **WHEN** the wrapper MCP server starts with `NVIM_ADDRESS=vex9z7.com:16667`
- **THEN** it connects to the host Neovim instance through the same raw msgpack-RPC TCP endpoint used by upstream `nvim-mcp`

#### Scenario: Host-side setup remains unchanged
- **WHEN** the wrapper MCP server replaces direct `uvx nvim-mcp` usage in Codex config
- **THEN** the host Neovim instance still only needs to listen on the configured TCP address and does not require a Neovim plugin

### Requirement: Wrapper MCP server exposes high-level debug tools
The system SHALL expose high-level MCP tools for common Neovim config-debug workflows while internally composing upstream `nvim-mcp` manager/client operations and Neovim Lua snippets.

#### Scenario: Agent requests a general debug snapshot
- **WHEN** the agent calls `get_debug_snapshot`
- **THEN** the wrapper returns a structured summary containing editor state, current buffers, diagnostics, messages summary, relevant paths, LSP summary, and log availability where available

#### Scenario: Agent requests messages
- **WHEN** the agent calls `get_messages`
- **THEN** the wrapper returns recent `:messages` output in a structured response without requiring the agent to manually call `send_command("messages")`

#### Scenario: Agent requests log tails
- **WHEN** the agent calls `get_logs_tail`
- **THEN** the wrapper returns bounded tails for known Neovim logs such as `nvim.log` and `lsp.log` when those files exist

#### Scenario: Agent requests LSP state
- **WHEN** the agent calls `get_lsp_snapshot`
- **THEN** the wrapper returns attached LSP clients, buffer associations, diagnostics counts, and relevant LSP log metadata in JSON-safe fields

#### Scenario: Agent requests health output
- **WHEN** the agent calls `run_checkhealth` with an optional topic
- **THEN** the wrapper runs the corresponding `:checkhealth` flow and returns the resulting health buffer content in a bounded structured response

### Requirement: Wrapper MCP server defaults to inspect-first behavior
The system SHALL make the high-level debug tools read-oriented by default and avoid saving files, quitting Neovim, or executing host shell commands unless a future explicitly-mutating tool is designed for that purpose.

#### Scenario: Debug snapshot is collected safely
- **WHEN** the agent calls any first-batch high-level debug tool
- **THEN** the wrapper collects editor state without writing buffers to disk, closing windows, quitting Neovim, or invoking shell commands through `:!`

### Requirement: Wrapper MCP server can be swapped in from Codex config
The system SHALL provide installation and Codex MCP configuration instructions that allow replacing direct `uvx nvim-mcp` usage with the wrapper command while preserving the existing environment variable contract.

#### Scenario: Codex config is updated to wrapper mode
- **WHEN** the user updates Codex MCP config from direct upstream mode to wrapper mode
- **THEN** the config keeps `NVIM_ADDRESS` and changes only the command/args needed to launch the wrapper MCP server
