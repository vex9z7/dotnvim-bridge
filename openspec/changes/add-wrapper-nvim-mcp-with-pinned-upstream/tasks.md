## 1. Package Scaffold

- [x] 1.1 Use `dotnvim-bridge` as the final wrapper distribution and command name, with `dotnvim_bridge` as the Python import package.
- [ ] 1.2 Add Python package metadata for the wrapper MCP package.
- [ ] 1.3 Pin upstream dependency to `nvim-mcp==1.0.0`.
- [ ] 1.4 Record upstream repository `https://github.com/paulburgess1357/nvim-mcp` and commit `db73c3706c466a0f7740b693c3a23ea426287b97` in package/docs metadata.
- [ ] 1.5 Add a wrapper console script entrypoint.

## 2. Adapter Layer

- [ ] 2.1 Create a `session.py` adapter that owns all imports from upstream `nvim-mcp`.
- [ ] 2.2 Implement connection reuse through the existing `NVIM_ADDRESS` environment contract.
- [ ] 2.3 Add helper methods for state, diagnostics, command output, Lua execution, buffer reads, and bounded text responses.
- [ ] 2.4 Ensure adapter code can be replaced later without changing public tool implementations.

## 3. High-Level MCP Tools

- [ ] 3.1 Implement `get_debug_snapshot` with editor state, buffers, diagnostics, messages summary, paths, LSP summary, and log availability.
- [ ] 3.2 Implement `get_messages` with bounded `:messages` collection.
- [ ] 3.3 Implement `get_logs_tail` with bounded tails for `nvim.log` and `lsp.log` where available.
- [ ] 3.4 Implement `get_lsp_snapshot` with clients, buffer associations, diagnostic counts, and log metadata.
- [ ] 3.5 Implement `run_checkhealth` with optional topic and bounded health buffer readback.

## 4. Safety and Limits

- [ ] 4.1 Ensure first-batch wrapper tools do not save buffers, quit Neovim, or invoke host shell commands.
- [ ] 4.2 Add default line/byte limits for messages, logs, and health output.
- [ ] 4.3 Return structured errors when Neovim is unreachable or an upstream call fails.

## 5. Tests and Validation

- [ ] 5.1 Add unit tests for each high-level tool using mocked adapter responses.
- [ ] 5.2 Add tests that verify the upstream dependency is pinned to `nvim-mcp==1.0.0`.
- [ ] 5.3 Add an optional integration test path against a live Neovim `--listen` endpoint.
- [ ] 5.4 Run local validation against `NVIM_ADDRESS=vex9z7.com:16667` when the host Neovim instance is available.

## 6. Documentation and Codex Config

- [ ] 6.1 Document direct upstream mode versus wrapper mode.
- [ ] 6.2 Add a Codex MCP config example for launching the wrapper with `NVIM_ADDRESS=vex9z7.com:16667`.
- [ ] 6.3 Document rollback to direct `uvx nvim-mcp` mode.
- [ ] 6.4 Document the future upgrade process for moving beyond upstream commit `db73c3706c466a0f7740b693c3a23ea426287b97`.
