from __future__ import annotations

from pathlib import Path

import pytest

from custom_components.erftverband_riverlevel.api import (
    extract_station_descriptors,
    parse_detail_page,
    parse_german_datetime,
    parse_german_number,
    parse_overview_page,
)
from custom_components.erftverband_riverlevel.models import StationDescriptor

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def overview_html() -> str:
    return (FIXTURES / "howis_aktwerte.html").read_text(encoding="utf-8")


@pytest.fixture
def essig_detail_html() -> str:
    return (FIXTURES / "pegel_Essig_zr.html").read_text(encoding="utf-8")


@pytest.fixture
def kirchheim_detail_html() -> str:
    return (FIXTURES / "pegel_Kirchheim_zr.html").read_text(encoding="utf-8")


@pytest.fixture
def zieverich_detail_html() -> str:
    return (FIXTURES / "pegel_Zieverich_zr.html").read_text(encoding="utf-8")


@pytest.fixture
def vussem_detail_html() -> str:
    return (FIXTURES / "pegel_Vussem_zr.html").read_text(encoding="utf-8")


@pytest.fixture
def niederberg_detail_html() -> str:
    return (FIXTURES / "pegel_Niederberg_zr.html").read_text(encoding="utf-8")


# --- German number parsing ---


class TestParseGermanNumber:
    def test_comma_decimal(self):
        assert parse_german_number("0,0") == 0.0
        assert parse_german_number("-14,0") == -14.0
        assert parse_german_number("12,4") == 12.4
        assert parse_german_number("0,04") == 0.04

    def test_dot_decimal(self):
        assert parse_german_number("0.00") == 0.0
        assert parse_german_number("69.5") == 69.5
        assert parse_german_number("0.04") == 0.04

    def test_mixed_separators(self):
        assert parse_german_number("1.234,5") == 1234.5
        assert parse_german_number("1,234.5") == 1234.5

    def test_negative_with_space(self):
        assert parse_german_number("- 14") == -14.0

    def test_negative_zero(self):
        assert parse_german_number("-0.000") == -0.0
        assert parse_german_number("-0") == -0.0

    def test_positive_values(self):
        assert parse_german_number("0") == 0.0
        assert parse_german_number("215") == 215.0
        assert parse_german_number("78") == 78.0
        assert parse_german_number("0.9") == 0.9
        assert parse_german_number("5.1") == 5.1
        assert parse_german_number("35") == 35.0
        assert parse_german_number("0.12") == 0.12
        assert parse_german_number("0.07") == 0.07
        assert parse_german_number("2,0") == 2.0
        assert parse_german_number("3,0") == 3.0

    def test_none_and_empty(self):
        assert parse_german_number(None) is None
        assert parse_german_number("") is None
        assert parse_german_number(" ") is None

    def test_dashes(self):
        assert parse_german_number("-") is None
        assert parse_german_number("—") is None
        assert parse_german_number("–") is None
        assert parse_german_number("---") is None


class TestParseGermanDatetime:
    def test_two_digit_year(self):
        dt = parse_german_datetime("21.07.26 07:01")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 7
        assert dt.day == 21
        assert dt.hour == 7
        assert dt.minute == 1
        assert dt.second == 0

    def test_four_digit_year(self):
        dt = parse_german_datetime("21.07.2026 07:30")
        assert dt is not None
        assert dt.year == 2026
        assert dt.hour == 7
        assert dt.minute == 30

    def test_with_seconds(self):
        dt = parse_german_datetime("21.07.2026 08:00:15")
        assert dt is not None
        assert dt.second == 15

    def test_none_and_empty(self):
        assert parse_german_datetime(None) is None
        assert parse_german_datetime("") is None


# --- Overview page parsing ---


class TestOverviewPage:
    def test_extract_station_descriptors(self, overview_html):
        descriptors = extract_station_descriptors(overview_html)
        assert len(descriptors) >= 28
        assert "Essig" in descriptors
        assert "Kirchheim" in descriptors
        assert "Zieverich" in descriptors
        assert "Moeschemer_M" in descriptors
        assert "Muelheim" in descriptors
        assert "Fuessenich_OW" in descriptors

        essig = descriptors["Essig"]
        assert isinstance(essig, StationDescriptor)
        assert essig.station_name == "Essig"
        assert essig.waterbody == "Orbach"
        assert "Pegel_Essig_zr.html" in essig.detail_url

        kirchheim = descriptors["Kirchheim"]
        assert kirchheim.station_name == "Kirchheim"
        assert kirchheim.waterbody == "Steinbach"

    def test_parse_all_stations(self, overview_html):
        measurements = parse_overview_page(overview_html)
        assert len(measurements) >= 28

    def test_parse_specific_stations(self, overview_html):
        measurements = parse_overview_page(overview_html, {"Essig", "Kirchheim"})
        assert "Essig" in measurements
        assert "Kirchheim" in measurements
        assert len(measurements) == 2

    def test_essig_measurements(self, overview_html):
        measurements = parse_overview_page(overview_html, {"Essig"})
        essig = measurements["Essig"]
        assert essig.water_level_cm == 0.0
        assert essig.water_trend_cm_h == -14.0
        assert essig.discharge_m3s == 0.0
        assert essig.discharge_trend_m3s_h == -0.0
        assert essig.measured_at is not None

    def test_kirchheim_measurements(self, overview_html):
        measurements = parse_overview_page(overview_html, {"Kirchheim"})
        kirchheim = measurements["Kirchheim"]
        assert kirchheim.water_level_cm == 0.0
        assert kirchheim.water_trend_cm_h == -0.0
        assert kirchheim.discharge_m3s == 0.0
        assert kirchheim.discharge_trend_m3s_h == -0.0
        assert kirchheim.measured_at is not None

    def test_zieverich_water_level_only(self, overview_html):
        measurements = parse_overview_page(overview_html, {"Zieverich"})
        z = measurements["Zieverich"]
        assert z.water_level_cm == 89.0
        assert z.discharge_m3s is None
        assert z.measured_at is not None

    def test_niederberg_water_level_only(self, overview_html):
        measurements = parse_overview_page(overview_html, {"Niederberg"})
        n = measurements["Niederberg"]
        assert n.water_level_cm == 9.0
        assert n.discharge_m3s is None
        assert n.measured_at is not None

    def test_vussem_no_thresholds(self, overview_html):
        measurements = parse_overview_page(overview_html, {"Vussem"})
        v = measurements["Vussem"]
        assert v.water_level_cm == 17.0
        assert v.discharge_m3s == 0.06
        assert v.measured_at is not None


# --- Detail page parsing ---


class TestDetailPage:
    def test_essig_metadata(self, essig_detail_html):
        descriptor = StationDescriptor(
            station_id="Essig",
            station_name="Essig",
            waterbody="Orbach",
            detail_url="https://example.com/Pegel_Essig_zr.html",
        )
        meta = parse_detail_page(essig_detail_html, descriptor)
        assert meta.station_name == "Essig"
        assert meta.waterbody == "Orbach"
        t = meta.thresholds
        assert t.mw_cm == 15.0
        assert t.mhw_cm == 82.0
        assert t.ev_alarm_cm == 60.0
        assert t.ev_alarm_m3s == 1.6
        assert t.hq10_cm == 144.0
        assert t.hq10_m3s == 12.4
        assert t.hq100_m3s == 78.0
        assert t.hqextrem_m3s == 215.0

    def test_kirchheim_metadata(self, kirchheim_detail_html):
        descriptor = StationDescriptor(
            station_id="Kirchheim",
            station_name="Kirchheim",
            waterbody="Steinbach",
            detail_url="https://example.com/Pegel_Kirchheim_zr.html",
        )
        meta = parse_detail_page(kirchheim_detail_html, descriptor)
        assert meta.station_name == "Kirchheim"
        t = meta.thresholds
        assert t.mw_cm == 5.0
        assert t.mhw_cm == 45.0
        assert t.ev_alarm_cm == 35.0
        assert t.ev_alarm_m3s == 1.0
        assert t.hq10_cm == 75.0
        assert t.hq10_m3s == 5.1
        assert t.hq100_cm == 180.0
        assert t.hq100_m3s == 35.0
        assert t.hqextrem_m3s == 69.5

    def test_zieverich_no_thresholds(self, zieverich_detail_html):
        descriptor = StationDescriptor(
            station_id="Zieverich",
            station_name="Zieverich",
            waterbody="Erft",
            detail_url="https://example.com/Pegel_Zieverich_zr.html",
        )
        meta = parse_detail_page(zieverich_detail_html, descriptor)
        t = meta.thresholds
        assert t.ev_alarm_cm is None
        assert t.ev_alarm_m3s is None
        assert t.hq10_cm is None

    def test_vussem_no_thresholds(self, vussem_detail_html):
        descriptor = StationDescriptor(
            station_id="Vussem",
            station_name="Vussem",
            waterbody="Veybach",
            detail_url="https://example.com/Pegel_Vussem_zr.html",
        )
        meta = parse_detail_page(vussem_detail_html, descriptor)
        t = meta.thresholds
        assert t.ev_alarm_cm is None
        assert t.ev_alarm_m3s is None
        assert t.hq10_cm is None
        assert t.hq10_m3s is None
        assert t.mw_cm is not None

    def test_niederberg_no_thresholds(self, niederberg_detail_html):
        descriptor = StationDescriptor(
            station_id="Niederberg",
            station_name="Niederberg",
            waterbody="Rotbach",
            detail_url="https://example.com/Pegel_Niederberg_zr.html",
        )
        meta = parse_detail_page(niederberg_detail_html, descriptor)
        t = meta.thresholds
        assert t.ev_alarm_cm is None
        assert t.hq10_cm is None
        assert meta.catchment_area_km2 == 130.6


class TestStationIdFromHref:
    def test_extract_hrefs(self, overview_html):
        descriptors = extract_station_descriptors(overview_html)
        assert "Schoenau" in descriptors
        assert "Eicherscheid" in descriptors
        assert "Moeschemer_M" in descriptors
        assert "Arloff" in descriptors
        assert "Hausweiler" in descriptors
        assert "Horchheim" in descriptors
        assert "Vussem" in descriptors
        assert "Burg_Veynau" in descriptors
        assert "Kirchheim" in descriptors
        assert "Essig" in descriptors
        assert "Morenhoven" in descriptors
        assert "Weilerswist" in descriptors
        assert "Schwerfen" in descriptors
        assert "Wichterich" in descriptors
        assert "Muelheim" in descriptors
        assert "Niederberg" in descriptors
        assert "Friesheim" in descriptors
        assert "Bliesheim" in descriptors
        assert "Horrem" in descriptors
        assert "Gymnich" in descriptors
        assert "Moedrath" in descriptors
        assert "Fuessenich_OW" in descriptors
        assert "Fuessenich" in descriptors
        assert "Bessenich" in descriptors
        assert "Langenich" in descriptors
        assert "Zieverich" in descriptors
        assert "Glesch" in descriptors
        assert "Bedburg" in descriptors
        assert "Neubrueck" in descriptors
        assert "Gill" in descriptors
        assert "Anstel" in descriptors
        assert "Glehn" in descriptors
