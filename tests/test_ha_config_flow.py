from __future__ import annotations

import pytest

from custom_components.erftverband_riverlevel.const import (
    CONF_STALE_THRESHOLD,
    CONF_STATIONS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_STALE_THRESHOLD,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)


@pytest.mark.usefixtures("mock_api")
async def test_user_step_success(hass, mock_api) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert CONF_STATIONS in result["data_schema"].schema

    essig_id = "Essig"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_STATIONS: [essig_id]},
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "Erftverband River Levels"
    assert result["data"][CONF_STATIONS] == [essig_id]


@pytest.mark.usefixtures("mock_api")
async def test_user_step_no_stations_selected(hass, mock_api) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_STATIONS: []},
    )
    assert result["type"] == "form"
    assert result["errors"] == {CONF_STATIONS: "at_least_one"}


@pytest.mark.usefixtures("mock_api_unreachable")
async def test_user_step_cannot_connect(hass, mock_api_unreachable) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"


async def test_user_step_no_stations_found(hass, aioclient_mock) -> None:
    from custom_components.erftverband_riverlevel.const import OVERVIEW_URL

    aioclient_mock.get(OVERVIEW_URL, text="<html>empty</html>")
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == "abort"
    assert result["reason"] == "no_stations_found"


@pytest.mark.usefixtures("mock_api")
async def test_duplicate_entry_blocked(hass, mock_api) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_STATIONS: ["Essig"]},
    )
    assert result["type"] == "create_entry"

    result2 = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result2 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {CONF_STATIONS: ["Kirchheim"]},
    )
    assert result2["type"] == "abort"
    assert result2["reason"] == "already_configured"


@pytest.mark.usefixtures("mock_api")
async def test_options_flow_stations_step(hass, init_integration, mock_api) -> None:
    entry = init_integration
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "stations"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_STATIONS: ["Essig", "Kirchheim"]},
    )
    assert result["type"] == "form"
    assert result["step_id"] == "settings"


@pytest.mark.usefixtures("mock_api")
async def test_options_flow_settings_step(hass, init_integration, mock_api) -> None:
    entry = init_integration
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_STATIONS: ["Essig"]},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
            CONF_STALE_THRESHOLD: DEFAULT_STALE_THRESHOLD,
        },
    )
    assert result["type"] == "create_entry"
    assert result["data"][CONF_UPDATE_INTERVAL] == DEFAULT_UPDATE_INTERVAL
    assert result["data"][CONF_STALE_THRESHOLD] == DEFAULT_STALE_THRESHOLD


@pytest.mark.usefixtures("mock_api")
async def test_options_flow_no_stations(hass, init_integration, mock_api) -> None:
    entry = init_integration
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_STATIONS: []},
    )
    assert result["type"] == "form"
    assert result["errors"] == {CONF_STATIONS: "at_least_one"}
