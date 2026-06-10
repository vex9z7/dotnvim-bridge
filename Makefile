.PHONY: format lint type test coverage build mcp-dev check

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

build:
	uv build

mcp-dev:
	uv run mcp dev src/dotnvim_bridge/server.py --with-editable .

check: lint type test
