from __future__ import annotations

from pathlib import Path

import pytest

from custom_components.erftverband_riverlevel.const import (
    DOMAIN,
    PRIMARY_URL,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.mark.usefixtures("mock_api")
async def test_coordinator_successful_update(hass, init_integration) -> None:
    coordinator = hass.data[DOMAIN][init_integration.entry_id]
    assert coordinator.data is not None
    assert "Essig" in coordinator.data.stations


async def test_coordinator_http_error(hass, aioclient_mock) -> None:
    aioclient_mock.get(PRIMARY_URL, status=500)
    from homeassistant.config_entries import ConfigEntryState
    from homeassistant.setup import async_setup_component
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"station_ids": ["Essig"], "scan_interval": 300, "stale_threshold": 180},
        title="Erftverband River Levels",
        unique_id=DOMAIN,
    )
    entry.add_to_hass(hass)
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
