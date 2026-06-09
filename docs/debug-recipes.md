# nvim-mcp Debug Recipes

Reusable workflows for debugging Neovim configuration through `nvim-mcp`.

These recipes intentionally use only confirmed `nvim-mcp` tools:

- `get_state_brief`
- `get_state`
- `get_all_diagnostics`
- `read_buf_range`
- `read_full_buf`
- `send_command`
- `write_full_buf`

## 1. General debug snapshot

Use when starting a Neovim config debugging turn.

Tool sequence:

```text
1. get_state_brief
2. get_all_diagnostics
3. send_command("messages")
4. send_command("lua print(vim.json.encode(...))")
```

Lua payload:

```vim
lua print(vim.json.encode({
  version = vim.version(),
  cwd = vim.fn.getcwd(),
  paths = {
    config = vim.fn.stdpath('config'),
    state = vim.fn.stdpath('state'),
    log = vim.fn.stdpath('log'),
    data = vim.fn.stdpath('data'),
    cache = vim.fn.stdpath('cache'),
  },
  buffers = vim.tbl_map(function(buf)
    return {
      bufnr = buf,
      name = vim.api.nvim_buf_get_name(buf),
      loaded = vim.api.nvim_buf_is_loaded(buf),
      listed = vim.bo[buf].buflisted,
      filetype = vim.bo[buf].filetype,
      buftype = vim.bo[buf].buftype,
      modified = vim.bo[buf].modified,
    }
  end, vim.api.nvim_list_bufs()),
  lsp_clients = vim.tbl_map(function(c)
    return {
      id = c.id,
      name = c.name,
      root_dir = c.config and c.config.root_dir or nil,
      filetypes = c.config and c.config.filetypes or nil,
    }
  end, vim.lsp.get_clients()),
  diagnostics_count = #vim.diagnostic.get(nil),
}))
```

## 2. Messages

Use when something failed silently or a plugin emitted errors.

```text
send_command("messages")
```

If messages are noisy, ask for a more focused action first, reproduce the issue, then call `messages` again.

## 3. Checkhealth

Use for subsystem health checks.

Tool sequence:

```text
1. send_command("checkhealth <topic>")
2. get_state_brief
3. read_buf_range("health://", 1, 300)
```

Examples:

```text
send_command("checkhealth vim.lsp")
send_command("checkhealth provider")
send_command("checkhealth lazy")
send_command("checkhealth nvim-treesitter")
```

Note: `checkhealth` usually writes the useful output into the `health://` buffer; the direct command output may only show progress.

## 4. Logs tail

Use when `:messages` is insufficient.

```vim
lua local function tail(path, n)
  if vim.fn.filereadable(path) ~= 1 then
    return { path = path, readable = false, tail = {} }
  end
  local lines = vim.fn.readfile(path)
  local start = math.max(1, #lines - n + 1)
  local out = {}
  for i = start, #lines do table.insert(out, lines[i]) end
  return { path = path, readable = true, tail = out }
end
print(vim.json.encode({
  nvim_log = tail(vim.fn.stdpath('log') .. '/nvim.log', 120),
  lsp_log = tail(vim.fn.stdpath('state') .. '/lsp.log', 120),
}))
```

Run via:

```text
send_command("lua <payload>")
```

## 5. LSP snapshot

Use when LSP is not attaching, diagnostics are missing, or completion behaves oddly.

Tool sequence:

```text
1. get_all_diagnostics
2. send_command("lua print(vim.json.encode(...))")
```

Lua payload:

```vim
lua print(vim.json.encode({
  clients = vim.tbl_map(function(c)
    return {
      id = c.id,
      name = c.name,
      root_dir = c.config and c.config.root_dir or nil,
      filetypes = c.config and c.config.filetypes or nil,
      cmd = c.config and c.config.cmd or nil,
      attached_buffers = vim.tbl_keys(c.attached_buffers or {}),
    }
  end, vim.lsp.get_clients()),
  diagnostics = vim.tbl_map(function(d)
    return {
      bufnr = d.bufnr,
      lnum = d.lnum,
      col = d.col,
      severity = d.severity,
      source = d.source,
      message = d.message,
    }
  end, vim.diagnostic.get(nil)),
  log_path = vim.lsp.get_log_path(),
}))
```

## 6. Plugin snapshot: lazy.nvim

Use when debugging plugin loading or startup state.

```vim
lua local result = { available = false, manager = nil }
local ok_lazy, lazy = pcall(require, 'lazy')
if ok_lazy then
  result.available = true
  result.manager = 'lazy.nvim'
  local ok_stats, stats = pcall(lazy.stats)
  if ok_stats then result.stats = stats end
  local ok_config, config = pcall(require, 'lazy.core.config')
  if ok_config then
    result.plugins = vim.tbl_map(function(name)
      local p = config.plugins[name]
      return {
        name = name,
        url = p.url,
        dir = p.dir,
        enabled = p.enabled,
        lazy = p.lazy,
        loaded = p._ and p._.loaded or false,
      }
    end, vim.tbl_keys(config.plugins))
  end
end
print(vim.json.encode(result))
```

## 7. Create a scratch debug buffer

Use when the agent should show a structured report inside Neovim without writing a file.

Tool sequence:

```text
1. send_command(["enew", "file mcp-debug.md", "setlocal buftype=nofile bufhidden=wipe noswapfile filetype=markdown"])
2. write_full_buf("mcp-debug.md", rendered_markdown)
```

Example report shape:

```markdown
# Neovim Debug Snapshot

## State
...

## Diagnostics
...

## Messages
...

## Suggested next actions
...
```

## 8. Safe edit workflow

Use when modifying config or an open file.

```text
1. get_state_brief
2. read_full_buf or read_buf_range
3. explain the intended change
4. find_and_replace_buf for targeted edits, or write_full_buf only when rewriting is intentional
5. get_state_brief to confirm modified buffer
6. do not save unless requested
```

## 9. Avoid by default

Avoid unless explicitly requested:

```text
send_command(":!...")
send_command("w")
send_command("qa!")
send_keys for complex edits
```

Reason: `send_command` is powerful enough to execute host shell commands and save/quit buffers.
