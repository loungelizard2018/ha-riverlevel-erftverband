from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import async_get as get_device_registry
from homeassistant.helpers.entity_registry import async_get as get_entity_registry

from .const import CONF_STALE_THRESHOLD, CONF_STATIONS, CONF_UPDATE_INTERVAL, DOMAIN
from .coordinator import ErftverbandCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    station_ids = list(entry.data.get(CONF_STATIONS, []))
    update_interval = entry.options.get(CONF_UPDATE_INTERVAL, 300)
    stale_threshold = entry.options.get(CONF_STALE_THRESHOLD, 180)

    coordinator = ErftverbandCoordinator(
        hass=hass,
        session=session,
        station_ids=station_ids,
        update_interval=update_interval,
        stale_threshold=stale_threshold,
    )

    await coordinator.async_load_saved_data()
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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
    ent_reg = get_entity_registry(hass)
    dev_reg = get_device_registry(hass)
    station_ids = list(entry.data.get(CONF_STATIONS, []))
    for station_id in station_ids:
        device_identifiers = {(DOMAIN, station_id)}
        for device_entry in list(dev_reg.devices.values()):
            if device_entry.identifiers & device_identifiers:
                for entity_entry in list(ent_reg.entities.values()):
                    if entity_entry.device_id == device_entry.id:
                        ent_reg.async_remove(entity_entry.entity_id)
                dev_reg.async_remove_device(device_entry.id)
