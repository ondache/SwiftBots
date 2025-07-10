test:
	uv run pytest --stepwise --quiet --no-header --color=yes --code-highlight=yes tests

ruff:
	uv run ruff check .

mypy:
	uv run mypy

black:
	uv run black --check -t py39 --diff --color .

check:
	uv run ruff check --statistics --exit-zero .
	uv run pytest --stepwise-skip --quiet --no-header --no-summary --color=yes --code-highlight=yes tests
	uv run mypy --no-pretty

build:
	uv sync --quiet
	uv export -o pylock.toml --quiet
	uv build --quiet