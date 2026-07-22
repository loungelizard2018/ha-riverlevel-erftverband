from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ERFTVERBAND_RIVERLEVEL,
    ATTR_ERFTVERBAND_SENSOR_ROLE,
    ATTR_ERFTVERBAND_SOURCE,
    ATTR_ERFTVERBAND_SOURCE_URL,
    ATTR_ERFTVERBAND_STATION_ID,
    ATTR_ERFTVERBAND_STATION_NAME,
    ATTR_ERFTVERBAND_WATERBODY,
    DOMAIN,
    LOGGER,
    MANUFACTURER,
)
from .coordinator import ErftverbandCoordinator


class ErftverbandEntity(CoordinatorEntity[ErftverbandCoordinator]):
    _attr_has_entity_name = True
    _attr_erftverband_sensor_role: str | None = None

    def __init__(
        self,
        coordinator: ErftverbandCoordinator,
        station_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._station_id = station_id
        descriptor = coordinator.get_descriptor(station_id)
        if descriptor:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, station_id)},
                name=f"{descriptor.waterbody} \u2013 {descriptor.station_name}",
                manufacturer=MANUFACTURER,
                model="Pegel",
                configuration_url=descriptor.detail_url,
            )
        else:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, station_id)},
                name=station_id,
                manufacturer=MANUFACTURER,
                model="Pegel",
            )
        self._attr_unique_id = f"{DOMAIN}_{station_id}_{self._attr_translation_key}"
        LOGGER.debug(
            "Set unique_id=%s for entity %s (station=%s)",
            self._attr_unique_id,
            self.entity_id if hasattr(self, "entity_id") else "(no entity_id)",
            station_id,
        )

    @property
    def station_id(self) -> str:
        return self._station_id

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        descriptor = self.coordinator.get_descriptor(self._station_id)
        station_id = (
            self._station_id.lower()
            if self._station_id and self._station_id != "_global"
            else None
        )
        attrs: dict[str, Any] = {
            ATTR_ERFTVERBAND_RIVERLEVEL: True,
            ATTR_ERFTVERBAND_STATION_ID: station_id,
            ATTR_ERFTVERBAND_SOURCE: "HOWIS",
        }
        if self._attr_erftverband_sensor_role:
            attrs[ATTR_ERFTVERBAND_SENSOR_ROLE] = self._attr_erftverband_sensor_role
        if descriptor:
            attrs[ATTR_ERFTVERBAND_STATION_NAME] = descriptor.station_name
            attrs[ATTR_ERFTVERBAND_WATERBODY] = descriptor.waterbody
            attrs[ATTR_ERFTVERBAND_SOURCE_URL] = descriptor.detail_url
        else:
            attrs[ATTR_ERFTVERBAND_STATION_NAME] = (
                self._station_id if self._station_id != "_global" else "Erftverband HOWIS"
            )
        return attrs
