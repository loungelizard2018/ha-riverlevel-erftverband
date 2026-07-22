from __future__ import annotations

import pytest

from custom_components.erftverband_riverlevel.const import DOMAIN


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_setup_entry(hass, init_integration) -> None:
    assert DOMAIN in hass.data
    assert init_integration.entry_id in hass.data[DOMAIN]
    coordinator = hass.data[DOMAIN][init_integration.entry_id]
    from custom_components.erftverband_riverlevel.coordinator import (
        ErftverbandCoordinator,
    )

    assert isinstance(coordinator, ErftverbandCoordinator)


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_unload_entry(hass, init_integration) -> None:
    assert await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    assert init_integration.entry_id not in hass.data[DOMAIN]


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_reload_entry(hass, init_integration) -> None:
    await hass.config_entries.async_reload(init_integration.entry_id)
    await hass.async_block_till_done()
    assert DOMAIN in hass.data
    assert init_integration.entry_id in hass.data[DOMAIN]


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_update_listener_reloads_entry(hass, init_integration) -> None:
    from custom_components.erftverband_riverlevel.const import CONF_SCAN_INTERVAL

    hass.config_entries.async_update_entry(
        init_integration,
        options={CONF_SCAN_INTERVAL: 600},
    )
    await hass.async_block_till_done()

    assert DOMAIN in hass.data
    assert init_integration.entry_id in hass.data[DOMAIN]
    coordinator = hass.data[DOMAIN][init_integration.entry_id]
    from custom_components.erftverband_riverlevel.coordinator import (
        ErftverbandCoordinator,
    )

    assert isinstance(coordinator, ErftverbandCoordinator)
    assert coordinator.update_interval.total_seconds() == 600


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_device_created(hass, init_integration) -> None:
    from homeassistant.helpers.device_registry import async_get as get_dr

    from custom_components.erftverband_riverlevel.const import DOMAIN

    dr = get_dr(hass)
    device = dr.async_get_device(identifiers={(DOMAIN, "Essig")})
    assert device is not None
    assert device.name == "Orbach \u2013 Essig"
    assert device.manufacturer == "Erftverband"
    assert device.model == "Pegel"
