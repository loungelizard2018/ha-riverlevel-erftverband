from __future__ import annotations

from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceRegistry, async_get

from .api import ErftverbandApi
from .const import (
    CONF_LOAD_ALL_STATIONS,
    CONF_SCAN_INTERVAL,
    CONF_STALE_THRESHOLD,
    CONF_STATION_IDS,
    DEFAULT_LOAD_ALL_STATIONS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STALE_THRESHOLD,
    DOMAIN,
    LOGGER,
)
from .coordinator import ErftverbandCoordinator
from .models import StationDescriptor

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

_STATIC_PATH = "/api/erftverband_riverlevel/static"
_STATIC_REGISTERED = f"{DOMAIN}.static_registered"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if not hass.data.get(DOMAIN, {}).get(_STATIC_REGISTERED):
        frontend_path = Path(__file__).parent / "frontend"
        if frontend_path.is_dir():
            from homeassistant.components.http import StaticPathConfig

            http = getattr(hass, "http", None)
            if http is not None:
                await http.async_register_static_paths(
                    [StaticPathConfig(str(_STATIC_PATH), str(frontend_path), cache_headers=False)]
                )
            hass.data.setdefault(DOMAIN, {})[_STATIC_REGISTERED] = True

    session = async_get_clientsession(hass)
    api = ErftverbandApi(session)

    load_all: bool = entry.options.get(
        CONF_LOAD_ALL_STATIONS, entry.data.get(CONF_LOAD_ALL_STATIONS, DEFAULT_LOAD_ALL_STATIONS)
    )

    scan_interval: int = entry.options.get(
        CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    stale_threshold: int = entry.options.get(
        CONF_STALE_THRESHOLD, entry.data.get(CONF_STALE_THRESHOLD, DEFAULT_STALE_THRESHOLD)
    )

    station_ids: set[str] | None = None
    descriptors: dict[str, StationDescriptor] | None = None

    if load_all:
        try:
            descriptors = await api.fetch_station_descriptors()
            station_ids = set(descriptors.keys())
            LOGGER.info(
                "HOWIS station catalog discovered: %d stations",
                len(descriptors),
            )
        except Exception as exc:
            LOGGER.warning(
                "Failed to fetch station descriptors: %s. "
                "Cannot enable load_all_stations. "
                "Previously configured stations continue to work.",
                exc,
            )

    if station_ids is None:
        station_ids = set(
            entry.options.get(CONF_STATION_IDS, entry.data.get(CONF_STATION_IDS, []))
        )

    LOGGER.info(
        "HOWIS stations configured: %d stations",
        len(station_ids),
    )

    coordinator = ErftverbandCoordinator(
        hass=hass,
        api=api,
        station_ids=station_ids,
        scan_interval=scan_interval,
        stale_threshold=stale_threshold,
    )

    if descriptors:
        coordinator.set_descriptors(descriptors)

    await coordinator.async_load_stored_data()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    load_all: bool = entry.data.get(CONF_LOAD_ALL_STATIONS, DEFAULT_LOAD_ALL_STATIONS)
    device_registry: DeviceRegistry = async_get(hass)

    if load_all:
        for device in list(device_registry.devices.values()):
            if any(identifier[0] == DOMAIN for identifier in device.identifiers):
                device_registry.async_remove_device(device.id)
    else:
        station_ids: set[str] = set(entry.data.get(CONF_STATION_IDS, []))
        for sid in station_ids:
            device = device_registry.async_get_device(identifiers={(DOMAIN, sid)})
            if device:
                device_registry.async_remove_device(device.id)
