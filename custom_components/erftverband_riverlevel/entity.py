from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER, MANUFACTURER
from .coordinator import ErftverbandCoordinator


class ErftverbandEntity(CoordinatorEntity[ErftverbandCoordinator]):
    _attr_has_entity_name = True

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
                name=f"{descriptor.station_name} ({descriptor.waterbody})",
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
