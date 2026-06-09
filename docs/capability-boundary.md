# nvim-mcp Capability Boundary Test

Date: 2026-06-05

Endpoint:

```text
NVIM_ADDRESS=vex9z7.com:16667
```

Current Neovim:

```text
cwd: /home/vex9z7
active file: hello.cpp
nvim: v0.12.2
```

## 1. Summary

`paulburgess1357/nvim-mcp` is sufficient for the core config-iteration workflow.

It can:

- inspect editor state;
- read buffers;
- edit buffers in memory;
- query diagnostics;
- execute Ex commands;
- execute Lua via `:lua ...`;
- run `:checkhealth` and read the generated health buffer;
- read Neovim logs via Lua/readfile;
- send normal-mode keystrokes;
- add/clear highlights and virtual text;
- execute shell commands through `:!cmd` on the host, because `send_command` can run arbitrary Ex commands.

Important: this is powerful enough for debugging, but it means `nvim-mcp` should be treated as a privileged bridge into the host Neovim process.

## 2. Tools observed

Key tools used:

- `get_state`
- `get_state_brief`
- `read_full_buf`
- `read_buf_range`
- `get_all_diagnostics`
- `get_buf_diagnostics`
- `find_and_replace_buf`
- `write_full_buf`
- `send_command`
- `send_keys`
- `highlight_range`
- `add_virtual_text`
- `clear_highlights`
- `clear_virtual_texts`

## 3. State and buffer inspection

`get_state` succeeded and returned:

```text
cwd: /home/vex9z7
buffer: hello.cpp
filetype: cpp
line: 1
content context: #include <cstdio>
modified_buffers: hello.cpp
```

`read_full_buf("hello.cpp")` returned:

```cpp
#include <cstdio>
```

## 4. Diagnostics

`get_all_diagnostics()` returned:

```json
[]
```

No active diagnostics in the current minimal setup.

## 5. Ex command execution

`send_command` can run ordinary Ex commands and capture output.

Validated:

```vim
:pwd
:version
:messages
```

Results included:

```text
/home/vex9z7
NVIM v0.12.2
hello from Codex via raw nvim RPC
```

Invalid commands return structured errors:

```text
nvim_exec2(), line 1: Vim:E492: Not an editor command: ThisCommandDoesNotExist
```

## 6. Lua execution

Lua execution works through `send_command("lua ...")`.

Validated:

```vim
:lua print(vim.json.encode({
  cwd = vim.fn.getcwd(),
  config = vim.fn.stdpath('config'),
  state = vim.fn.stdpath('state'),
  log = vim.fn.stdpath('log'),
  clients = vim.tbl_map(function(c)
    return { id = c.id, name = c.name }
  end, vim.lsp.get_clients())
}))
```

Returned:

```json
{
  "cwd": "/home/vex9z7",
  "config": "/home/vex9z7/.config/nvim",
  "state": "/home/vex9z7/.local/state/nvim",
  "log": "/home/vex9z7/.local/state/nvim",
  "clients": []
}
```

This is enough to query arbitrary Neovim runtime state.

## 7. Logs

Neovim logs can be read through Lua/readfile.

Validated:

```vim
:lua local p=vim.fn.stdpath('log')..'/nvim.log'; print(vim.json.encode({
  path = p,
  readable = vim.fn.filereadable(p),
  tail = vim.fn.readfile(p, '', 5),
}))
```

Returned:

```text
path: /home/vex9z7/.local/state/nvim/nvim.log
readable: 1
```

So even though there is no dedicated `get_nvim_log` tool, `send_command` + Lua covers it.

## 8. Checkhealth

`send_command("checkhealth vim.lsp")` ran successfully.

The command output itself was mostly progress:

```text
checkhealth: 100% checking vim.lsp
checkhealth: checks done
```

But it opened a `health://` buffer, which `nvim-mcp` can read.

`read_buf_range("health://", 1, 40)` returned useful health output:

```text
vim.lsp: ✅
- LSP log level : WARN
- Log path: /home/vex9z7/.local/state/nvim/lsp.log
- Log size: 0 KB
- No active clients
```

This means config debug workflows can run `:checkhealth` and then inspect the generated health buffer.

## 9. Temporary debug buffers

Created a nofile scratch buffer via:

```vim
:enew
:file mcp-debug.md
:setlocal buftype=nofile bufhidden=wipe noswapfile filetype=markdown
```

Then wrote content via `write_full_buf("mcp-debug.md", ...)`.

State showed:

```text
file: mcp-debug.md
buftype: nofile
filetype: markdown
modified: false
```

This is useful for surfacing debug snapshots inside Neovim without writing to disk.

## 10. Annotations

Validated:

- `add_virtual_text`
- `highlight_range`
- `clear_virtual_texts`
- `clear_highlights`

These are useful for annotating suspicious lines or debug findings visually.

## 11. Keystrokes

`send_keys("G")` moved the cursor to the bottom of the current buffer.

This means normal-mode navigation and edits are possible, but structured edit tools should be preferred for file content changes.

## 12. Host shell execution boundary

Because `send_command` can run arbitrary Ex commands, it can also run shell commands with `:!`.

Validated harmlessly:

```vim
:!printf nvim-mcp-shell-ok
```

Returned:

```text
nvim-mcp-shell-ok
```

This means `nvim-mcp` is not merely an editor-state reader. It can become host command execution via Neovim.

For our own workflow this is acceptable if treated as trusted/local, but it should be documented clearly.

## 13. Fit for Neovim config iteration

Sufficient for:

- inspecting current Neovim context;
- reading and editing open buffers;
- running `:messages`;
- running `:checkhealth` and reading `health://`;
- querying LSP clients via Lua;
- reading `nvim.log` / `lsp.log` via Lua/readfile;
- creating scratch debug buffers;
- annotating buffers;
- executing temporary Lua snippets;
- testing config mutations at runtime.

Main limitations:

- no dedicated high-level `get_logs` / `get_lsp_clients` / `get_checkhealth` tools;
- high-level debug workflows need to be encoded as `send_command("lua ...")` snippets;
- command output can be less structured unless we print JSON from Lua;
- it is powerful enough to run host shell commands, so prompts/rules should treat it as privileged.

## 14. Recommended workflow

Use `nvim-mcp` as the main Neovim integration.

Prefer this pattern:

```text
1. get_state_brief
2. get_all_diagnostics
3. send_command("messages")
4. send_command("checkhealth <topic>")
5. read_buf_range("health://", ...)
6. send_command("lua print(vim.json.encode(...))") for structured runtime info
7. read/edit buffers only after explaining the plan
```

For structured debug queries, use Lua that prints JSON, e.g.:

```vim
:lua print(vim.json.encode({
  clients = vim.tbl_map(function(c)
    return { id = c.id, name = c.name, root_dir = c.config.root_dir }
  end, vim.lsp.get_clients()),
  diagnostics = vim.diagnostic.get(nil),
  paths = {
    config = vim.fn.stdpath('config'),
    state = vim.fn.stdpath('state'),
    log = vim.fn.stdpath('log'),
  },
}))
```

