# Agent Instructions

## Verzeichnisse

- Zielrepo: `/Users/vwebpu4/Developer/ha-riverlevel-erftverband`
- Referenz (read-only): `/Users/vwebpu4/Developer/homeassistant-odf-reference`

## Prüfungen

Vor jeder Änderung:
- `git diff --check`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pytest -vv --cov=custom_components/erftverband_riverlevel --cov-report=term-missing`

## Verbote

- Kein Commit, Push oder GitHub Release
- Keine Änderungen an `/Volumes/config`
- Keine Änderungen am Referenz-Repository
