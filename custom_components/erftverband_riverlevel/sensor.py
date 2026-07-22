from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN,
    FLOOD_STATES,
    STATE_EV_ACTION,
    STATE_EXTREME,
    STATE_HQ10,
    STATE_HQ100,
    STATE_NORMAL,
    STATE_UNKNOWN,
)
from .coordinator import ErftverbandCoordinator
from .entity import ErftverbandEntity


def evaluate_flood_alert(
    water_level_cm: float | None,
    discharge_m3s: float | None,
    ev_alarm_cm: float | None,
    ev_alarm_m3s: float | None,
    hq10_cm: float | None,
    hq10_m3s: float | None,
    hq100_cm: float | None,
    hq100_m3s: float | None,
    hqextrem_cm: float | None,
    hqextrem_m3s: float | None,
) -> str:
    max_state = STATE_NORMAL

    def _check(value: float | None, threshold: float | None) -> bool:
        if value is None or threshold is None:
            return False
        return value >= threshold

    if _check(water_level_cm, hqextrem_cm) or _check(discharge_m3s, hqextrem_m3s):
        max_state = STATE_EXTREME
    elif _check(water_level_cm, hq100_cm) or _check(discharge_m3s, hq100_m3s):
        max_state = STATE_HQ100
    elif _check(water_level_cm, hq10_cm) or _check(discharge_m3s, hq10_m3s):
        max_state = STATE_HQ10
    elif _check(water_level_cm, ev_alarm_cm) or _check(discharge_m3s, ev_alarm_m3s):
        max_state = STATE_EV_ACTION

    return max_state


TZ_BERLIN = ZoneInfo("Europe/Berlin")


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
                WaterLevelSensor(coordinator, sid),
                DischargeSensor(coordinator, sid),
                WaterTrendRawSensor(coordinator, sid),
                DischargeTrendRawSensor(coordinator, sid),
                LastMeasurementSensor(coordinator, sid),
                DataAgeSensor(coordinator, sid),
                FloodStatusSensor(coordinator, sid),
            ]
        )

    async_add_entities(entities)


class ErftverbandSensor(ErftverbandEntity, SensorEntity):
    _attr_should_poll = False

    @property
    def available(self) -> bool:
        data = self.coordinator.data
        if data is None:
            return False
        station_data = data.stations.get(self._station_id)
        if station_data is None:
            return False
        if station_data.age_minutes is not None and self.coordinator.is_stale(
            station_data.age_minutes
        ):
            try:
                cat = self._attr_entity_category
            except AttributeError:
                cat = None
            if cat is None or cat != EntityCategory.DIAGNOSTIC:
                return False
        value = self.native_value
        if value is None:
            return False
        return True


class WaterLevelSensor(ErftverbandSensor):
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "cm"
    _attr_translation_key = "water_level"
    _attr_erftverband_sensor_role = "water_level"

    @property
    def native_value(self) -> StateType:
        data = self.coordinator.data
        if data is None:
            return None
        station = data.stations.get(self._station_id)
        if station is None:
            return None
        return station.water_level_cm


class DischargeSensor(ErftverbandSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "m³/s"
    _attr_translation_key = "discharge"
    _attr_erftverband_sensor_role = "discharge"

    @property
    def native_value(self) -> StateType:
        data = self.coordinator.data
        if data is None:
            return None
        station = data.stations.get(self._station_id)
        if station is None:
            return None
        return station.discharge_m3s


class WaterTrendRawSensor(ErftverbandSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "cm/h"
    _attr_translation_key = "water_trend_raw"
    _attr_erftverband_sensor_role = "water_level_trend"

    @property
    def native_value(self) -> StateType:
        data = self.coordinator.data
        if data is None:
            return None
        station = data.stations.get(self._station_id)
        if station is None:
            return None
        return station.water_trend_cm_h


class DischargeTrendRawSensor(ErftverbandSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "m³/s/h"
    _attr_translation_key = "discharge_trend_raw"
    _attr_erftverband_sensor_role = "discharge_trend"

    @property
    def native_value(self) -> StateType:
        data = self.coordinator.data
        if data is None:
            return None
        station = data.stations.get(self._station_id)
        if station is None:
            return None
        return station.discharge_trend_m3s_h


class LastMeasurementSensor(ErftverbandSensor):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_translation_key = "last_measurement"
    _attr_erftverband_sensor_role = "last_measurement"

    @property
    def native_value(self) -> datetime | None:
        data = self.coordinator.data
        if data is None:
            return None
        station = data.stations.get(self._station_id)
        if station is None or station.measured_at is None:
            return None
        try:
            dt = datetime.fromisoformat(station.measured_at)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TZ_BERLIN)
            return dt
        except ValueError, TypeError:
            return None


class DataAgeSensor(ErftverbandSensor):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "min"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "data_age"
    _attr_erftverband_sensor_role = "data_age"

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> StateType:
        data = self.coordinator.data
        if data is None:
            return None
        station = data.stations.get(self._station_id)
        if station is None:
            return None
        return station.age_minutes


class FloodStatusSensor(ErftverbandSensor):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = FLOOD_STATES
    _attr_translation_key = "flood_status"
    _attr_erftverband_sensor_role = "flood_status"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data
        if data is None:
            return STATE_UNKNOWN
        station = data.stations.get(self._station_id)
        if station is None:
            return STATE_UNKNOWN

        age = station.age_minutes
        if age is not None and self.coordinator.is_stale(age):
            return STATE_UNKNOWN

        meta = self.coordinator.get_metadata(self._station_id)
        if meta is None or meta.thresholds is None:
            return STATE_UNKNOWN

        t = meta.thresholds
        return evaluate_flood_alert(
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

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = dict(super().extra_state_attributes or {})
        meta = self.coordinator.get_metadata(self._station_id)
        if meta is None or meta.thresholds is None:
            return attrs
        t = meta.thresholds
        if t.mw_cm is not None:
            attrs["mw_cm"] = t.mw_cm
        if t.mhw_cm is not None:
            attrs["mhw_cm"] = t.mhw_cm
        if t.ev_alarm_cm is not None:
            attrs["ev_alarm_cm"] = t.ev_alarm_cm
        if t.ev_alarm_m3s is not None:
            attrs["ev_alarm_m3s"] = t.ev_alarm_m3s
        if t.hq10_cm is not None:
            attrs["hq10_cm"] = t.hq10_cm
        if t.hq10_m3s is not None:
            attrs["hq10_m3s"] = t.hq10_m3s
        if t.hq100_cm is not None:
            attrs["hq100_cm"] = t.hq100_cm
        if t.hq100_m3s is not None:
            attrs["hq100_m3s"] = t.hq100_m3s
        if t.hqextrem_cm is not None:
            attrs["hqextrem_cm"] = t.hqextrem_cm
        if t.hqextrem_m3s is not None:
            attrs["hqextrem_m3s"] = t.hqextrem_m3s
        if meta.catchment_area_km2 is not None:
            attrs["catchment_area_km2"] = meta.catchment_area_km2
        return attrs
