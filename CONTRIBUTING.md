# Contributing

## Setup

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Code Style

This project uses Ruff for linting and formatting:

```bash
uv run ruff check .
uv run ruff format --check .
```

## Testing

```bash
uv run pytest -vv --cov=custom_components/erftverband_riverlevel --cov-report=term-missing
```

Tests use offline HTML fixtures in `tests/fixtures/`. No network access required.

## Pull Requests

- Run all checks before submitting.
- Add tests for new functionality.
- Keep `pyproject.toml` updated.
