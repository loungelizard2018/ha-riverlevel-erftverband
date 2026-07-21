from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, FloodStatus
from .coordinator import ErftverbandCoordinator
from .entity import ErftverbandEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ErftverbandCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []
    for station_id in coordinator._station_ids:
        entities.append(SourceReachableSensor(coordinator, station_id))
        entities.append(DataStaleSensor(coordinator, station_id))
        entities.append(FloodAlertSensor(coordinator, station_id))

    async_add_entities(entities)


class SourceReachableSensor(ErftverbandEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_registry_visible_default = True
    _attr_translation_key = "source_reachable"

    def __init__(
        self,
        coordinator: ErftverbandCoordinator,
        station_id: str,
    ) -> None:
        self._station_id = station_id
        from .models import StationData

        station = None
        if coordinator.data and station_id in coordinator.data:
            station = coordinator.data[station_id]
        super().__init__(
            coordinator,
            station
            or StationData(
                station_id=station_id,
                name=station_id,
                waterbody="",
            ),
            unique_id_suffix="source_reachable",
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.source_reachable

    @property
    def available(self) -> bool:
        return True


class DataStaleSensor(ErftverbandEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_translation_key = "data_stale"

    def __init__(
        self,
        coordinator: ErftverbandCoordinator,
        station_id: str,
    ) -> None:
        self._station_id = station_id
        from .models import StationData

        station = None
        if coordinator.data and station_id in coordinator.data:
            station = coordinator.data[station_id]
        super().__init__(
            coordinator,
            station
            or StationData(
                station_id=station_id,
                name=station_id,
                waterbody="",
            ),
            unique_id_suffix="data_stale",
        )

    @property
    def is_on(self) -> bool:
        sd = self.station_data
        if sd is None or sd.measured_at is None:
            return True
        now = datetime.now(tz=sd.measured_at.tzinfo)
        age = now - sd.measured_at
        threshold = timedelta(minutes=self.coordinator.stale_threshold)
        return age > threshold

    @property
    def available(self) -> bool:
        return True


class FloodAlertSensor(ErftverbandEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _attr_translation_key = "flood_alert"

    def __init__(
        self,
        coordinator: ErftverbandCoordinator,
        station_id: str,
    ) -> None:
        self._station_id = station_id
        from .models import StationData

        station = None
        if coordinator.data and station_id in coordinator.data:
            station = coordinator.data[station_id]
        super().__init__(
            coordinator,
            station
            or StationData(
                station_id=station_id,
                name=station_id,
                waterbody="",
            ),
            unique_id_suffix="flood_alert",
        )

    @property
    def is_on(self) -> bool:
        sd = self.station_data
        if sd is None:
            return False
        from .sensor import _compute_flood_status

        status = _compute_flood_status(sd)
        return status != FloodStatus.NORMAL and status != FloodStatus.UNKNOWN

    @property
    def available(self) -> bool:
        sd = self.station_data
        return sd is not None
