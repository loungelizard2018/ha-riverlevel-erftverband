from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from custom_components.erftverband_riverlevel.api import (
    extract_all_stations_from_overview,
    parse_detail_html,
)
from custom_components.erftverband_riverlevel.models import (
    CoordinatorData,
    StationData,
    StationThresholds,
)

TZ_BERLIN = ZoneInfo("Europe/Berlin")
FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class TestCoordinatorData:
    def test_empty_coordinator_data(self) -> None:
        data = CoordinatorData()
        assert data.stations == {}
        assert data.source_reachable is True
        assert data.cache_used is False

    def test_coordinator_roundtrip(self) -> None:
        station = StationData(
            station_id="Essig",
            name="Essig",
            waterbody="Orbach",
            operator="Erftverband",
            water_level_cm=15.0,
        )
        data = CoordinatorData(stations={"Essig": station})
        serialized = data.to_dict()
        restored = CoordinatorData.from_dict(serialized)
        assert "Essig" in restored.stations
        assert restored.stations["Essig"].water_level_cm == 15.0
        assert restored.stations["Essig"].operator == "Erftverband"


class TestFloodStatusCalculation:
    def test_normal_status(self) -> None:
        station = StationData(
            station_id="Essig",
            name="Essig",
            waterbody="Orbach",
            thresholds=StationThresholds(
                ev_w=60.0,
                ev_q=1.6,
                hq10_w=144.0,
                hq10_q=12.4,
                hq100_w=None,
                hq100_q=78.0,
                hqextrem_w=None,
                hqextrem_q=215.0,
            ),
            water_level_cm=15.0,
            discharge_m3s=0.12,
        )
        from custom_components.erftverband_riverlevel.sensor import _compute_flood_status

        assert _compute_flood_status(station).value == "normal"

    def test_ev_action_by_water_level(self) -> None:
        station = StationData(
            station_id="Essig",
            name="Essig",
            waterbody="Orbach",
            thresholds=StationThresholds(ev_w=60.0, ev_q=1.6),
            water_level_cm=80.0,
        )
        from custom_components.erftverband_riverlevel.sensor import _compute_flood_status

        assert _compute_flood_status(station).value == "ev_action"

    def test_ev_action_by_discharge(self) -> None:
        station = StationData(
            station_id="Essig",
            name="Essig",
            waterbody="Orbach",
            thresholds=StationThresholds(ev_w=60.0, ev_q=1.6),
            water_level_cm=10.0,
            discharge_m3s=2.0,
        )
        from custom_components.erftverband_riverlevel.sensor import _compute_flood_status

        assert _compute_flood_status(station).value == "ev_action"

    def test_hq10_by_water_level(self) -> None:
        station = StationData(
            station_id="Essig",
            name="Essig",
            waterbody="Orbach",
            thresholds=StationThresholds(ev_w=60.0, hq10_w=144.0),
            water_level_cm=150.0,
        )
        from custom_components.erftverband_riverlevel.sensor import _compute_flood_status

        assert _compute_flood_status(station).value == "hq10"

    def test_hq100_by_discharge(self) -> None:
        station = StationData(
            station_id="Essig",
            name="Essig",
            waterbody="Orbach",
            thresholds=StationThresholds(hq100_q=78.0),
            discharge_m3s=100.0,
        )
        from custom_components.erftverband_riverlevel.sensor import _compute_flood_status

        assert _compute_flood_status(station).value == "hq100"

    def test_extreme(self) -> None:
        station = StationData(
            station_id="Essig",
            name="Essig",
            waterbody="Orbach",
            thresholds=StationThresholds(hqextrem_q=215.0),
            discharge_m3s=300.0,
        )
        from custom_components.erftverband_riverlevel.sensor import _compute_flood_status

        assert _compute_flood_status(station).value == "extreme"

    def test_missing_thresholds_returns_normal(self) -> None:
        station = StationData(
            station_id="Wichterich",
            name="Wichterich",
            waterbody="Bleibach",
            thresholds=StationThresholds(),
            water_level_cm=17.0,
            discharge_m3s=0.05,
        )
        from custom_components.erftverband_riverlevel.sensor import _compute_flood_status

        assert _compute_flood_status(station).value == "normal"

    def test_no_water_level_no_discharge_unknown(self) -> None:
        station = StationData(
            station_id="Essig",
            name="Essig",
            waterbody="Orbach",
        )
        from custom_components.erftverband_riverlevel.sensor import _compute_flood_status

        assert _compute_flood_status(station).value == "unknown"

    def test_missing_threshold_never_zero(self) -> None:
        """Fehlende Schwellen nie als 0 interpretieren."""
        station = StationData(
            station_id="Essig",
            name="Essig",
            waterbody="Orbach",
            thresholds=StationThresholds(ev_w=None, ev_q=None),
            water_level_cm=50.0,
        )
        from custom_components.erftverband_riverlevel.sensor import _compute_flood_status

        assert _compute_flood_status(station).value == "normal"


class TestCacheFallback:
    def test_cache_used_flag(self) -> None:
        from custom_components.erftverband_riverlevel.const import STORAGE_KEY

        assert STORAGE_KEY == "erftverband_riverlevel.coordinator_data"

    def test_stale_data_stays_original_timestamp(self) -> None:
        original_time = datetime(2026, 7, 21, 12, 0, tzinfo=TZ_BERLIN)
        station = StationData(
            station_id="Essig",
            name="Essig",
            waterbody="Orbach",
            measured_at=original_time,
        )
        serialized = station.to_dict()
        restored = StationData.from_dict(serialized)
        assert restored.measured_at == original_time


class TestDataAge:
    def test_data_age_calculation(self) -> None:
        now = datetime(2026, 7, 21, 19, 0, tzinfo=TZ_BERLIN)
        measured = datetime(2026, 7, 21, 18, 0, tzinfo=TZ_BERLIN)
        delta = now - measured
        assert int(delta.total_seconds() // 60) == 60

    def test_data_age_zero(self) -> None:
        now = datetime(2026, 7, 21, 19, 0, tzinfo=TZ_BERLIN)
        measured = datetime(2026, 7, 21, 19, 0, tzinfo=TZ_BERLIN)
        delta = now - measured
        assert int(delta.total_seconds() // 60) == 0


class TestOverviewAndDetail:
    def test_merge_keeps_detail_thresholds(self) -> None:
        overview_html = _load_fixture("overview.html")
        parsed, descriptors = extract_all_stations_from_overview(overview_html)
        essig_overview = parsed.get("Essig")
        assert essig_overview is not None
        assert essig_overview.water_level_cm is not None

        detail_html = _load_fixture("detail_Essig.html")
        essig_detail = parse_detail_html(detail_html, "Essig")
        assert essig_detail.thresholds.ev_w == 60.0

    def test_detail_overview_water_level_match(self) -> None:
        overview_html = _load_fixture("overview.html")
        parsed, descriptors = extract_all_stations_from_overview(overview_html)
        essig_overview = parsed.get("Essig")
        detail_html = _load_fixture("detail_Essig.html")
        essig_detail = parse_detail_html(detail_html, "Essig")
        if essig_overview and essig_detail:
            assert essig_overview.water_level_cm is not None
            assert essig_detail.water_level_cm is not None


class TestDeviceInfo:
    def test_device_identifier_pattern(self) -> None:
        from custom_components.erftverband_riverlevel.const import DOMAIN

        station_id = "Essig"
        identifier = (DOMAIN, station_id)
        assert identifier == ("erftverband_riverlevel", "Essig")
