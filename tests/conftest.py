from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.erftverband_riverlevel.const import (
    DETAIL_URL_TEMPLATE,
    DOMAIN,
    OVERVIEW_URL,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: Any) -> None:
    return


@pytest.fixture
def overview_html() -> str:
    return (FIXTURES / "overview.html").read_text(encoding="utf-8")


@pytest.fixture
def detail_essig_html() -> str:
    return (FIXTURES / "detail_Essig.html").read_text(encoding="utf-8")


@pytest.fixture
def detail_kirchheim_html() -> str:
    return (FIXTURES / "detail_Kirchheim.html").read_text(encoding="utf-8")


@pytest.fixture
def detail_niederberg_html() -> str:
    return (FIXTURES / "detail_Niederberg.html").read_text(encoding="utf-8")


def _mock_detail_url(station_id: str) -> str:
    return DETAIL_URL_TEMPLATE.format(station_id=station_id)


@pytest.fixture
def mock_api(aioclient_mock: Any, overview_html: str) -> Any:
    aioclient_mock.get(OVERVIEW_URL, text=overview_html)
    return aioclient_mock


@pytest.fixture
def mock_api_with_detail(
    aioclient_mock: Any,
    overview_html: str,
    detail_essig_html: str,
) -> Any:
    aioclient_mock.get(OVERVIEW_URL, text=overview_html)
    aioclient_mock.get(
        _mock_detail_url("Essig"),
        text=detail_essig_html,
    )
    return aioclient_mock


@pytest.fixture
def mock_api_unreachable(aioclient_mock: Any) -> Any:
    aioclient_mock.get(OVERVIEW_URL, exc=TimeoutError())
    return aioclient_mock


@pytest.fixture
def config_entry_data() -> dict[str, Any]:
    return {"stations": ["Essig"]}


@pytest.fixture
async def init_integration(
    hass: Any,
    mock_api_with_detail: Any,
    config_entry_data: dict[str, Any],
) -> Any:
    from homeassistant.config_entries import ConfigEntryState

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=config_entry_data,
        title="Erftverband River Levels",
        unique_id=DOMAIN,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    return entry
