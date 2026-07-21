from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN
from .coordinator import ErftverbandCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinator: ErftverbandCoordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "coordinator": {
            "source_reachable": coordinator.source_reachable,
            "cache_used": coordinator.cache_used,
            "update_interval_seconds": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
            "stale_threshold_minutes": coordinator.stale_threshold,
            "station_ids": coordinator._station_ids,
            "last_update": (
                coordinator.data.get("last_update") if isinstance(coordinator.data, dict) else None
            ),
        },
        "stations": {
            sid: sd.to_dict() if hasattr(sd, "to_dict") else str(sd)
            for sid, sd in (coordinator.data or {}).items()
        },
    }


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
) -> dict[str, Any]:
    coordinator: ErftverbandCoordinator = hass.data[DOMAIN][entry.entry_id]
    station_id = None
    for identifier in device.identifiers:
        if len(identifier) == 2 and identifier[0] == DOMAIN:
            station_id = identifier[1]
            break
    station_data = None
    if station_id and coordinator.data:
        station_data = (
            coordinator.data[station_id].to_dict() if station_id in coordinator.data else None
        )
    return {
        "device": {
            "id": device.id,
            "name": device.name,
            "model": device.model,
            "manufacturer": device.manufacturer,
            "identifiers": list(device.identifiers),
            "configuration_url": device.configuration_url,
        },
        "station_id": station_id,
        "station_data": station_data,
        "coordinator": {
            "source_reachable": coordinator.source_reachable,
            "cache_used": coordinator.cache_used,
        },
    }
