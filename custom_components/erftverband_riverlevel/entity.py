from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DETAIL_URL_TEMPLATE, DOMAIN, MANUFACTURER
from .coordinator import ErftverbandCoordinator
from .models import StationData


class ErftverbandEntity(CoordinatorEntity[ErftverbandCoordinator]):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ErftverbandCoordinator,
        station: StationData,
        unique_id_suffix: str = "",
    ) -> None:
        super().__init__(coordinator)
        self._station_id = station.station_id
        self._station_name = station.name
        self._waterbody = station.waterbody
        self._attr_unique_id = (
            f"{station.station_id}_{unique_id_suffix}" if unique_id_suffix else station.station_id
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station.station_id)},
            name=f"{station.name} ({station.waterbody})",
            manufacturer=MANUFACTURER,
            model="Pegel",
            configuration_url=DETAIL_URL_TEMPLATE.format(station_id=station.station_id),
        )
        self._attr_translation_key = None

    @property
    def station_data(self) -> StationData | None:
        if self.coordinator.data and self._station_id in self.coordinator.data:
            return self.coordinator.data[self._station_id]
        return None
