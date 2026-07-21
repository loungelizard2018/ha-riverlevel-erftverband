from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

from custom_components.erftverband_riverlevel.api import (
    DetailPageParser,
    OverviewTableParser,
    extract_station_id_from_href,
    parse_detail_html,
    parse_german_datetime,
    parse_german_number,
    parse_overview_stations,
    parse_overview_table,
    parse_station_name_cell,
)
from custom_components.erftverband_riverlevel.models import StationData

FIXTURES = Path(__file__).parent / "fixtures"
TZ_BERLIN = ZoneInfo("Europe/Berlin")


class TestParseGermanNumber:
    def test_integer(self) -> None:
        assert parse_german_number("152") == 152.0
        assert parse_german_number("0") == 0.0
        assert parse_german_number("5") == 5.0

    def test_comma_decimal(self) -> None:
        assert parse_german_number("2,0") == 2.0
        assert parse_german_number("0,9") == 0.9
        assert parse_german_number("3,7") == 3.7
        assert parse_german_number("41,1") == 41.1

    def test_period_decimal(self) -> None:
        assert parse_german_number("0.03") == 0.03
        assert parse_german_number("12.4") == 12.4
        assert parse_german_number("8.6") == 8.6

    def test_mixed_formats(self) -> None:
        assert parse_german_number("84,2") == 84.2
        assert parse_german_number("28,5") == 28.5
        assert parse_german_number("16,6") == 16.6

    def test_negative_values(self) -> None:
        assert parse_german_number("-14") == -14.0
        assert parse_german_number("-0") == 0.0
        assert parse_german_number("-0.000") == 0.0
        assert parse_german_number("-0.001") == -0.001

    def test_space_padded(self) -> None:
        assert parse_german_number("     5") == 5.0
        assert parse_german_number("    15") == 15.0
        assert parse_german_number("   152") == 152.0

    def test_negative_with_space(self) -> None:
        assert parse_german_number("-14") == -14.0
        assert parse_german_number("+     1") == 1.0
        assert parse_german_number("+     0") == 0.0
        assert parse_german_number("-1") == -1.0

    def test_empty_and_missing(self) -> None:
        assert parse_german_number("-") is None
        assert parse_german_number(" - ") is None
        assert parse_german_number("k.A.") is None
        assert parse_german_number("") is None
        assert parse_german_number("---") is None

    def test_dash_variants(self) -> None:
        assert parse_german_number("\u2014") is None
        assert parse_german_number("\u2013") is None

    def test_nbsp(self) -> None:
        assert parse_german_number("1\u00a0000,5") == 1000.5


class TestParseGermanDateTime:
    def test_two_digit_year(self) -> None:
        dt = parse_german_datetime("21.07.26 18:50")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 7
        assert dt.day == 21
        assert dt.hour == 18
        assert dt.minute == 50
        assert dt.tzinfo == TZ_BERLIN

    def test_four_digit_year(self) -> None:
        dt = parse_german_datetime("21.07.2026 18:01")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 7
        assert dt.day == 21
        assert dt.hour == 18
        assert dt.minute == 1

    def test_invalid(self) -> None:
        assert parse_german_datetime("") is None
        assert parse_german_datetime("invalid") is None


class TestStationIdExtraction:
    def test_standard(self) -> None:
        assert extract_station_id_from_href("./pegel/Pegel_Essig_zr.html") == "Essig"

    def test_with_umlaut(self) -> None:
        assert extract_station_id_from_href("./pegel/Pegel_Moedrath_zr.html") == "Moedrath"
        assert extract_station_id_from_href("./pegel/Pegel_Neubrueck_zr.html") == "Neubrueck"
        assert extract_station_id_from_href("./pegel/Pegel_Muelheim_zr.html") == "Muelheim"

    def test_with_suffix(self) -> None:
        href = "./pegel/Pegel_Fuessenich_OW_zr.html"
        assert extract_station_id_from_href(href) == "Fuessenich_OW"
        href2 = "./pegel/Pegel_Moeschemer_M_zr.html"
        assert extract_station_id_from_href(href2) == "Moeschemer_M"

    def test_none(self) -> None:
        assert extract_station_id_from_href("") is None
        assert extract_station_id_from_href("no_underscore.html") is None


class TestParseStationNameCell:
    def test_standard(self) -> None:
        assert parse_station_name_cell("Essig (Orbach)") == ("Essig", "Orbach")
        assert parse_station_name_cell("Kirchheim (Steinbach)") == ("Kirchheim", "Steinbach")

    def test_with_nbsp(self) -> None:
        assert parse_station_name_cell("Sch\u00f6nau (Erft)") == ("Sch\u00f6nau", "Erft")


class TestOverviewParsing:
    def test_parse_all_stations(self) -> None:
        html = (FIXTURES / "overview.html").read_text(encoding="utf-8")
        stations = parse_overview_stations(html)
        station_ids = [s.station_id for s in stations]
        assert "Schoenau" in station_ids
        assert "Essig" in station_ids
        assert "Kirchheim" in station_ids
        assert "Niederberg" in station_ids
        assert "Moedrath" in station_ids
        assert len(stations) >= 30

    def test_station_ids_are_stable(self) -> None:
        html = (FIXTURES / "overview.html").read_text(encoding="utf-8")
        stations = parse_overview_stations(html)
        for s in stations:
            assert s.station_id
            assert "_zr" not in s.station_id
            assert "Pegel" not in s.station_id
            assert "/" not in s.station_id

    def test_station_descriptors(self) -> None:
        html = (FIXTURES / "overview.html").read_text(encoding="utf-8")
        stations = parse_overview_stations(html)
        essig = next((s for s in stations if s.station_id == "Essig"), None)
        assert essig is not None
        assert essig.name == "Essig"
        assert essig.waterbody == "Orbach"
        assert "_zr.html" in essig.href

    def test_overview_table_values(self) -> None:
        html = (FIXTURES / "overview.html").read_text(encoding="utf-8")
        table_data = parse_overview_table(html)
        key_essig = "Essig|Orbach"
        key_kirchheim = "Kirchheim|Steinbach"
        assert key_essig in table_data
        assert key_kirchheim in table_data
        essig = table_data[key_essig]
        assert essig["name"] == "Essig"
        assert essig["waterbody"] == "Orbach"
        assert essig["water_level_cm"] == 0
        assert essig["discharge_m3s"] == 0.0

    def test_one_overview_request(self) -> None:
        html = (FIXTURES / "overview.html").read_text(encoding="utf-8")
        table1 = parse_overview_table(html)
        table2 = parse_overview_table(html)
        assert table1 == table2


class TestDetailParsing:
    def test_essig_metadata(self) -> None:
        html = (FIXTURES / "detail_Essig.html").read_text(encoding="utf-8")
        station = parse_detail_html(html, "Essig")
        assert station.station_id == "Essig"
        assert station.name == "Essig"
        assert station.waterbody == "Orbach"
        assert station.operator == "Erftverband"

    def test_essig_thresholds(self) -> None:
        html = (FIXTURES / "detail_Essig.html").read_text(encoding="utf-8")
        station = parse_detail_html(html, "Essig")
        th = station.thresholds
        assert th.ev_w == 60.0
        assert th.ev_q == 1.6
        assert th.hq10_w == 144.0
        assert th.hq10_q == 12.4
        assert th.hq100_w is None
        assert th.hq100_q == 78.0
        assert th.hqextrem_w is None
        assert th.hqextrem_q == 215.0

    def test_essig_main_values(self) -> None:
        html = (FIXTURES / "detail_Essig.html").read_text(encoding="utf-8")
        station = parse_detail_html(html, "Essig")
        assert station.catchment_area == 41.1

    def test_kirchheim_operator(self) -> None:
        html = (FIXTURES / "detail_Kirchheim.html").read_text(encoding="utf-8")
        station = parse_detail_html(html, "Kirchheim")
        assert station.operator == "e-regio"
        assert station.waterbody == "Steinbach"

    def test_kirchheim_thresholds(self) -> None:
        html = (FIXTURES / "detail_Kirchheim.html").read_text(encoding="utf-8")
        station = parse_detail_html(html, "Kirchheim")
        th = station.thresholds
        assert th.ev_w == 35
        assert th.ev_q == 1.0
        assert th.hq10_w == 75
        assert th.hq10_q == 5.1
        assert th.hq100_w == 180
        assert th.hq100_q == 35
        assert th.hqextrem_w is None
        assert th.hqextrem_q == 69.5

    def test_niederberg_no_discharge(self) -> None:
        html = (FIXTURES / "detail_Niederberg.html").read_text(encoding="utf-8")
        station = parse_detail_html(html, "Niederberg")
        assert station.discharge_m3s is None
        assert station.water_level_cm == 9.0
        th = station.thresholds
        assert th.ev_w is None
        assert th.ev_q is None
        assert th.hq10_w is None

    def test_wichterich_no_thresholds(self) -> None:
        html = (FIXTURES / "detail_Wichterich.html").read_text(encoding="utf-8")
        station = parse_detail_html(html, "Wichterich")
        th = station.thresholds
        assert th.ev_w is None
        assert th.ev_q is None
        assert th.hq10_w is None
        assert th.hq10_q is None

    def test_schoenau_umlaut(self) -> None:
        html = (FIXTURES / "detail_Schoenau.html").read_text(encoding="utf-8")
        station = parse_detail_html(html, "Schoenau")
        assert station.name == "Sch\u00f6nau"
        assert station.waterbody == "Erft"

    def test_detail_current_values(self) -> None:
        html = (FIXTURES / "detail_Essig.html").read_text(encoding="utf-8")
        station = parse_detail_html(html, "Essig")
        assert station.water_level_cm is not None
        assert station.measured_at is not None
        assert station.wl_trend is not None
        assert station.detail_fetched_at is not None


class TestModelSerialization:
    def test_station_data_roundtrip(self) -> None:
        html = (FIXTURES / "detail_Essig.html").read_text(encoding="utf-8")
        station = parse_detail_html(html, "Essig")
        serialized = station.to_dict()
        restored = StationData.from_dict(serialized)
        assert restored.station_id == station.station_id
        assert restored.name == station.name
        assert restored.waterbody == station.waterbody
        assert restored.operator == station.operator
        assert restored.thresholds.ev_w == station.thresholds.ev_w
        assert restored.thresholds.hq10_q == station.thresholds.hq10_q
        if station.water_level_cm is not None:
            assert restored.water_level_cm == station.water_level_cm
        assert restored.catchment_area == station.catchment_area


class TestUmlautHandling:
    def test_display_name_preserves_umlaut(self) -> None:
        html = (FIXTURES / "detail_Umlaut.html").read_text(encoding="utf-8")
        station = parse_detail_html(html, "Schoenau")
        assert station.name == "Sch\u00f6nau"
        assert "ö" in station.name

    def test_html_decoding_entities(self) -> None:
        html = (FIXTURES / "detail_Umlaut.html").read_text(encoding="utf-8")
        station = parse_detail_html(html, "Schoenau")
        assert station.waterbody == "M\u00fchlbach"
        assert "ü" in station.waterbody

    def test_waterbody_umlaut(self) -> None:
        html = (FIXTURES / "detail_Umlaut.html").read_text(encoding="utf-8")
        station = parse_detail_html(html, "Schoenau")
        assert "Gewässer" in station.waterbody or station.waterbody == "M\u00fchlbach"

    def test_station_id_derived_from_href_independent_of_name(self) -> None:
        html = (FIXTURES / "detail_Umlaut.html").read_text(encoding="utf-8")
        station = parse_detail_html(html, "Schoenau")
        assert station.station_id == "Schoenau"
        assert station.station_id != "Sch\u00f6nau"

    def test_no_encoding_corruption(self) -> None:
        html = (FIXTURES / "detail_Umlaut.html").read_text(encoding="utf-8")
        raw = html.encode("utf-8")
        decoded = raw.decode("utf-8")
        assert "Sch\u00c3\u00b6nau" not in decoded
        assert "SchÃ¶nau" not in decoded
        station = parse_detail_html(html, "Schoenau")
        assert station.name == "Sch\u00f6nau"

    def test_overview_umlaut_decoding(self, overview_html: str) -> None:
        from custom_components.erftverband_riverlevel.api import parse_overview_stations

        stations = parse_overview_stations(overview_html)
        found = [s for s in stations if "önau" in s.name or "ö" in s.name]
        assert len(found) > 0
        schoenau = next(
            (s for s in stations if "Schoenau" in s.station_id or "önau" in s.name),
            None,
        )
        assert schoenau is not None
        assert "ö" in schoenau.name or "Schoenau" in schoenau.station_id


class TestHtmlParser:
    def test_overview_parser_simple(self) -> None:
        html = (
            "<table><thead></thead><tbody><tr>"
            "<td>Essig (Orbach)</td><td>21.07.26 18:01</td>"
            "<td>5</td><td>-0</td><td>0.03</td><td>-0.001</td>"
            "<td>0.12</td><td>2,0</td><td>3,0</td>"
            "<td>12.4</td><td>78</td><td>215</td>"
            "</tr></tbody></table>"
        )
        parser = OverviewTableParser()
        parser.feed(html)
        assert len(parser.rows) == 1
        assert parser.rows[0]["name"] == "Essig"
        assert parser.rows[0]["water_level_cm"] == 5.0

    def test_detail_parser(self) -> None:
        html = "<h4> Stammdaten</h4><table><tr><td>Pegel</td><td>Essig</td></tr></table>"
        parser = DetailPageParser("Essig")
        parser.feed(html)
        data = parser.get_station_data()
        assert data.name == "Essig"
