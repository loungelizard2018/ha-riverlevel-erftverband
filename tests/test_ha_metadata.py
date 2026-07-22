from __future__ import annotations

from pathlib import Path

import pytest

from custom_components.erftverband_riverlevel.const import DOMAIN

FRONTEND_DIR = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "erftverband_riverlevel"
    / "frontend"
)

ASSETS_DIR = FRONTEND_DIR / "assets"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_water_level_has_metadata(hass, init_integration) -> None:
    state = hass.states.get("sensor.orbach_essig_water_level")
    assert state is not None
    attrs = state.attributes
    assert attrs.get("erftverband_riverlevel") is True
    assert attrs.get("erftverband_station_id") == "essig"
    assert attrs.get("erftverband_station_name") == "Essig"
    assert attrs.get("erftverband_waterbody") == "Orbach"
    assert attrs.get("erftverband_sensor_role") == "water_level"
    assert attrs.get("erftverband_source") == "HOWIS"
    assert "erftverband_source_url" in attrs
    assert "Pegel_Essig_zr.html" in attrs["erftverband_source_url"]


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_discharge_has_metadata(hass, init_integration) -> None:
    state = hass.states.get("sensor.orbach_essig_discharge")
    assert state is not None
    attrs = state.attributes
    assert attrs.get("erftverband_riverlevel") is True
    assert attrs.get("erftverband_station_id") == "essig"
    assert attrs.get("erftverband_sensor_role") == "discharge"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_trend_has_metadata(hass, init_integration) -> None:
    state = hass.states.get("sensor.orbach_essig_water_level_trend")
    assert state is not None
    attrs = state.attributes
    assert attrs.get("erftverband_sensor_role") == "water_level_trend"
    assert attrs.get("erftverband_station_id") == "essig"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_discharge_trend_has_metadata(hass, init_integration) -> None:
    state = hass.states.get("sensor.orbach_essig_discharge_trend")
    assert state is not None
    attrs = state.attributes
    assert attrs.get("erftverband_sensor_role") == "discharge_trend"
    assert attrs.get("erftverband_station_id") == "essig"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_last_measurement_has_metadata(hass, init_integration) -> None:
    state = hass.states.get("sensor.orbach_essig_last_measurement")
    assert state is not None
    attrs = state.attributes
    assert attrs.get("erftverband_sensor_role") == "last_measurement"
    assert attrs.get("erftverband_station_id") == "essig"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_data_age_has_metadata(hass, init_integration) -> None:
    state = hass.states.get("sensor.orbach_essig_data_age")
    assert state is not None
    attrs = state.attributes
    assert attrs.get("erftverband_sensor_role") == "data_age"
    assert attrs.get("erftverband_station_id") == "essig"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_flood_status_has_metadata(hass, init_integration) -> None:
    state = hass.states.get("sensor.orbach_essig_flood_status")
    assert state is not None
    attrs = state.attributes
    assert attrs.get("erftverband_sensor_role") == "flood_status"
    assert attrs.get("erftverband_station_id") == "essig"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_binary_sensors_have_metadata(hass, init_integration) -> None:
    stale = hass.states.get("binary_sensor.orbach_essig_data_stale")
    assert stale is not None
    assert stale.attributes.get("erftverband_sensor_role") == "data_stale"
    assert stale.attributes.get("erftverband_station_id") == "essig"

    alarm = hass.states.get("binary_sensor.orbach_essig_flood_alert")
    assert alarm is not None
    assert alarm.attributes.get("erftverband_sensor_role") == "flood_alarm"
    assert alarm.attributes.get("erftverband_station_id") == "essig"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_source_reachable_has_global_metadata(hass, init_integration) -> None:
    state = hass.states.get("binary_sensor.erftverband_howis_source_reachable")
    assert state is not None
    attrs = state.attributes
    assert attrs.get("erftverband_riverlevel") is True
    assert attrs.get("erftverband_sensor_role") == "source_reachable"
    assert attrs.get("erftverband_station_id") is None
    assert attrs.get("erftverband_source") == "HOWIS"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_all_essig_entities_same_station_id(hass, init_integration) -> None:
    essig_entities = [
        "sensor.orbach_essig_water_level",
        "sensor.orbach_essig_discharge",
        "sensor.orbach_essig_water_level_trend",
        "sensor.orbach_essig_discharge_trend",
        "sensor.orbach_essig_last_measurement",
        "sensor.orbach_essig_data_age",
        "sensor.orbach_essig_flood_status",
        "binary_sensor.orbach_essig_data_stale",
        "binary_sensor.orbach_essig_flood_alert",
    ]

    station_ids = set()
    for eid in essig_entities:
        state = hass.states.get(eid)
        assert state is not None, f"Missing entity {eid}"
        station_ids.add(state.attributes.get("erftverband_station_id"))

    assert station_ids == {"essig"}


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_roles_are_unique_per_station(hass, init_integration) -> None:
    from homeassistant.helpers.entity_registry import async_get as get_er

    er = get_er(hass)
    station_roles: dict[str, list[str]] = {}
    for entry in er.entities.values():
        if entry.platform != DOMAIN:
            continue
        state = hass.states.get(entry.entity_id)
        if state is None:
            continue
        sid = state.attributes.get("erftverband_station_id")
        role = state.attributes.get("erftverband_sensor_role")
        if sid is None or role is None:
            continue
        station_roles.setdefault(sid, []).append(role)

    for sid, roles in station_roles.items():
        assert len(set(roles)) == len(roles), f"Duplicate roles for station {sid}: {roles}"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_flood_status_extra_attributes_preserved(hass, init_integration) -> None:
    state = hass.states.get("sensor.orbach_essig_flood_status")
    assert state is not None
    attrs = state.attributes
    assert attrs.get("erftverband_riverlevel") is True
    assert attrs.get("mw_cm") == 15.0
    assert attrs.get("hq10_cm") == 144.0
    assert attrs.get("ev_alarm_m3s") == 1.6


def test_javascript_file_exists() -> None:
    js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
    assert js_path.exists(), f"JS file not found at {js_path}"
    content = js_path.read_text(encoding="utf-8")
    assert "customElements.define" in content
    assert "window.customCards" in content
    assert "setConfig" in content
    assert "getGridOptions" in content


def test_javascript_passes_syntax_check() -> None:
    import subprocess

    js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
    result = subprocess.run(
        ["node", "--check", str(js_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"JS syntax error: {result.stderr}"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_static_path_registered(hass, init_integration) -> None:
    registered = hass.data.get(DOMAIN, {}).get(f"{DOMAIN}.static_registered")
    assert registered is True, "Static path was not registered"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_static_path_not_duplicated(hass, init_integration) -> None:
    from homeassistant.config_entries import ConfigEntryState
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry2 = MockConfigEntry(
        domain=DOMAIN,
        data={"station_ids": ["Essig"], "scan_interval": 300, "stale_threshold": 180},
        title="Erftverband River Levels",
        unique_id=f"{DOMAIN}_2",
    )
    entry2.add_to_hass(hass)
    await hass.config_entries.async_setup(entry2.entry_id)
    await hass.async_block_till_done()
    assert entry2.state is ConfigEntryState.LOADED

    registered_count = sum(
        1 for key in hass.data.get(DOMAIN, {}) if key == f"{DOMAIN}.static_registered"
    )
    assert registered_count == 1, "Static path key should appear only once in hass.data"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_station_name_always_set(hass, init_integration) -> None:
    for entity in hass.states.async_all():
        if entity.attributes.get("erftverband_riverlevel") is not True:
            continue
        name = entity.attributes.get("erftverband_station_name")
        assert name is not None, f"station_name missing on {entity.entity_id}"
        assert isinstance(name, str) and len(name) > 0


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_flood_status_has_all_metadata(hass, init_integration) -> None:
    state = hass.states.get("sensor.orbach_essig_flood_status")
    assert state is not None
    attrs = state.attributes
    assert attrs.get("erftverband_riverlevel") is True
    assert attrs.get("erftverband_station_id") == "essig"
    assert attrs.get("erftverband_station_name") == "Essig"
    assert attrs.get("erftverband_waterbody") == "Orbach"
    assert attrs.get("erftverband_sensor_role") == "flood_status"
    assert attrs.get("erftverband_source") == "HOWIS"
    assert "erftverband_source_url" in attrs


def test_javascript_has_fallbacks() -> None:
    js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
    content = js_path.read_text(encoding="utf-8")
    assert "_getStations" in content
    assert "entity.attributes.friendly_name" in content or "rawStationId" in content
    assert '|| ""' in content
    assert ".trim().toLowerCase()" in content


def test_javascript_no_broken_editor_patterns() -> None:
    js_path = FRONTEND_DIR / "erftverband-riverlevel-card.js"
    content = js_path.read_text(encoding="utf-8")
    assert "ErftverbandRiverlevelCard.getStubConfig" not in content, (
        "Editor must not reference ErftverbandRiverlevelCard by name (block-scoped)"
    )
    assert "form.dataset" not in content, "ha-form uses .schema, not .dataset"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_metadata_based_grouping_works(hass, init_integration) -> None:
    all_erftverband = []
    for entity in hass.states.async_all():
        if entity.attributes.get("erftverband_riverlevel") is True:
            all_erftverband.append(entity)

    assert len(all_erftverband) >= 9

    stations = {}
    for entity in all_erftverband:
        sid = entity.attributes.get("erftverband_station_id")
        role = entity.attributes.get("erftverband_sensor_role")
        if sid is None or role is None:
            continue
        stations.setdefault(sid, {})[role] = entity.entity_id

    assert "essig" in stations
    assert stations["essig"].get("water_level") == "sensor.orbach_essig_water_level"
    assert stations["essig"].get("discharge") == "sensor.orbach_essig_discharge"
    assert stations["essig"].get("flood_status") == "sensor.orbach_essig_flood_status"
    assert stations["essig"].get("data_stale") == "binary_sensor.orbach_essig_data_stale"
    assert stations["essig"].get("flood_alarm") == "binary_sensor.orbach_essig_flood_alert"


def test_background_asset_exists() -> None:
    """Background image must exist under the assets directory."""
    asset_path = ASSETS_DIR / "level_background.png"
    assert asset_path.exists(), f"Background image not found at {asset_path}"


def test_background_asset_is_png() -> None:
    """Background image must be a valid PNG."""
    asset_path = ASSETS_DIR / "level_background.png"
    data = asset_path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "Not a valid PNG header"


def test_static_folder_contains_assets() -> None:
    """Static frontend folder must contain the assets subdirectory."""
    assert ASSETS_DIR.is_dir(), "assets/ directory not found in frontend/"
    assert (ASSETS_DIR / "level_background.png").is_file()


def test_background_not_oversized() -> None:
    """Background image width must not exceed 1920 pixels."""
    import subprocess

    asset_path = ASSETS_DIR / "level_background.png"
    result = subprocess.run(
        ["sips", "-g", "pixelWidth", str(asset_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "pixelWidth: " in result.stdout
    width = int(result.stdout.strip().split()[-1])
    assert width <= 1920, f"Image width {width} exceeds 1920px"


def test_static_path_url_and_filesystem_match() -> None:
    """The registered static path must point to the frontend directory."""
    from custom_components.erftverband_riverlevel import _STATIC_PATH

    assert _STATIC_PATH == "/api/erftverband_riverlevel/static"
    frontend = (
        Path(__file__).resolve().parent.parent
        / "custom_components"
        / "erftverband_riverlevel"
        / "frontend"
    )
    assert frontend.is_dir()
