from __future__ import annotations

import pytest


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_config_entry_diagnostics(hass, init_integration) -> None:
    from custom_components.erftverband_riverlevel.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    result = await async_get_config_entry_diagnostics(hass, init_integration)
    assert "entry" in result
    assert result["entry"]["entry_id"] == init_integration.entry_id
    assert result["entry"]["data"]["stations"] == ["Essig"]
    assert "coordinator" in result
    assert result["coordinator"]["source_reachable"] is True
    assert result["coordinator"]["cache_used"] is False
    assert "stations" in result
    assert "Essig" in result["stations"]


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_device_diagnostics(hass, init_integration) -> None:
    from homeassistant.helpers.device_registry import async_get as get_dr

    from custom_components.erftverband_riverlevel.const import DOMAIN
    from custom_components.erftverband_riverlevel.diagnostics import (
        async_get_device_diagnostics,
    )

    dr = get_dr(hass)
    device = dr.async_get_device(identifiers={(DOMAIN, "Essig")})
    assert device is not None

    result = await async_get_device_diagnostics(hass, init_integration, device)
    assert "device" in result
    assert result["station_id"] == "Essig"
    assert "station_data" in result
    assert "coordinator" in result
