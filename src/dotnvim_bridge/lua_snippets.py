"""Ephemeral Neovim Lua snippets used by high-level tools."""

from __future__ import annotations

LOGS_TAIL = r"""
local max_lines = ...
local function tail(path, n)
  if vim.fn.filereadable(path) ~= 1 then
    return { path = path, readable = false, tail = {}, line_count = 0, truncated = false }
  end
  local lines = vim.fn.readfile(path)
  local start = math.max(1, #lines - n + 1)
  local out = {}
  for i = start, #lines do table.insert(out, lines[i]) end
  return { path = path, readable = true, tail = out, line_count = #lines, truncated = start > 1 }
end
return {
  nvim_log = tail(vim.fn.stdpath('log') .. '/nvim.log', max_lines),
  lsp_log = tail(vim.fn.stdpath('state') .. '/lsp.log', max_lines),
}
"""

LSP_SNAPSHOT = r"""
local include_diagnostics = ...
local clients = vim.tbl_map(function(c)
  return {
    id = c.id,
    name = c.name,
    root_dir = c.config and c.config.root_dir or nil,
    filetypes = c.config and c.config.filetypes or nil,
    cmd = c.config and c.config.cmd or nil,
    attached_buffers = vim.tbl_keys(c.attached_buffers or {}),
  }
end, vim.lsp.get_clients())
local result = {
  clients = clients,
  log_path = vim.lsp.get_log_path(),
  log_level = vim.lsp.log and vim.lsp.log.get_level and vim.lsp.log.get_level() or nil,
}
if include_diagnostics then
  result.diagnostics = vim.tbl_map(function(d)
    return {
      bufnr = d.bufnr,
      lnum = d.lnum,
      col = d.col,
      severity = d.severity,
      source = d.source,
      message = d.message,
    }
  end, vim.diagnostic.get(nil))
end
return result
"""

RUNTIME_SNAPSHOT = r"""
return {
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
}
"""
