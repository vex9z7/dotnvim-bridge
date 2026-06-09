# Setup: Codex CLI to Host Neovim via nvim-mcp

This is the confirmed route.

```text
Codex CLI inside container
  -> MCP server: uvx nvim-mcp
  -> NVIM_ADDRESS=vex9z7.com:16667
  -> NPM Stream TCP 16667
  -> host Neovim --listen 0.0.0.0:16667
```

## 1. Host side

Start Neovim with a TCP listener:

```bash
nvim --listen 0.0.0.0:16667 ~/.config/nvim
```

For a test file:

```bash
nvim --listen 0.0.0.0:16667 ~/hello.cpp
```

Verify on the host running Neovim:

```bash
ss -ltnp | grep 16667
```

## 2. NPM Stream side

Nginx Proxy Manager must use **Streams**, not Proxy Hosts.

Confirmed shape:

```text
Incoming Port: 16667
Forward Host: <Neovim host, e.g. mac-mini.internal>
Forward Port: 16667
TCP: enabled
UDP: optional/off preferred
SSL: off
```

The NPM container/app must expose the stream port:

```text
host 16667/tcp -> container 16667/tcp
```

The generated stream config should use raw TCP:

```nginx
server {
  listen 16667;
  proxy_pass mac-mini.internal:16667;
}
```

It must not use:

```nginx
listen 16667 ssl;
```

## 3. Container / agent side

The confirmed stable endpoint is:

```bash
export NVIM_ADDRESS=vex9z7.com:16667
```

Smoke-test the endpoint:

```bash
NVIM_ADDRESS=vex9z7.com:16667 ./scripts/test-nvim-mcp-endpoint
```

A stronger raw RPC test should return the Neovim cwd:

```text
/home/vex9z7
```

## 4. Codex CLI MCP config

Configured with:

```bash
codex mcp add nvim-mcp \
  --env NVIM_ADDRESS=vex9z7.com:16667 \
  -- uvx nvim-mcp
```

Equivalent TOML:

```toml
[mcp_servers.nvim-mcp]
command = "uvx"
args = ["nvim-mcp"]

[mcp_servers.nvim-mcp.env]
NVIM_ADDRESS = "vex9z7.com:16667"
```

Check:

```bash
codex mcp list
codex mcp get nvim-mcp
```

After changing MCP config, start a new Codex session.

## 5. End-to-end validation

In a new Codex session, ask:

```text
Use nvim-mcp to inspect my running Neovim instance. Report cwd, active buffer, cursor position, and diagnostics summary.
```

Confirmed live result:

```text
cwd: /home/vex9z7
active buffer: hello.cpp
filetype: cpp
nvim version: v0.12.2
diagnostics: []
```

## 6. Notes

- Neovim does not need a plugin for this route.
- `nvim-mcp` connects through Neovim's native msgpack-RPC endpoint.
- Stream endpoints are `host:port`, not `https://...` URLs.
- `send_command` can run arbitrary Ex commands, including `:lua ...` and `:!cmd`; treat this as privileged host access through Neovim.
