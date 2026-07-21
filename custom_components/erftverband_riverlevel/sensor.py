from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    ATTR_THRESHOLDS,
    DOMAIN,
    FloodStatus,
)
from .coordinator import ErftverbandCoordinator
from .entity import ErftverbandEntity
from .models import StationData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ErftverbandCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []
    for station_id in coordinator._station_ids:
        entities.append(WaterLevelSensor(coordinator, station_id))
        entities.append(DischargeSensor(coordinator, station_id))
        entities.append(WaterLevelTrendSensor(coordinator, station_id))
        entities.append(DischargeTrendSensor(coordinator, station_id))
        entities.append(LastMeasurementSensor(coordinator, station_id))
        entities.append(DataAgeSensor(coordinator, station_id))
        entities.append(FloodStatusSensor(coordinator, station_id))

    async_add_entities(entities)


class ErftverbandSensor(ErftverbandEntity, SensorEntity):
    _sensor_type = ""

    def __init__(
        self,
        coordinator: ErftverbandCoordinator,
        station_id: str,
    ) -> None:
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
            unique_id_suffix=self._sensor_type,
        )
        self._station_id = station_id


class WaterLevelSensor(ErftverbandSensor):
    _sensor_type = "water_level"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "cm"
    _attr_translation_key = "water_level"
    _attr_suggested_display_precision = 0

    @property
    def native_value(self) -> StateType:
        sd = self.station_data
        if sd is None:
            return None
        return sd.water_level_cm


class DischargeSensor(ErftverbandSensor):
    _sensor_type = "discharge"
    _attr_device_class = SensorDeviceClass.VOLUME_FLOW_RATE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "m\u00b3/s"
    _attr_translation_key = "discharge"
    _attr_suggested_display_precision = 2

    @property
    def native_value(self) -> StateType:
        sd = self.station_data
        if sd is None:
            return None
        return sd.discharge_m3s


class WaterLevelTrendSensor(ErftverbandSensor):
    _sensor_type = "wl_trend"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "cm/h"
    _attr_translation_key = "wl_trend"
    _attr_suggested_display_precision = 0

    @property
    def native_value(self) -> StateType:
        sd = self.station_data
        if sd is None:
            return None
        return sd.wl_trend


class DischargeTrendSensor(ErftverbandSensor):
    _sensor_type = "q_trend"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "m\u00b3/s/h"
    _attr_translation_key = "q_trend"
    _attr_suggested_display_precision = 3

    @property
    def native_value(self) -> StateType:
        sd = self.station_data
        if sd is None:
            return None
        return sd.q_trend


class LastMeasurementSensor(ErftverbandSensor):
    _sensor_type = "measured_at"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_translation_key = "measured_at"

    @property
    def native_value(self) -> datetime | None:
        sd = self.station_data
        if sd is None:
            return None
        return sd.measured_at


class DataAgeSensor(ErftverbandSensor):
    _sensor_type = "data_age"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "min"
    _attr_entity_registry_visible_default = True
    _attr_translation_key = "data_age"

    @property
    def native_value(self) -> int | None:
        sd = self.station_data
        if sd is None or sd.measured_at is None:
            return None
        now = datetime.now(tz=sd.measured_at.tzinfo)
        delta = now - sd.measured_at
        return int(delta.total_seconds() // 60)

    @property
    def available(self) -> bool:
        return True


def _compute_flood_status(station: StationData) -> FloodStatus:
    wl = station.water_level_cm
    q = station.discharge_m3s
    th = station.thresholds

    if wl is None and q is None:
        return FloodStatus.UNKNOWN

    status = FloodStatus.NORMAL

    if wl is not None and th.hqextrem_w is not None and wl >= th.hqextrem_w:
        return FloodStatus.EXTREME
    if q is not None and th.hqextrem_q is not None and q >= th.hqextrem_q:
        return FloodStatus.EXTREME

    if wl is not None and th.hq100_w is not None and wl >= th.hq100_w:
        return FloodStatus.HQ100
    if q is not None and th.hq100_q is not None and q >= th.hq100_q:
        return FloodStatus.HQ100

    if wl is not None and th.hq10_w is not None and wl >= th.hq10_w:
        return FloodStatus.HQ10
    if q is not None and th.hq10_q is not None and q >= th.hq10_q:
        return FloodStatus.HQ10

    if wl is not None and th.ev_w is not None and wl >= th.ev_w:
        return FloodStatus.EV_ACTION
    if q is not None and th.ev_q is not None and q >= th.ev_q:
        return FloodStatus.EV_ACTION

    return status


class FloodStatusSensor(ErftverbandSensor):
    _sensor_type = "flood_status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(FloodStatus)
    _attr_translation_key = "flood_status"

    @property
    def native_value(self) -> str | None:
        sd = self.station_data
        if sd is None:
            return None
        return _compute_flood_status(sd)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = {}
        sd = self.station_data
        if sd is not None and sd.thresholds:
            attrs[ATTR_THRESHOLDS] = sd.thresholds.to_dict()
        return attrs
