from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Remove editable-install __editable__* entries from sys.path (they are not
# real directories and cause HA's loader to crash when iterating sys.path).
# The __editable__ meta_path finder remains active so imports still work.
sys.path[:] = [p for p in sys.path if not p.startswith("__editable__")]

const_module = import_module("custom_components.erftverband_riverlevel.const")
DETAIL_URL_PATTERN = const_module.DETAIL_URL_PATTERN
DOMAIN = const_module.DOMAIN
PRIMARY_URL = const_module.PRIMARY_URL

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: Any) -> None:
    return


@pytest.fixture
def overview_html() -> str:
    return (FIXTURES / "howis_aktwerte.html").read_text(encoding="utf-8")


@pytest.fixture
def detail_essig_html() -> str:
    return (FIXTURES / "pegel_Essig_zr.html").read_text(encoding="utf-8")


@pytest.fixture
def detail_kirchheim_html() -> str:
    return (FIXTURES / "pegel_Kirchheim_zr.html").read_text(encoding="utf-8")


@pytest.fixture
def detail_niederberg_html() -> str:
    return (FIXTURES / "pegel_Niederberg_zr.html").read_text(encoding="utf-8")


def _mock_detail_url(station_id: str) -> str:
    return DETAIL_URL_PATTERN.format(station_id=station_id)


@pytest.fixture
def mock_api(aioclient_mock: Any, overview_html: str) -> Any:
    aioclient_mock.get(PRIMARY_URL, text=overview_html)
    return aioclient_mock


@pytest.fixture
def mock_api_with_detail(
    aioclient_mock: Any,
    overview_html: str,
    detail_essig_html: str,
) -> Any:
    aioclient_mock.get(PRIMARY_URL, text=overview_html)
    aioclient_mock.get(
        _mock_detail_url("Essig"),
        text=detail_essig_html,
    )
    return aioclient_mock


@pytest.fixture
def mock_api_unreachable(aioclient_mock: Any) -> Any:
    aioclient_mock.get(PRIMARY_URL, exc=TimeoutError())
    return aioclient_mock


@pytest.fixture
def config_entry_data() -> dict[str, Any]:
    return {"station_ids": ["Essig"], "scan_interval": 300, "stale_threshold": 180}


@pytest.fixture
async def init_integration(
    hass: Any,
    mock_api_with_detail: Any,
    config_entry_data: dict[str, Any],
    freezer: Any,
) -> Any:
    freezer.move_to("2026-07-21 18:10:00+02:00")

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
