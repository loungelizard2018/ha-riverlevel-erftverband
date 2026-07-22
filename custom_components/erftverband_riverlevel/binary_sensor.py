from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    STATE_NORMAL,
    STATE_UNKNOWN,
)
from .coordinator import ErftverbandCoordinator
from .entity import ErftverbandEntity
from .sensor import evaluate_flood_alert


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ErftverbandCoordinator = hass.data[DOMAIN][entry.entry_id]
    station_ids: set[str] = coordinator._station_ids

    entities: list[ErftverbandEntity] = []
    for sid in station_ids:
        entities.extend(
            [
                DataStaleBinarySensor(coordinator, sid),
                FloodAlertBinarySensor(coordinator, sid),
            ]
        )

    entities.append(SourceReachableBinarySensor(coordinator, "_global"))
    async_add_entities(entities)


class ErftverbandBinarySensor(ErftverbandEntity, BinarySensorEntity):
    _attr_should_poll = False


class SourceReachableBinarySensor(ErftverbandBinarySensor):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "source_reachable"
    _attr_unique_id = "erftverband_source_reachable"
    _attr_has_entity_name = True
    _attr_erftverband_sensor_role = "source_reachable"

    def __init__(
        self,
        coordinator: ErftverbandCoordinator,
        station_id: str,
    ) -> None:
        super().__init__(coordinator, station_id)
        self._attr_entity_registry_enabled_default = True
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "_global")},
            "name": "Erftverband HOWIS",
            "manufacturer": "Erftverband",
        }

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data
        if data is None:
            return False
        return data.source_reachable

    @property
    def available(self) -> bool:
        return True


class DataStaleBinarySensor(ErftverbandBinarySensor):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_translation_key = "data_stale"
    _attr_erftverband_sensor_role = "data_stale"

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data
        if data is None:
            return True
        station = data.stations.get(self._station_id)
        if station is None:
            return True
        age = station.age_minutes
        if age is None:
            return True
        return self.coordinator.is_stale(age)


class FloodAlertBinarySensor(ErftverbandBinarySensor):
    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _attr_translation_key = "flood_alert"
    _attr_erftverband_sensor_role = "flood_alarm"

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data
        if data is None:
            return False
        station = data.stations.get(self._station_id)
        if station is None:
            return False

        age = station.age_minutes
        if age is not None and self.coordinator.is_stale(age):
            return False

        meta = self.coordinator.get_metadata(self._station_id)
        if meta is None or meta.thresholds is None:
            return False

        t = meta.thresholds
        flood_state = evaluate_flood_alert(
            station.water_level_cm,
            station.discharge_m3s,
            t.ev_alarm_cm,
            t.ev_alarm_m3s,
            t.hq10_cm,
            t.hq10_m3s,
            t.hq100_cm,
            t.hq100_m3s,
            t.hqextrem_cm,
            t.hqextrem_m3s,
        )
        return flood_state not in (STATE_NORMAL, STATE_UNKNOWN)
