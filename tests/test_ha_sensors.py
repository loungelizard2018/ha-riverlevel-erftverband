from __future__ import annotations

import pytest

from custom_components.erftverband_riverlevel.const import DOMAIN


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_sensors_created(hass, init_integration) -> None:
    from homeassistant.helpers.entity_registry import async_get as get_er

    er = get_er(hass)
    erftverband_entities = [entry for entry in er.entities.values() if entry.platform == DOMAIN]
    assert len(erftverband_entities) > 0


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_water_level_sensor(hass, init_integration) -> None:
    state = hass.states.get("sensor.essig_orbach_water_level")
    assert state is not None
    assert state.state == "0.0"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_discharge_sensor(hass, init_integration) -> None:
    state = hass.states.get("sensor.essig_orbach_discharge")
    assert state is not None
    assert state.state == "0.0"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_flood_status_sensor(hass, init_integration) -> None:
    state = hass.states.get("sensor.essig_orbach_flood_status")
    assert state is not None
    assert state.state == "normal"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_binary_sensors_created(hass, init_integration) -> None:
    for entity_id in (
        "binary_sensor.essig_orbach_data_stale",
        "binary_sensor.essig_orbach_flood_alert",
        "binary_sensor.erftverband_howis_source_reachable",
    ):
        state = hass.states.get(entity_id)
        assert state is not None, f"Missing {entity_id}"

    reachable = hass.states.get("binary_sensor.erftverband_howis_source_reachable")
    assert reachable.state == "on"

    stale = hass.states.get("binary_sensor.essig_orbach_data_stale")
    assert stale.state == "off"

    alert = hass.states.get("binary_sensor.essig_orbach_flood_alert")
    assert alert.state == "off"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_last_measurement_sensor(hass, init_integration) -> None:
    state = hass.states.get("sensor.essig_orbach_last_measurement")
    assert state is not None
    assert state.state == "2026-07-21T16:01:00+00:00"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_wl_trend_sensor(hass, init_integration) -> None:
    state = hass.states.get("sensor.essig_orbach_water_level_trend")
    assert state is not None


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_q_trend_sensor(hass, init_integration) -> None:
    state = hass.states.get("sensor.essig_orbach_discharge_trend")
    assert state is not None


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_data_age_sensor(hass, init_integration) -> None:
    state = hass.states.get("sensor.essig_orbach_data_age")
    assert state is not None
