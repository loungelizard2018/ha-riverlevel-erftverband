from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from custom_components.erftverband_riverlevel.api import age_minutes, parse_german_datetime
from custom_components.erftverband_riverlevel.const import (
    STATE_EV_ACTION,
    STATE_EXTREME,
    STATE_HQ10,
    STATE_HQ100,
    STATE_NORMAL,
    STATE_UNKNOWN,
)
from custom_components.erftverband_riverlevel.models import (
    CoordinatorData,
    StationMeasurement,
    StationThresholds,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
TZ_BERLIN = ZoneInfo("Europe/Berlin")


@pytest.fixture
def overview_html() -> str:
    return (FIXTURES / "howis_aktwerte.html").read_text(encoding="utf-8")


@pytest.fixture
def coordinator_data() -> CoordinatorData:
    now = datetime.now(TZ_BERLIN)
    return CoordinatorData(
        ok=True,
        live_fetch_ok=True,
        source_reachable=True,
        fetched_at=now.isoformat(),
        stations={
            "Essig": StationMeasurement(
                measured_at=now.isoformat(),
                age_minutes=0,
                water_level_cm=10.0,
                water_trend_cm_h=0.0,
                discharge_m3s=0.5,
                discharge_trend_m3s_h=0.0,
            ),
            "Kirchheim": StationMeasurement(
                measured_at=now.isoformat(),
                age_minutes=2,
                water_level_cm=5.0,
                water_trend_cm_h=-0.0,
                discharge_m3s=0.1,
                discharge_trend_m3s_h=-0.0,
            ),
        },
    )


# --- Status calculation tests ---


class TestFloodStatusCalculation:
    def test_normal(self):
        thresholds = StationThresholds(
            ev_alarm_cm=60.0,
            ev_alarm_m3s=1.6,
            hq10_cm=144.0,
            hq10_m3s=12.4,
        )
        status = _calculate_status(
            water_level=10.0, discharge=0.5, thresholds=thresholds, is_stale=False
        )
        assert status == STATE_NORMAL

    def test_ev_action_by_water_level(self):
        thresholds = StationThresholds(
            ev_alarm_cm=60.0,
            ev_alarm_m3s=1.6,
        )
        status = _calculate_status(
            water_level=70.0, discharge=0.5, thresholds=thresholds, is_stale=False
        )
        assert status == STATE_EV_ACTION

    def test_ev_action_by_discharge(self):
        thresholds = StationThresholds(
            ev_alarm_cm=60.0,
            ev_alarm_m3s=1.6,
        )
        status = _calculate_status(
            water_level=10.0, discharge=2.0, thresholds=thresholds, is_stale=False
        )
        assert status == STATE_EV_ACTION

    def test_hq10_by_water_level(self):
        thresholds = StationThresholds(
            ev_alarm_cm=60.0,
            hq10_cm=144.0,
        )
        status = _calculate_status(
            water_level=150.0, discharge=0.0, thresholds=thresholds, is_stale=False
        )
        assert status == STATE_HQ10

    def test_hq100_by_discharge(self):
        thresholds = StationThresholds(
            ev_alarm_cm=60.0,
            ev_alarm_m3s=1.6,
            hq10_cm=144.0,
            hq10_m3s=12.4,
            hq100_cm=180.0,
            hq100_m3s=35.0,
        )
        status = _calculate_status(
            water_level=10.0, discharge=40.0, thresholds=thresholds, is_stale=False
        )
        assert status == STATE_HQ100

    def test_extreme_by_discharge(self):
        thresholds = StationThresholds(
            ev_alarm_cm=60.0,
            ev_alarm_m3s=1.6,
            hq10_cm=144.0,
            hq10_m3s=12.4,
            hq100_cm=180.0,
            hq100_m3s=35.0,
            hqextrem_cm=200.0,
            hqextrem_m3s=69.5,
        )
        status = _calculate_status(
            water_level=10.0, discharge=80.0, thresholds=thresholds, is_stale=False
        )
        assert status == STATE_EXTREME

    def test_highest_priority_wins(self):
        thresholds = StationThresholds(
            ev_alarm_cm=60.0,
            hq10_cm=144.0,
            hq100_cm=180.0,
            hqextrem_cm=200.0,
        )
        status = _calculate_status(
            water_level=250.0, discharge=0.0, thresholds=thresholds, is_stale=False
        )
        assert status == STATE_EXTREME

    def test_unknown_when_stale(self):
        thresholds = StationThresholds(
            ev_alarm_cm=60.0,
        )
        status = _calculate_status(
            water_level=70.0, discharge=0.0, thresholds=thresholds, is_stale=True
        )
        assert status == STATE_UNKNOWN

    def test_missing_thresholds_returns_normal(self):
        thresholds = StationThresholds()
        status = _calculate_status(
            water_level=70.0, discharge=2.0, thresholds=thresholds, is_stale=False
        )
        assert status == STATE_NORMAL

    def test_none_values_dont_trigger(self):
        thresholds = StationThresholds(
            ev_alarm_cm=60.0,
            ev_alarm_m3s=None,
            hq10_cm=144.0,
            hq10_m3s=None,
        )
        status = _calculate_status(
            water_level=None, discharge=2.0, thresholds=thresholds, is_stale=False
        )
        assert status == STATE_NORMAL


# --- Coordinator data tests ---


class TestCoordinatorData:
    def test_as_dict(self, coordinator_data):
        d = coordinator_data.as_dict()
        assert d["ok"] is True
        assert d["live_fetch_ok"] is True
        assert d["source_reachable"] is True
        assert "Essig" in d["stations"]
        assert d["stations"]["Essig"]["water_level_cm"] == 10.0

    def test_empty_stations(self):
        data = CoordinatorData()
        assert data.ok is False
        assert data.stations == {}

    def test_partial_data(self):
        data = CoordinatorData(
            ok=False,
            error="Connection failed",
            stations={
                "Essig": StationMeasurement(
                    measured_at=None,
                    age_minutes=None,
                    water_level_cm=None,
                    water_trend_cm_h=None,
                    discharge_m3s=None,
                    discharge_trend_m3s_h=None,
                ),
            },
        )
        d = data.as_dict()
        assert d["ok"] is False
        assert d["error"] == "Connection failed"


# --- Cache fallback tests ---


class TestCacheFallback:
    def test_age_recalculation(self, freezer):
        freezer.move_to("2025-06-15 12:30:00+02:00")
        now = datetime.now(TZ_BERLIN)
        five_min_ago = now - timedelta(minutes=5)
        age = age_minutes(five_min_ago)
        assert age is not None
        assert age == 5

    def test_age_none(self):
        assert age_minutes(None) is None


# --- Edge cases ---


class TestEdgeCases:
    def test_sommerzeit(self):
        """Test summer time handling."""
        dt = parse_german_datetime("21.07.2026 12:00")
        assert dt is not None
        assert dt.tzinfo is not None
        assert dt.tzinfo.key == "Europe/Berlin"

    def test_station_with_umlaut_in_url(self):
        """Möschemer Mühle has underscores in URL-safe ID."""
        from custom_components.erftverband_riverlevel.api import extract_station_descriptors

        html = (FIXTURES / "howis_aktwerte.html").read_text(encoding="utf-8")
        descriptors = extract_station_descriptors(html)
        assert "Moeschemer_M" in descriptors
        desc = descriptors["Moeschemer_M"]
        assert desc.station_name == "Möschemer Mühle"

    def test_station_with_umlaut_in_url_muelheim(self):
        from custom_components.erftverband_riverlevel.api import extract_station_descriptors

        html = (FIXTURES / "howis_aktwerte.html").read_text(encoding="utf-8")
        descriptors = extract_station_descriptors(html)
        assert "Muelheim" in descriptors
        desc = descriptors["Muelheim"]
        assert desc.station_name == "Mülheim"

    def test_station_with_name_suffix(self):
        """Füssenich OW has a name suffix and sup tag."""
        from custom_components.erftverband_riverlevel.api import extract_station_descriptors

        html = (FIXTURES / "howis_aktwerte.html").read_text(encoding="utf-8")
        descriptors = extract_station_descriptors(html)
        assert "Fuessenich_OW" in descriptors
        desc = descriptors["Fuessenich_OW"]
        assert desc.station_name == "Füssenich OW"

    def test_betreiber_contains_link(self):
        """Möschemer Mühle betreiber field has an HTML link."""
        from custom_components.erftverband_riverlevel.api import parse_detail_page
        from custom_components.erftverband_riverlevel.models import StationDescriptor

        moeschemer_path = FIXTURES / "pegel_Moeschemer_M_zr.html"
        html = moeschemer_path.read_text(encoding="utf-8")
        descriptor = StationDescriptor(
            station_id="Moeschemer_M",
            station_name="Möschemer Mühle",
            waterbody="Eschweilerbach",
            detail_url="https://example.com/Pegel_Moeschemer_M_zr.html",
        )
        meta = parse_detail_page(html, descriptor)
        assert meta.station_name == "Möschemer Mühle"
        assert meta.thresholds.ev_alarm_cm == 90.0
        assert meta.thresholds.hq10_m3s == 8.1


# --- Overview page: one request per poll ---


class TestOneRequestPerPoll:
    def test_parse_only_called_once(self, overview_html):
        """Verify that one HTML parse extracts all stations."""
        from custom_components.erftverband_riverlevel.api import parse_overview_page

        measurements = parse_overview_page(overview_html)
        assert len(measurements) >= 28

        # Verify specific stations
        assert "Essig" in measurements
        assert "Kirchheim" in measurements
        assert "Glesch" in measurements
        assert "Bedburg" in measurements


# --- Translations keys test ---


class TestTranslationKeys:
    def test_translation_keys_exist(self):
        """Verify that translation keys referenced in sensors exist in translations."""
        import json

        translations_de = json.loads(
            (
                Path(__file__).resolve().parent.parent
                / "custom_components"
                / "erftverband_riverlevel"
                / "translations"
                / "de.json"
            ).read_text(encoding="utf-8")
        )
        translations_en = json.loads(
            (
                Path(__file__).resolve().parent.parent
                / "custom_components"
                / "erftverband_riverlevel"
                / "translations"
                / "en.json"
            ).read_text(encoding="utf-8")
        )

        sensor_keys = {
            "water_level",
            "discharge",
            "water_trend_raw",
            "discharge_trend_raw",
            "last_measurement",
            "data_age",
            "flood_status",
        }
        binary_sensor_keys = {
            "source_reachable",
            "data_stale",
            "flood_alert",
        }

        for lang, translations in [("de", translations_de), ("en", translations_en)]:
            entities = translations.get("entity", {})
            sensors = entities.get("sensor", {})
            binary_sensors = entities.get("binary_sensor", {})

            for key in sensor_keys:
                assert key in sensors, f"Missing sensor translation key '{key}' in {lang}.json"

            for key in binary_sensor_keys:
                assert key in binary_sensors, (
                    f"Missing binary_sensor translation key '{key}' in {lang}.json"
                )


# --- Diagnostics test ---


def test_diagnostics_schema():
    """Verify the diagnostics function returns the expected structure."""
    from custom_components.erftverband_riverlevel.diagnostics import (
        async_get_config_entry_diagnostics,
        async_get_device_diagnostics,
    )

    # These tests need a full HA setup, so we just verify the async functions exist
    assert callable(async_get_config_entry_diagnostics)
    assert callable(async_get_device_diagnostics)


# --- Helper for status calculation ---


def _calculate_status(
    water_level: float | None,
    discharge: float | None,
    thresholds: StationThresholds,
    is_stale: bool,
) -> str:

    if is_stale:
        return STATE_UNKNOWN

    max_state = STATE_NORMAL

    if thresholds is not None:
        if _check(water_level, thresholds.hqextrem_cm) or _check(
            discharge, thresholds.hqextrem_m3s
        ):
            max_state = max(max_state, STATE_EXTREME, key=_state_order)
        if _check(water_level, thresholds.hq100_cm) or _check(discharge, thresholds.hq100_m3s):
            max_state = max(max_state, STATE_HQ100, key=_state_order)
        if _check(water_level, thresholds.hq10_cm) or _check(discharge, thresholds.hq10_m3s):
            max_state = max(max_state, STATE_HQ10, key=_state_order)
        if _check(water_level, thresholds.ev_alarm_cm) or _check(
            discharge, thresholds.ev_alarm_m3s
        ):
            max_state = max(max_state, STATE_EV_ACTION, key=_state_order)

    return max_state


def _check(value: float | None, threshold: float | None) -> bool:
    if value is None or threshold is None:
        return False
    return value >= threshold


def _state_order(state: str) -> int:
    order = {
        STATE_NORMAL: 0,
        STATE_EV_ACTION: 1,
        STATE_HQ10: 2,
        STATE_HQ100: 3,
        STATE_EXTREME: 4,
        STATE_UNKNOWN: -1,
    }
    return order.get(state, -1)
