from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ErftverbandApi,
    age_minutes,
    iso_with_offset,
    parse_overview_page,
)
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DETAIL_PAGE_TTL,
    DOMAIN,
    LOGGER,
    STORAGE_KEY_LAST_DATA,
    STORAGE_KEY_METADATA,
    STORAGE_VERSION,
)
from .models import (
    CoordinatorData,
    StationDescriptor,
    StationMeasurement,
    StationMetadata,
)

TZ_BERLIN = ZoneInfo("Europe/Berlin")


class ErftverbandCoordinator(DataUpdateCoordinator[CoordinatorData]):
    def __init__(
        self,
        hass: HomeAssistant,
        api: ErftverbandApi,
        station_ids: set[str],
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
        stale_threshold: int = 180,
    ) -> None:
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._api = api
        self._station_ids = station_ids
        self._stale_threshold = stale_threshold
        self._metadata_store = Store[dict[str, Any]](hass, STORAGE_VERSION, STORAGE_KEY_METADATA)
        self._last_data_store = Store[dict[str, Any]](hass, STORAGE_VERSION, STORAGE_KEY_LAST_DATA)
        self._metadata: dict[str, StationMetadata] = {}
        self._descriptors: dict[str, StationDescriptor] = {}
        self._detail_fetch_times: dict[str, datetime] = {}

    @property
    def metadata(self) -> dict[str, StationMetadata]:
        return self._metadata

    @property
    def descriptors(self) -> dict[str, StationDescriptor]:
        return self._descriptors

    async def async_load_stored_data(self) -> None:
        stored_metadata = await self._metadata_store.async_load()
        if stored_metadata:
            for sid, data in stored_metadata.items():
                self._metadata[sid] = StationMetadata(**data)

    async def _async_update_metadata(
        self,
        descriptors: dict[str, StationDescriptor],
    ) -> None:
        now = datetime.now(TZ_BERLIN)
        needs_fetch: list[StationDescriptor] = []
        for sid, desc in descriptors.items():
            if sid not in self._station_ids:
                continue
            meta = self._metadata.get(sid)
            if meta is None:
                needs_fetch.append(desc)
            else:
                fetched = meta.fetched_at
                if fetched:
                    try:
                        fetched_dt = datetime.fromisoformat(fetched)
                        if now - fetched_dt > DETAIL_PAGE_TTL:
                            needs_fetch.append(desc)
                    except ValueError, TypeError:
                        needs_fetch.append(desc)

        if needs_fetch:
            results = await asyncio.gather(
                *[self._api.fetch_station_metadata(d) for d in needs_fetch],
                return_exceptions=True,
            )
            for desc, result in zip(needs_fetch, results):
                if isinstance(result, Exception):
                    LOGGER.warning("Failed to fetch metadata for %s: %s", desc.station_id, result)
                    continue
                self._metadata[desc.station_id] = result
                self._detail_fetch_times[desc.station_id] = now

            await self._metadata_store.async_save(
                {
                    sid: {
                        "station_id": m.station_id,
                        "station_name": m.station_name,
                        "waterbody": m.waterbody,
                        "detail_url": m.detail_url,
                        "catchment_area_km2": m.catchment_area_km2,
                        "fetched_at": m.fetched_at,
                        "thresholds": {
                            "mw_cm": m.thresholds.mw_cm,
                            "mhw_cm": m.thresholds.mhw_cm,
                            "ev_alarm_cm": m.thresholds.ev_alarm_cm,
                            "ev_alarm_m3s": m.thresholds.ev_alarm_m3s,
                            "hq10_cm": m.thresholds.hq10_cm,
                            "hq10_m3s": m.thresholds.hq10_m3s,
                            "hq100_cm": m.thresholds.hq100_cm,
                            "hq100_m3s": m.thresholds.hq100_m3s,
                            "hqextrem_cm": m.thresholds.hqextrem_cm,
                            "hqextrem_m3s": m.thresholds.hqextrem_m3s,
                        },
                    }
                    for sid, m in self._metadata.items()
                    if sid in self._station_ids
                }
            )

    async def _async_update_data(self) -> CoordinatorData:
        fetched_at = datetime.now(TZ_BERLIN)
        data = CoordinatorData(
            fetched_at=iso_with_offset(fetched_at),
        )

        try:
            html = await self._api.fetch_overview()
            measurements = parse_overview_page(html, self._station_ids)
            data.live_fetch_ok = True
            data.source_reachable = True

            for sid in self._station_ids:
                if sid in measurements:
                    data.stations[sid] = measurements[sid]

            if all(sid in data.stations for sid in self._station_ids):
                data.ok = True

            if data.ok:
                await self._last_data_store.async_save(
                    {
                        "stations": {
                            sid: {
                                "measured_at": m.measured_at,
                                "age_minutes": m.age_minutes,
                                "water_level_cm": m.water_level_cm,
                                "water_trend_cm_h": m.water_trend_cm_h,
                                "discharge_m3s": m.discharge_m3s,
                                "discharge_trend_m3s_h": m.discharge_trend_m3s_h,
                            }
                            for sid, m in data.stations.items()
                        },
                        "fetched_at": data.fetched_at,
                    }
                )
                if not self._descriptors:
                    self._descriptors = await self._api.fetch_station_descriptors()

                await self._async_update_metadata(self._descriptors)

        except Exception as err:
            LOGGER.warning("Live fetch failed: %s", err)
            data.error = str(err)
            data.source_reachable = False

            cached = await self._last_data_store.async_load()
            if cached:
                data.cache_used = True
                for sid in self._station_ids:
                    cached_station = cached.get("stations", {}).get(sid)
                    if cached_station:
                        raw_time = cached_station.get("measured_at")
                        parsed_dt = None
                        if raw_time:
                            try:
                                parsed_dt = datetime.fromisoformat(raw_time)
                            except ValueError, TypeError:
                                pass
                        if parsed_dt is not None:
                            if parsed_dt.tzinfo is None:
                                parsed_dt = parsed_dt.replace(tzinfo=TZ_BERLIN)
                            cached_station["age_minutes"] = age_minutes(parsed_dt)
                        data.stations[sid] = StationMeasurement(
                            measured_at=cached_station.get("measured_at"),
                            age_minutes=cached_station.get("age_minutes"),
                            water_level_cm=cached_station.get("water_level_cm"),
                            water_trend_cm_h=cached_station.get("water_trend_cm_h"),
                            discharge_m3s=cached_station.get("discharge_m3s"),
                            discharge_trend_m3s_h=cached_station.get("discharge_trend_m3s_h"),
                        )
                if all(sid in data.stations for sid in self._station_ids):
                    data.ok = True
            else:
                data.ok = False

            if not data.ok:
                raise UpdateFailed(f"Failed to fetch data: {err}")

        return data

    def get_metadata(self, station_id: str) -> StationMetadata | None:
        return self._metadata.get(station_id)

    def get_descriptor(self, station_id: str) -> StationDescriptor | None:
        return self._descriptors.get(station_id)

    def recalc_age(self, data: CoordinatorData) -> CoordinatorData:
        for sid, measurement in data.stations.items():
            if measurement.measured_at:
                try:
                    dt = datetime.fromisoformat(measurement.measured_at)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=TZ_BERLIN)
                    measurement.age_minutes = age_minutes(dt)
                except ValueError, TypeError:
                    pass
        return data

    async def async_refresh_descriptors(self) -> dict[str, StationDescriptor]:
        self._descriptors = await self._api.fetch_station_descriptors()
        return self._descriptors

    def set_descriptors(self, descriptors: dict[str, StationDescriptor]) -> None:
        self._descriptors = descriptors

    def set_station_ids(self, station_ids: set[str]) -> None:
        self._station_ids = station_ids

    def set_scan_interval(self, interval: int) -> None:
        self.update_interval = timedelta(seconds=interval)

    @property
    def stale_threshold(self) -> int:
        return self._stale_threshold

    def is_stale(self, age: int | None) -> bool:
        if age is None:
            return True
        return age > self._stale_threshold
