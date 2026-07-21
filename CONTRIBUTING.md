# Contributing

## Development Setup

```bash
uv sync
```

## Code Quality

```bash
uv run ruff check .
uv run ruff format --check .
```

## Running Tests

```bash
uv run pytest -vv
```

## Pre-commit Checklist

1. Run `git diff --check` for whitespace errors
2. Run `uv run ruff check .`
3. Run `uv run ruff format --check .`
4. Run `uv run pytest -vv --cov=custom_components/erftverband_riverlevel`

## Pull Requests

- Target the `main` branch
- Keep changes focused and atomic
- Update tests for new functionality
- Document breaking changes
