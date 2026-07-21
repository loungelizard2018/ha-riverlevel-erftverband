from __future__ import annotations

import pytest

from custom_components.erftverband_riverlevel.const import (
    DOMAIN,
    OVERVIEW_URL,
)


@pytest.mark.usefixtures("mock_api_unreachable")
async def test_coordinator_timeout(hass, aioclient_mock) -> None:
    from homeassistant.config_entries import ConfigEntryState
    from homeassistant.setup import async_setup_component
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"stations": ["Essig"]},
        title="Erftverband River Levels",
        unique_id=DOMAIN,
    )
    entry.add_to_hass(hass)
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_coordinator_http_error(hass, aioclient_mock) -> None:
    aioclient_mock.get(OVERVIEW_URL, status=500)
    from homeassistant.config_entries import ConfigEntryState
    from homeassistant.setup import async_setup_component
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"stations": ["Essig"]},
        title="Erftverband River Levels",
        unique_id=DOMAIN,
    )
    entry.add_to_hass(hass)
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.usefixtures("mock_api_with_detail")
async def test_coordinator_successful_update(hass, init_integration) -> None:
    coordinator = hass.data[DOMAIN][init_integration.entry_id]
    assert coordinator.data is not None
    assert "Essig" in coordinator.data
    assert coordinator.source_reachable is True
    assert coordinator.cache_used is False


async def test_coordinator_cache_fallback(hass, aioclient_mock, detail_essig_html) -> None:
    from homeassistant.setup import async_setup_component
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.erftverband_riverlevel.const import DETAIL_URL_TEMPLATE

    aioclient_mock.get(OVERVIEW_URL, text="<html>empty</html>")
    aioclient_mock.get(
        DETAIL_URL_TEMPLATE.format(station_id="Essig"),
        text=detail_essig_html,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"stations": ["Essig"]},
        title="Erftverband River Levels",
        unique_id=DOMAIN,
    )
    entry.add_to_hass(hass)
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    from homeassistant.config_entries import ConfigEntryState

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_coordinator_fetch_station_details(
    hass, init_integration, aioclient_mock, detail_essig_html
) -> None:
    from custom_components.erftverband_riverlevel.const import DETAIL_URL_TEMPLATE

    coordinator = hass.data[DOMAIN][init_integration.entry_id]
    detail_url = DETAIL_URL_TEMPLATE.format(station_id="Essig")
    aioclient_mock.get(detail_url, text=detail_essig_html)

    result = await coordinator.fetch_station_details(["Essig"])
    assert "Essig" in result
    assert result["Essig"].station_id == "Essig"


async def test_coordinator_fetch_station_details_failure(
    hass, aioclient_mock, overview_html
) -> None:
    from homeassistant.setup import async_setup_component
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    aioclient_mock.get(OVERVIEW_URL, text=overview_html)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"stations": ["Essig"]},
        title="Erftverband River Levels",
        unique_id=DOMAIN,
    )
    entry.add_to_hass(hass)
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][entry.entry_id]

    result = await coordinator.fetch_station_details(["Essig"])
    assert result == {}
