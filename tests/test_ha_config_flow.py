from __future__ import annotations

from pathlib import Path

import pytest

from custom_components.erftverband_riverlevel.const import (
    CONF_SCAN_INTERVAL,
    CONF_STALE_THRESHOLD,
    CONF_STATION_IDS,
    DOMAIN,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.mark.usefixtures("mock_api")
async def test_user_step_success(hass, mock_api) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_STATION_IDS: ["Essig"], CONF_SCAN_INTERVAL: 300, CONF_STALE_THRESHOLD: 180},
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "Erftverband HOWIS"
    assert result["data"][CONF_STATION_IDS] == ["Essig"]


@pytest.mark.usefixtures("mock_api")
async def test_user_step_no_stations_selected(hass, mock_api) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_STATION_IDS: [], CONF_SCAN_INTERVAL: 300, CONF_STALE_THRESHOLD: 180},
    )
    assert result["type"] == "form"
    assert result["errors"]["base"] == "no_stations"
