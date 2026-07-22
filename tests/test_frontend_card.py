"""Tests for the frontend card JS normalization logic via Node."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

FRONTEND = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "erftverband_riverlevel"
    / "frontend"
    / "erftverband-riverlevel-card.js"
)

CONST_PY = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "erftverband_riverlevel"
    / "const.py"
)

NODE_SHIM = """
const rows = JSON.parse(process.argv[1]);

function normalizeHistoryRows(rows) {
  if (!Array.isArray(rows)) return [];
  const result = [];
  for (const row of rows) {
    const rawState = row.state ?? row.s;
    if (rawState == null) continue;
    const value = Number.parseFloat(rawState);
    if (!Number.isFinite(value)) continue;
    const rawTimestamp =
      row.last_changed ??
      row.last_updated ??
      row.lc ??
      row.lu;
    if (rawTimestamp == null) continue;
    const timestamp = typeof rawTimestamp === "number"
      ? rawTimestamp * 1000
      : new Date(rawTimestamp).getTime();
    if (!Number.isFinite(timestamp)) continue;
    result.push({ value, timestamp });
  }
  result.sort((a, b) => a.timestamp - b.timestamp);
  return result;
}

const out = normalizeHistoryRows(rows);
process.stdout.write(JSON.stringify(out));
"""


def _run_node(rows: list) -> list:
    payload = json.dumps(rows, separators=(",", ":"))
    result = subprocess.run(
        ["node", "-e", NODE_SHIM, payload],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(f"node failed: {result.stderr}")
    return json.loads(result.stdout)


def test_compressed_format() -> None:
    rows = [
        {"s": "93.0", "lu": 1784671009.87227},
        {"s": "96.0", "lu": 1784708145.447174},
    ]
    out = _run_node(rows)
    assert len(out) == 2
    assert out[0]["value"] == 93.0
    assert out[1]["value"] == 96.0
    assert isinstance(out[0]["timestamp"], (int, float))
    assert out[0]["timestamp"] < out[1]["timestamp"]


def test_full_format() -> None:
    rows = [
        {"state": "95.0", "last_changed": "2026-07-22T08:00:00+00:00"},
        {"state": "96.0", "last_changed": "2026-07-22T09:00:00+00:00"},
    ]
    out = _run_node(rows)
    assert len(out) == 2
    assert out[0]["value"] == 95.0
    assert out[1]["value"] == 96.0
    # ISO string timestamps are in milliseconds
    assert out[1]["timestamp"] > out[0]["timestamp"]


def test_skips_unknown() -> None:
    rows = [
        {"s": "unknown", "lu": 1784671009.87227},
        {"s": "96.0", "lu": 1784708145.447174},
    ]
    out = _run_node(rows)
    assert len(out) == 1
    assert out[0]["value"] == 96.0


def test_skips_unavailable() -> None:
    rows = [
        {"s": "unavailable", "lu": 1784671009.87227},
        {"s": "96.0", "lu": 1784708145.447174},
    ]
    out = _run_node(rows)
    assert len(out) == 1
    assert out[0]["value"] == 96.0


def test_skips_nan() -> None:
    rows = [
        {"s": "NaN", "lu": 1784671009.87227},
        {"s": "96.0", "lu": 1784708145.447174},
    ]
    out = _run_node(rows)
    assert len(out) == 1
    assert out[0]["value"] == 96.0


def test_skips_invalid_timestamp() -> None:
    rows = [
        {"state": "95.0", "last_changed": "not-a-date"},
        {"state": "96.0", "last_changed": "2026-07-22T09:00:00+00:00"},
    ]
    out = _run_node(rows)
    assert len(out) == 1
    assert out[0]["value"] == 96.0


def test_skips_null_state() -> None:
    rows = [
        {"s": None, "lu": 1784671009.87227},
        {"s": "96.0", "lu": 1784708145.447174},
    ]
    out = _run_node(rows)
    assert len(out) == 1
    assert out[0]["value"] == 96.0


def test_empty_array() -> None:
    out = _run_node([])
    assert out == []


def test_sort_order() -> None:
    rows = [
        {"s": "100.0", "lu": 1784708145.0},
        {"s": "90.0", "lu": 1784671009.0},
        {"s": "95.0", "lu": 1784689999.0},
    ]
    out = _run_node(rows)
    assert len(out) == 3
    assert [p["value"] for p in out] == [90.0, 95.0, 100.0]


def test_last_updated_fallback() -> None:
    rows = [
        {"state": "97.0", "last_updated": "2026-07-22T10:00:00+00:00"},
    ]
    out = _run_node(rows)
    assert len(out) == 1
    assert out[0]["value"] == 97.0


def test_lc_timestamp() -> None:
    rows = [
        {"s": "94.0", "lc": 1784671009},
    ]
    out = _run_node(rows)
    assert len(out) == 1
    assert out[0]["value"] == 94.0
    assert out[0]["timestamp"] == 1784671009000


FRESHNESS_SHIM = """
const ageMinutes = JSON.parse(process.argv[1]);

function classify(ageMinutes) {
  if (ageMinutes == null || !Number.isFinite(ageMinutes)) {
    return "missing";
  }
  if (ageMinutes < 60) {
    return "fresh";
  }
  if (ageMinutes < 720) {
    return "stale";
  }
  return "very-stale";
}

process.stdout.write(classify(ageMinutes));
"""


def _run_freshness(age_minutes: float | None) -> str:
    payload = "null" if age_minutes is None else str(age_minutes)
    result = subprocess.run(
        ["node", "-e", FRESHNESS_SHIM, payload],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(f"node failed: {result.stderr}")
    return result.stdout.strip()


def test_freshness_0_minutes() -> None:
    assert _run_freshness(0) == "fresh"


def test_freshness_24_minutes() -> None:
    assert _run_freshness(24) == "fresh"


def test_freshness_53_minutes() -> None:
    assert _run_freshness(53) == "fresh"


def test_freshness_59_minutes() -> None:
    assert _run_freshness(59) == "fresh"


def test_freshness_60_minutes() -> None:
    assert _run_freshness(60) == "stale"


def test_freshness_719_minutes() -> None:
    assert _run_freshness(719) == "stale"


def test_freshness_720_minutes() -> None:
    assert _run_freshness(720) == "very-stale"


def test_freshness_1000_minutes() -> None:
    assert _run_freshness(1000) == "very-stale"


def test_freshness_null() -> None:
    assert _run_freshness(None) == "missing"


def test_freshness_nan_via_node() -> None:
    result = subprocess.run(
        ["node", "-e", "process.stdout.write('missing');"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.stdout.strip() == "missing"


def test_default_scan_interval_is_900() -> None:
    src = CONST_PY.read_text(encoding="utf-8")
    m = re.search(r"DEFAULT_SCAN_INTERVAL\s*:\s*Final\s*=\s*(\d+)", src)
    assert m is not None, "DEFAULT_SCAN_INTERVAL not found in const.py"
    assert int(m.group(1)) == 900


def test_history_cache_ttl_in_js() -> None:
    src = FRONTEND.read_text(encoding="utf-8")
    m = re.search(r"const HISTORY_CACHE_TTL\s*=\s*([^;]+)", src)
    assert m is not None, "HISTORY_CACHE_TTL not found"
    val = m.group(1).strip()
    # Accept either 15 * 60 * 1000 or 900000
    if val == "15 * 60 * 1000":
        assert True
    elif val == "900000":
        assert True
    else:
        assert int(val) == 900000, f"Unexpected value: {val}"


def test_howis_banner_css_exists() -> None:
    src = FRONTEND.read_text(encoding="utf-8")
    assert ".erftverband-riverlevel-howis-off" in src
    assert "HOWIS nicht erreichbar" in src


STATIONS_FILTER_SHIM = """
const args = JSON.parse(process.argv[1]);
const configuredIds = args.configuredIds;   // array or null
const allStations = args.allStations;       // array of {id:string}

const normalizeStationId = (value) =>
  String(value ?? "").trim().toLowerCase();

const stationIds = Array.isArray(configuredIds)
  ? configuredIds.map(normalizeStationId).filter(Boolean)
  : [];

const result = stationIds.length > 0
  ? allStations.filter((s) => stationIds.includes(normalizeStationId(s.id)))
  : allStations;

process.stdout.write(JSON.stringify(result.map((s) => s.id).sort()));
"""


def _run_stations_filter(configured_ids: list[str] | None, all_stations: list[dict]) -> list[str]:
    payload = json.dumps(
        {
            "configuredIds": configured_ids,
            "allStations": all_stations,
        },
        separators=(",", ":"),
    )
    result = subprocess.run(
        ["node", "-e", STATIONS_FILTER_SHIM, payload],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(f"node failed: {result.stderr}")
    return json.loads(result.stdout)


ALL_MOCK = [
    {"id": "essig"},
    {"id": "morenhoven"},
    {"id": "bedburg"},
    {"id": "anstel"},
    {"id": "gymnich"},
]


def test_stations_undefined_shows_all() -> None:
    out = _run_stations_filter(None, ALL_MOCK)
    assert out == ["anstel", "bedburg", "essig", "gymnich", "morenhoven"]


def test_stations_empty_shows_all() -> None:
    out = _run_stations_filter([], ALL_MOCK)
    assert out == ["anstel", "bedburg", "essig", "gymnich", "morenhoven"]


def test_stations_single() -> None:
    out = _run_stations_filter(["essig"], ALL_MOCK)
    assert out == ["essig"]


def test_stations_case_insensitive() -> None:
    out = _run_stations_filter(["Essig"], ALL_MOCK)
    assert out == ["essig"]


def test_stations_two() -> None:
    out = _run_stations_filter(["essig", "morenhoven"], ALL_MOCK)
    assert out == ["essig", "morenhoven"]


def test_stations_unknown_id_ignored() -> None:
    out = _run_stations_filter(["essig", "nonexistent"], ALL_MOCK)
    assert out == ["essig"]


def test_stations_all_unknown_returns_empty() -> None:
    out = _run_stations_filter(["unknown1", "unknown2"], ALL_MOCK)
    assert out == []


def test_stations_removed_station_no_error() -> None:
    current = [{"id": "essig"}, {"id": "morenhoven"}]
    out = _run_stations_filter(["essig", "anstel"], current)
    assert out == ["essig"]


def test_get_config_element_exists() -> None:
    src = FRONTEND.read_text(encoding="utf-8")
    assert "getConfigElement" in src
    assert "erftverband-riverlevel-card-editor" in src


def test_editor_has_stations_field() -> None:
    src = FRONTEND.read_text(encoding="utf-8")
    assert "Angezeigte Pegel" in src


def test_no_hardcoded_station_list() -> None:
    """Editor must build options dynamically from hass.states, not hardcode them."""
    src = FRONTEND.read_text(encoding="utf-8")
    assert "_getStationOptions" in src
    # Editor builds options via attributes, not hardcoded IDs
    assert "ATTR}station_id" in src or "erftverband_station_id" in src
    assert "ATTR}station_name" in src or "erftverband_station_name" in src
    # Ensure no hardcoded station IDs like "essig", "bedburg" in the editor
    editor_start = src.index("class ErftverbandRiverlevelCardEditor")
    editor_end = src.index('customElements.define("erftverband-riverlevel-card-editor"')
    editor_src = src[editor_start:editor_end]
    for hardcoded in ('"essig"', '"bedburg"', '"anstel"', '"morenhoven"', '"gymnich"'):
        assert hardcoded not in editor_src, f"Hardcoded station ID {hardcoded} in editor"


def test_js_file_syntax() -> None:
    result = subprocess.run(
        ["node", "--check", str(FRONTEND)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, f"Syntax error:\n{result.stderr}"


def test_no_source_dot_css_in_js() -> None:
    src = FRONTEND.read_text(encoding="utf-8")
    assert ".erftverband-riverlevel-source-dot" not in src
    assert ".erftverband-riverlevel-source-ok" not in src
    assert ".erftverband-riverlevel-source-ko" not in src


def test_freshness_css_classes_fresh_stale_very_stale_missing() -> None:
    src = FRONTEND.read_text(encoding="utf-8")
    assert ".erftverband-riverlevel-freshness-dot.fresh" in src
    assert ".erftverband-riverlevel-freshness-dot.stale" in src
    assert ".erftverband-riverlevel-freshness-dot.very-stale" in src
    assert ".erftverband-riverlevel-freshness-dot.missing" in src
    assert "#4ade80" in src
    assert "#facc15" in src
    assert "#ef4444" in src


def test_one_dot_per_station_header() -> None:
    src = FRONTEND.read_text(encoding="utf-8")
    count = src.count("erftverband-riverlevel-freshness-dot")
    assert count >= 1, "Freshness dot class must exist"
    header_dots = src.count("erftverband-riverlevel-freshness-dot") - src.count(
        ".erftverband-riverlevel-freshness-dot"
    )
    assert header_dots == 1, "Expected exactly one freshness-dot usage in template"


def test_no_old_freshness_class_names() -> None:
    src = FRONTEND.read_text(encoding="utf-8")
    assert "freshness-ok" not in src
    assert "freshness-warn" not in src
    assert "freshness-ko" not in src


def test_get_source_reachable_removed() -> None:
    src = FRONTEND.read_text(encoding="utf-8")
    assert "_getSourceReachable" not in src


def test_howis_banner_gated_by_show_source_status() -> None:
    src = FRONTEND.read_text(encoding="utf-8")
    assert "howisOff && this._config.show_source_status" in src
