from __future__ import annotations

import pytest

from custom_components.erftverband_riverlevel.const import DOMAIN

SENSOR_PREFIX = "sensor.essig_orbach"
BS_PREFIX = "binary_sensor.essig_orbach"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_sensors_created(hass, init_integration) -> None:
    from homeassistant.helpers.entity_registry import async_get as get_er

    er = get_er(hass)
    erftverband_entities = [entry for entry in er.entities.values() if entry.platform == DOMAIN]
    assert len(erftverband_entities) > 0


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_water_level_sensor(hass, init_integration) -> None:
    state = hass.states.get(f"{SENSOR_PREFIX}_distance")
    assert state is not None
    assert state.state == "0.0"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_discharge_sensor(hass, init_integration) -> None:
    state = hass.states.get(f"{SENSOR_PREFIX}_volume_flow_rate")
    assert state is not None
    assert state.state == "0.0"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_flood_status_sensor(hass, init_integration) -> None:
    state = hass.states.get(f"{SENSOR_PREFIX}_3")
    assert state is not None
    assert state.state == "normal"
    assert "thresholds" in state.attributes


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_binary_sensors_created(hass, init_integration) -> None:
    reachable = hass.states.get(f"{BS_PREFIX}_connectivity")
    assert reachable is not None
    assert reachable.state == "on"

    stale = hass.states.get(f"{BS_PREFIX}_problem")
    assert stale is not None

    alert = hass.states.get(f"{BS_PREFIX}_safety")
    assert alert is not None
    assert alert.state == "off"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_last_measurement_sensor(hass, init_integration) -> None:
    state = hass.states.get(f"{SENSOR_PREFIX}_timestamp")
    assert state is not None
    assert state.state != "unavailable"
    assert state.state != "unknown"


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_wl_trend_sensor(hass, init_integration) -> None:
    state = hass.states.get(SENSOR_PREFIX)
    assert state is not None


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_q_trend_sensor(hass, init_integration) -> None:
    state = hass.states.get(f"{SENSOR_PREFIX}_2")
    assert state is not None


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_data_age_sensor(hass, init_integration) -> None:
    state = hass.states.get(f"{SENSOR_PREFIX}_duration")
    assert state is not None
