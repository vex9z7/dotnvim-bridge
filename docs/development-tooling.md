# Development Tooling

Date: 2026-06-10
Status: current MVP development toolchain

This document records the development toolchain used by the current `dotnvim-bridge` MVP package scaffold.

## Goals

The toolchain should keep the MVP simple while still protecting the architecture decisions that matter:

- use `uv` for environment, dependency, lockfile, and command execution;
- keep all package/tool configuration in `pyproject.toml` where practical;
- make formatting, linting, typing, and tests easy to run locally;
- support MCP server development with MCP Inspector / `mcp dev`;
- avoid adding heavyweight guardrail tools before there is enough implementation code to justify them;
- leave a clear path to add import-boundary and architecture checks later.

## Community baseline

Modern Python MCP/server projects commonly use:

- `uv` for project, virtualenv, lockfile, and command execution;
- `pyproject.toml` as the central Python project configuration file;
- `ruff` for formatting, import sorting, and linting;
- `pytest` for unit tests;
- `pytest-asyncio` for async MCP/session tests;
- `pytest-cov` for coverage reporting;
- `pyright` or `basedpyright` for static type checking;
- `pre-commit` for local pre-commit checks;
- `mcp[cli]` and MCP Inspector for server development/debugging.

## Decisions

### Decision 1: Use `uv` as the project runner and dependency manager

Use `uv` for:

- creating/syncing the virtual environment;
- generating and updating `uv.lock`;
- running developer commands;
- launching MCP development workflows.

Expected commands:

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run mcp dev src/dotnvim_bridge/server.py
```

Alternative considered: `pip` + `venv` + ad-hoc scripts. Rejected because `uv` gives a single fast workflow for locking, syncing, and running tools.

### Decision 2: Use `hatchling` as the build backend

Use `hatchling`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Rationale:

- it is lightweight;
- it works cleanly with `src/` layout;
- the pinned upstream `nvim-mcp` package also uses `hatchling`, so package behavior stays familiar.

### Decision 3: Use `ruff` for formatting, linting, and import sorting

Use one tool instead of separate Black, isort, flake8, pyupgrade, and bugbear setup.

Initial policy:

```toml
[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
```

Rationale:

- `E` / `F` cover pycodestyle and Pyflakes basics;
- `I` sorts imports;
- `UP` modernizes Python syntax;
- `B` catches common bug patterns;
- `E501` is ignored because line length is better handled by the formatter and occasional long strings/Lua snippets are expected.

### Decision 4: Use `pytest` plus async and coverage plugins

Use:

```toml
[dependency-groups]
dev = [
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
]
```

Rationale:

- high-level MCP tools and session adapter methods are async;
- mocked unit tests should be the default path;
- coverage should be available without making every test run verbose.

Live Neovim integration tests should be optional and environment-gated:

```bash
NVIM_ADDRESS=vex9z7.com:16667 RUN_LIVE_NVIM_TESTS=1 uv run pytest
```

### Decision 5: Use `basedpyright` for type checking

Use `basedpyright` as the static type checker:

```toml
[dependency-groups]
dev = [
    "basedpyright",
]
```

Rationale:

- it can be installed and pinned as a normal Python dev dependency;
- it avoids requiring Node/npm for type checking;
- it is a good fit for a `uv`-managed Python project.

Policy:

- include `src` and `tests`;
- start stricter for `src/dotnvim_bridge` than for tests;
- keep any upstream `nvim_mcp` typing workarounds in `session.py`;
- do not let type-checker pressure leak upstream internals into tool modules.

Alternative considered: `mypy`. Rejected for the MVP to avoid running two type checkers.

Alternative considered: npm-based `pyright`. Rejected because `basedpyright` keeps the project Python/uv-native.

### Decision 6: Use `pre-commit` for local hygiene

Use `pre-commit` to run cheap checks before commits.

Initial hooks should cover:

- Ruff format/check;
- trailing whitespace / end-of-file checks;
- optionally `pytest` later if it stays fast.

Do not make expensive live Neovim integration tests part of pre-commit.

### Decision 7: Use `mcp[cli]` for server development

Runtime dependencies should include:

```toml
dependencies = [
    "nvim-mcp==1.0.0",
    "mcp[cli]",
]
```

Rationale:

- `nvim-mcp==1.0.0` is the pinned MVP communication/control dependency;
- `mcp[cli]` provides FastMCP and development commands such as `mcp dev`.

Expected development command:

```bash
uv run mcp dev src/dotnvim_bridge/server.py --with-editable .
```

### Decision 8: Add a small `Makefile` for common workflows

Use a small `Makefile` as a convenience wrapper around `uv run` commands.

Planned targets:

```make
.PHONY: format lint type test coverage mcp-dev check

format:
	uv run ruff format .
	uv run ruff check . --fix

lint:
	uv run ruff check .

type:
	uv run basedpyright

test:
	uv run pytest

coverage:
	uv run pytest --cov=dotnvim_bridge

mcp-dev:
	uv run mcp dev src/dotnvim_bridge/server.py --with-editable .

check: lint type test
```

Rationale:

- keeps common commands discoverable;
- avoids complex task runners for the MVP;
- remains transparent because each target is just a `uv run ...` command.

### Decision 9: Defer heavyweight architecture guardrails

Do not add these tools to the MVP dev dependency group yet:

| Tool | Defer reason |
|---|---|
| `import-linter` | Useful once internal package boundaries are real; premature before implementation modules exist. |
| `semgrep` | Useful for project-specific architecture rules; add after there are concrete patterns to enforce. |
| `vulture` | Useful after there is enough code for dead-code checks to be meaningful. |
| `tox` / `nox` | Not needed while `uv run` plus CI covers the MVP. |
| `mypy` | Avoid duplicate type checkers; use `basedpyright` first. |

Future guardrails to consider after implementation starts:

- import-boundary check: only `dotnvim_bridge.session` may import `nvim_mcp`;
- Semgrep rule: forbid `from nvim_mcp...` outside `src/dotnvim_bridge/session.py`;
- high-confidence dead-code check;
- OpenSpec validation as part of `make check`.

## Dependency plan

Runtime dependencies:

```toml
dependencies = [
    "nvim-mcp==1.0.0",
    "mcp[cli]",
]
```

Dev dependencies:

```toml
[dependency-groups]
dev = [
    "basedpyright",
    "pre-commit",
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "ruff",
]
```

## Local workflow

```bash
uv sync --dev
uv run ruff format .
uv run ruff check .
uv run basedpyright
uv run pytest
uv run pytest --cov=dotnvim_bridge
uv run mcp dev src/dotnvim_bridge/server.py --with-editable .
```
