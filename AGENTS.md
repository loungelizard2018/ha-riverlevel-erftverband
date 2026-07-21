# Agent Instructions

## Directories

- Target repo: `/Users/vwebpu4/Developer/ha-riverlevel-erftverband`
- Reference (read-only): `/Users/vwebpu4/Developer/homeassistant-odf-reference`

## Checks

Before each change:
- `git diff --check`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pytest -vv --cov=custom_components/erftverband_riverlevel --cov-report=term-missing`

## Prohibitions

- No commit, push, or GitHub release
- No changes to `/Volumes/config`
- No changes to the reference repository
