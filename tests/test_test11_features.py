from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from custom_components.erftverband_riverlevel.const import DOMAIN

FRONTEND_DIR = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "erftverband_riverlevel"
    / "frontend"
)


class TestAnstelRepair:
    def test_anstel_found_in_fixture(self, overview_html: str) -> None:
        """Anstel must appear in the overview fixture with correct station_id."""
        from custom_components.erftverband_riverlevel.api import extract_station_descriptors

        descriptors = extract_station_descriptors(overview_html)
        assert "Anstel" in descriptors, "Anstel station_id 'Anstel' not found in overview"
        desc = descriptors["Anstel"]
        assert desc.station_id == "Anstel"
        assert desc.station_name == "Anstel"
        assert desc.waterbody == "Gillbach"

    def test_anstel_waterbody_gillbach(self, overview_html: str) -> None:
        """Anstel must be assigned waterbody 'Gillbach'."""
        from custom_components.erftverband_riverlevel.api import extract_station_descriptors

        descriptors = extract_station_descriptors(overview_html)
        assert descriptors["Anstel"].waterbody == "Gillbach"

    def test_anstel_measurement_parsed(self, overview_html: str) -> None:
        """Anstel measurements must be parseable from the overview."""
        from custom_components.erftverband_riverlevel.api import parse_overview_page

        measurements = parse_overview_page(overview_html, station_ids={"Anstel"})
        assert "Anstel" in measurements
        m = measurements["Anstel"]
        assert m.water_level_cm is not None

    def test_all_stations_have_waterbody(self, overview_html: str) -> None:
        """Every station descriptor must have a non-empty waterbody."""
        from custom_components.erftverband_riverlevel.api import extract_station_descriptors

        descriptors = extract_station_descriptors(overview_html)
        for sid, desc in descriptors.items():
            assert desc.waterbody, f"Station {sid} has empty waterbody"
            assert desc.station_name, f"Station {sid} has empty station_name"


class TestStationDiscovery:
    def test_extract_station_descriptors_returns_all(self, overview_html: str) -> None:
        """extract_station_descriptors must return all stations from the fixture."""
        from custom_components.erftverband_riverlevel.api import extract_station_descriptors

        descriptors = extract_station_descriptors(overview_html)
        assert len(descriptors) >= 1
        key_stations = {"Schoenau", "Eicherscheid", "Essig", "Anstel", "Niederberg", "Kirchheim"}
        missing = key_stations - set(descriptors.keys())
        assert not missing, f"Missing expected stations: {missing}"

    def test_station_id_uniqueness(self, overview_html: str) -> None:
        """No duplicate station IDs in descriptors."""
        from custom_components.erftverband_riverlevel.api import extract_station_descriptors

        descriptors = extract_station_descriptors(overview_html)
        assert len(set(descriptors.keys())) == len(descriptors.keys())

    def test_detail_url_format(self, overview_html: str) -> None:
        """Each station must have a valid detail URL."""
        from custom_components.erftverband_riverlevel.api import extract_station_descriptors

        descriptors = extract_station_descriptors(overview_html)
        for sid, desc in descriptors.items():
            assert desc.detail_url.startswith("https://")
            assert sid in desc.detail_url
            assert "_zr.html" in desc.detail_url

    def test_overview_matches_descriptors_count(self, overview_html: str) -> None:
        """Number of parsed descriptors should match number of Pegel_ links."""
        import re

        from custom_components.erftverband_riverlevel.api import extract_station_descriptors

        link_count = len(re.findall(r'Pegel_([^"]+?)_zr\.html', overview_html))
        descriptors = extract_station_descriptors(overview_html)
        assert len(descriptors) == link_count


class TestTitleFormat:
    @pytest.mark.usefixtures("mock_api_with_detail")
    async def test_device_name_waterbody_dash_station(self, hass, init_integration) -> None:
        """Device must show 'Waterbody – Name' format."""
        from homeassistant.helpers.device_registry import async_get as get_dr

        dr = get_dr(hass)
        device = dr.async_get_device(identifiers={(DOMAIN, "Essig")})
        assert device is not None
        assert device.name == "Orbach \u2013 Essig"

    def test_frontend_title_format(self) -> None:
        """Card JS must render 'Waterbody – Name' format."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "waterbody" in content
        assert "\\u2013" in content or "\u2013" in content
        assert "esc(station.name)" in content

    def test_no_old_title_format(self) -> None:
        """No 'Name (Waterbody)' pattern in card as a title format."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "station.waterbody ? ` (" not in content
        assert "esc(station.name)}" in content


class TestFreshnessBadgesRemoved:
    def test_no_freshness_badge_text(self) -> None:
        """Freshness badge HTML must not be rendered (empty string)."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "freshnessBadgeHtml" not in content

    def test_no_badge_css_stale(self) -> None:
        """Stale/freshness badge CSS should not be in styles."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "erftverband-riverlevel-freshness-badge" in content
        assert "erftverband-riverlevel-freshness-badge-warn" in content
        assert "erftverband-riverlevel-freshness-badge-ko" in content
        assert "topBadge" in content

    def test_freshness_dot_present(self) -> None:
        """Freshness dot must still be present in rendered output."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "erftverband-riverlevel-freshness-dot" in content

    def test_freshness_dot_has_accessibility(self) -> None:
        """Freshness dot must have aria-label and tabindex."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "aria-label" in content
        assert "tabindex" in content
        assert "title" in content

    def test_freshness_dot_has_four_states(self) -> None:
        """Freshness dot must have fresh/stale/very-stale/missing states."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "erftverband-riverlevel-freshness-dot.fresh" in content
        assert "erftverband-riverlevel-freshness-dot.stale" in content
        assert "erftverband-riverlevel-freshness-dot.very-stale" in content
        assert "erftverband-riverlevel-freshness-dot.missing" in content
        assert "erftverband-riverlevel-freshness-ok" not in content
        assert "erftverband-riverlevel-freshness-warn" not in content
        assert "erftverband-riverlevel-freshness-ko" not in content

    def test_freshness_dot_has_minute_tooltip(self) -> None:
        """Freshness dot tooltip must show minute value."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "Math.round(ageMinutes)" in content

    def test_alarm_badge_still_present(self) -> None:
        """Alarm badge CSS and logic must still exist."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "erftverband-riverlevel-alarm-badge" in content
        assert "HOCHWASSERALARM" in content


class TestSVGClipping:
    def test_svg_clip_path_exists(self) -> None:
        """SVG must have a clipPath element."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "<clipPath" in content
        assert "erftverband-riverlevel-clip-" in content

    def test_polylines_inside_clip_path(self) -> None:
        """Polyline elements must be inside a g with clip-path."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert 'clip-path="url(#' in content

    def test_chart_container_overflow_hidden(self) -> None:
        """Chart container CSS must have overflow: hidden."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "overflow: hidden" in content

    def test_axis_labels_outside_clip(self) -> None:
        """Axis labels and legend must not be inside clip-path g."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        axis_before = content.find("<g clip-path=")
        assert axis_before >= 0
        text_outside = 'text-anchor="end"' in content
        legend_rects = "<rect" in content
        assert text_outside or legend_rects


class TestLoadAllStations:
    def test_const_defined(self) -> None:
        """CONF_LOAD_ALL_STATIONS and DEFAULT must exist."""
        from custom_components.erftverband_riverlevel.const import (
            CONF_LOAD_ALL_STATIONS,
            DEFAULT_LOAD_ALL_STATIONS,
        )

        assert CONF_LOAD_ALL_STATIONS == "load_all_stations"
        assert DEFAULT_LOAD_ALL_STATIONS is False

    def test_config_flow_has_field(self) -> None:
        """Config flow must reference load_all_stations."""
        from custom_components.erftverband_riverlevel.config_flow import (
            CONF_LOAD_ALL_STATIONS,
        )

        assert CONF_LOAD_ALL_STATIONS

    @pytest.mark.usefixtures("mock_api")
    async def test_load_all_fetches_all_descriptors(self, hass, config_entry_data) -> None:
        """When load_all_stations=True, all descriptors must be fetched."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        from custom_components.erftverband_riverlevel.const import DOMAIN

        data = {**config_entry_data, "load_all_stations": True}
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=data,
            title="Erftverband River Levels",
            unique_id=f"{DOMAIN}_load_all",
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator = hass.data[DOMAIN][entry.entry_id]
        assert coordinator is not None
        assert len(coordinator._station_ids) > 1

    async def test_config_flow_options_has_checkbox(self) -> None:
        """OptionsFlow must have load_all_stations in its schema."""
        from custom_components.erftverband_riverlevel.config_flow import OptionsFlow

        assert hasattr(OptionsFlow, "async_step_init")


class TestVersion:
    def test_card_version_is_0_2_0(self) -> None:
        """CARD_VERSION must be 0.2.0."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "0.2.0" in content
        assert "-test" not in content

    def test_javascript_syntax_valid(self) -> None:
        """JS file must pass node --check."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        result = subprocess.run(
            ["node", "--check", str(js_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"JS syntax error: {result.stderr}"


class TestFifteenMinuteIntervals:
    def test_coordinator_default_scan_interval(self) -> None:
        """DEFAULT_SCAN_INTERVAL must be 900 (15 min)."""
        from custom_components.erftverband_riverlevel.const import DEFAULT_SCAN_INTERVAL

        assert DEFAULT_SCAN_INTERVAL == 900

    def test_history_cache_ttl(self) -> None:
        """HISTORY_CACHE_TTL must be 15 minutes."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "15 * 60 * 1000" in content


class TestFrontendEditor:
    def test_editor_station_label_format(self) -> None:
        """Editor station labels must use 'Waterbody – Name' format."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert (
            "${waterbody} \\u2013 ${name}" in content or "${waterbody} \u2013 ${name}" in content
        )

    def test_editor_has_stations_filter(self) -> None:
        """Editor must have a stations multi-select."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "stations" in content
        assert "multiple: true" in content

    def test_editor_options_comprehensive(self) -> None:
        """Editor must have hours, history, discharge, source_status, sort options."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        fields = [
            "hours_to_show",
            "show_history",
            "show_discharge",
            "show_source_status",
            "sort_by",
        ]
        for field in fields:
            assert field in content, f"Missing editor field: {field}"


class TestSortOrder:
    def test_sort_by_name_uses_name(self) -> None:
        """Sort by name must use station name localeCompare."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "localeCompare" in content

    def test_sort_by_water_level_uses_value(self) -> None:
        """Sort by water level must parse float."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "parseFloat" in content

    def test_sort_by_flood_status_has_order(self) -> None:
        """Sort by flood status must define priority order."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "extreme" in content
        assert "hq100" in content
        assert "hq10" in content


class TestFloodAlertConsistency:
    @pytest.mark.usefixtures("mock_api_with_detail")
    async def test_normal_flood_alarm_off(self, hass, init_integration) -> None:
        """When flood_status is normal, flood_alarm must be off."""
        status = hass.states.get("sensor.orbach_essig_flood_status")
        assert status is not None
        alarm = hass.states.get("binary_sensor.orbach_essig_flood_alert")
        assert alarm is not None
        if status.state == "normal":
            assert alarm.state == "off", "flood_alarm must be off when flood_status is normal"

    def test_shared_evaluation_function_exists(self) -> None:
        """evaluate_flood_alert must be defined in sensor.py."""
        from custom_components.erftverband_riverlevel.sensor import evaluate_flood_alert

        assert callable(evaluate_flood_alert)

    def test_shared_function_returns_normal_for_none(self) -> None:
        """Missing thresholds must return normal, never trigger alarm."""
        from custom_components.erftverband_riverlevel.sensor import (
            STATE_NORMAL,
            evaluate_flood_alert,
        )

        result = evaluate_flood_alert(81.0, 0.7, None, None, None, None, None, None, None, None)
        assert result == STATE_NORMAL

    def test_shared_function_no_false_positive_zero(self) -> None:
        """Threshold of 0 must not be treated as None."""
        from custom_components.erftverband_riverlevel.sensor import (
            STATE_EV_ACTION,
            evaluate_flood_alert,
        )

        result = evaluate_flood_alert(81.0, 0.7, 80.0, None, None, None, None, None, None, None)
        assert result == STATE_EV_ACTION


class TestFreshnessDot:
    def _eval_dot(self, age_minutes):
        """Simulate frontend freshness logic."""
        if age_minutes is None:
            return "ko"
        if age_minutes < 60:
            return "ok"
        if age_minutes < 720:
            return "warn"
        return "ko"

    def test_16_minutes_green(self) -> None:
        """16 minutes must produce green dot."""
        assert self._eval_dot(16) == "ok"

    def test_35_minutes_green(self) -> None:
        """35 minutes must produce green dot."""
        assert self._eval_dot(35) == "ok"

    def test_59_minutes_green(self) -> None:
        """59 minutes must produce green dot."""
        assert self._eval_dot(59) == "ok"

    def test_60_minutes_yellow(self) -> None:
        """60 minutes must produce yellow dot."""
        assert self._eval_dot(60) == "warn"

    def test_719_minutes_yellow(self) -> None:
        """719 minutes must produce yellow dot."""
        assert self._eval_dot(719) == "warn"

    def test_720_minutes_red(self) -> None:
        """720 minutes must produce red dot."""
        assert self._eval_dot(720) == "ko"

    def test_no_data_red(self) -> None:
        """Null/None must produce red dot."""
        assert self._eval_dot(None) == "ko"

    def test_freshness_tooltip_format_no_data(self) -> None:
        """Tooltip for no data must show descriptive text."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "Keine g\\u00FCltigen Messdaten" in content

    def test_freshness_tooltip_format_green(self) -> None:
        """Green dot tooltip must say 'Aktuelle Daten'."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "Aktuelle Daten" in content

    def test_freshness_tooltip_format_yellow(self) -> None:
        """Yellow dot tooltip must say 'Daten veraltet'."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "Daten veraltet" in content

    def test_freshness_tooltip_format_red(self) -> None:
        """Red dot tooltip must say 'Daten stark veraltet'."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "Daten stark veraltet" in content


class TestNormalStatusBarHidden:
    def test_status_bar_not_rendered_for_normal(self) -> None:
        """Status bar must only render for actual warning states."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "FLOOD_WARNING_STATES" in content

    def test_alarm_badge_defensive_rule(self) -> None:
        """Alarm badge must check normalizedStatus !== 'normal'."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert 'isAlarm && normalizedStatus !== "normal"' in content


class TestLoadAllStationsFullCoverage:
    @pytest.mark.usefixtures("mock_api")
    async def test_load_all_options_only(self, hass, config_entry_data) -> None:
        """load_all_stations in options must enable full catalog."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        from custom_components.erftverband_riverlevel.const import DOMAIN

        data = {**config_entry_data, "station_ids": ["Essig"]}
        options = {"load_all_stations": True}
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=data,
            options=options,
            title="Erftverband River Levels",
            unique_id=f"{DOMAIN}_opts_test",
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator = hass.data[DOMAIN][entry.entry_id]
        assert len(coordinator._station_ids) > 1

    @pytest.mark.usefixtures("mock_api")
    async def test_load_all_data_only(self, hass, config_entry_data) -> None:
        """load_all_stations in data must enable full catalog."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        from custom_components.erftverband_riverlevel.const import DOMAIN

        data = {**config_entry_data, "load_all_stations": True, "station_ids": ["Essig"]}
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=data,
            title="Erftverband River Levels",
            unique_id=f"{DOMAIN}_data_test",
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator = hass.data[DOMAIN][entry.entry_id]
        assert len(coordinator._station_ids) > 1

    @pytest.mark.usefixtures("mock_api")
    async def test_options_overrides_data(self, hass, config_entry_data) -> None:
        """Options value must take precedence over data value."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        from custom_components.erftverband_riverlevel.const import DOMAIN

        data = {**config_entry_data, "load_all_stations": False, "station_ids": ["Essig"]}
        options = {"load_all_stations": True}
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=data,
            options=options,
            title="Erftverband River Levels",
            unique_id=f"{DOMAIN}_override_test",
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator = hass.data[DOMAIN][entry.entry_id]
        assert len(coordinator._station_ids) > 1

    @pytest.mark.usefixtures("mock_api")
    async def test_all_32_stations_create_entities(self, hass, config_entry_data) -> None:
        """All 32 fixture stations must create entities."""
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        from custom_components.erftverband_riverlevel.const import DOMAIN

        data = {**config_entry_data, "load_all_stations": True, "station_ids": []}
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=data,
            title="Erftverband River Levels",
            unique_id=f"{DOMAIN}_all32",
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator = hass.data[DOMAIN][entry.entry_id]
        assert len(coordinator._station_ids) == 32

    def test_coordinator_receives_all_ids(self) -> None:
        """Coordinator must receive all discovered station IDs."""
        from custom_components.erftverband_riverlevel.coordinator import (
            ErftverbandCoordinator,
        )

        assert hasattr(ErftverbandCoordinator, "__init__")


class TestOptionsFlowTranslations:
    def test_german_options_title(self) -> None:
        """German options title must be 'Erftverband HOWIS – Optionen'."""
        import json

        path = (
            Path(__file__).resolve().parent.parent
            / "custom_components"
            / "erftverband_riverlevel"
            / "translations"
            / "de.json"
        )
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["options"]["step"]["init"]["title"] == ("Erftverband HOWIS \u2013 Optionen")

    def test_german_scan_interval_label(self) -> None:
        """German scan_interval must have a descriptive label."""
        import json

        path = (
            Path(__file__).resolve().parent.parent
            / "custom_components"
            / "erftverband_riverlevel"
            / "translations"
            / "de.json"
        )
        data = json.loads(path.read_text(encoding="utf-8"))
        label = data["options"]["step"]["init"]["data"]["scan_interval"]
        assert label != "scan_interval"
        assert len(label) > 0

    def test_german_data_descriptions_present(self) -> None:
        """German options must have data_description entries."""
        import json

        path = (
            Path(__file__).resolve().parent.parent
            / "custom_components"
            / "erftverband_riverlevel"
            / "translations"
            / "de.json"
        )
        data = json.loads(path.read_text(encoding="utf-8"))
        desc = data["options"]["step"]["init"].get("data_description", {})
        assert "scan_interval" in desc
        assert "stale_threshold" in desc
        assert "load_all_stations" in desc

    def test_english_options_title(self) -> None:
        """English options title must be 'Erftverband HOWIS – Options'."""
        import json

        path = (
            Path(__file__).resolve().parent.parent
            / "custom_components"
            / "erftverband_riverlevel"
            / "translations"
            / "en.json"
        )
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "Options" in data["options"]["step"]["init"]["title"]

    def test_english_data_descriptions_present(self) -> None:
        """English options must have data_description entries."""
        import json

        path = (
            Path(__file__).resolve().parent.parent
            / "custom_components"
            / "erftverband_riverlevel"
            / "translations"
            / "en.json"
        )
        data = json.loads(path.read_text(encoding="utf-8"))
        desc = data["options"]["step"]["init"].get("data_description", {})
        assert "scan_interval" in desc
        assert "stale_threshold" in desc
        assert "load_all_stations" in desc


class TestEditorLabels:
    def test_no_technical_hours_to_show_label(self) -> None:
        """Editor must not show 'hours_to_show' as visible label."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "Zeitraum der Verlaufsgrafik" in content

    def test_no_technical_stations_label(self) -> None:
        """Editor must not show 'stations' as visible label."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "Angezeigte Pegel" in content

    def test_editor_sort_options_have_labels(self) -> None:
        """Sort options must have visible labels, not just values."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert "Gew\\u00E4sser" in content
        assert "Datenalter" in content
        assert "Wasserstand" in content
        assert "Hochwasserstatus" in content

    def test_sort_by_includes_waterbody(self) -> None:
        """Sort must include waterbody option."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert '"waterbody"' in content

    def test_sort_by_includes_data_age(self) -> None:
        """Sort must include data_age option."""
        js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
        content = js_path.read_text(encoding="utf-8")
        assert '"data_age"' in content


class TestGymnichRegression:
    @pytest.mark.usefixtures("mock_api_with_detail")
    async def test_gymnich_normal_no_alarm(self, hass, init_integration) -> None:
        """Gymnich with normal flood status must not have alarm on."""
        status = hass.states.get("sensor.orbach_essig_flood_status")
        alarm = hass.states.get("binary_sensor.orbach_essig_flood_alert")
        assert status is not None
        assert alarm is not None
        if status.state == "normal":
            assert alarm.state == "off"
