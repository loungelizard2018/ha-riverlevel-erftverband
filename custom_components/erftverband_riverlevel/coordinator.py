from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import (
    extract_all_stations_from_overview,
    fetch_detail_page,
    fetch_overview,
    parse_detail_html,
)
from .const import (
    DEFAULT_STALE_THRESHOLD,
    DEFAULT_UPDATE_INTERVAL,
    DETAIL_TTL_HOURS,
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .models import CoordinatorData, StationData

_LOGGER = logging.getLogger(__name__)


class ErftverbandCoordinator(DataUpdateCoordinator[dict[str, StationData]]):
    def __init__(
        self,
        hass: HomeAssistant,
        session: ClientSession,
        station_ids: list[str],
        update_interval: int = DEFAULT_UPDATE_INTERVAL,
        stale_threshold: int = DEFAULT_STALE_THRESHOLD,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )
        self._session = session
        self._station_ids = station_ids
        self._stale_threshold = stale_threshold
        self._store = Store[dict[str, Any]](hass, STORAGE_VERSION, STORAGE_KEY)
        self._saved_data: CoordinatorData | None = None
        self.source_reachable = True
        self.cache_used = False

    @property
    def stale_threshold(self) -> int:
        return self._stale_threshold

    def set_stale_threshold(self, value: int) -> None:
        self._stale_threshold = value

    def set_update_interval(self, seconds: int) -> None:
        self.update_interval = timedelta(seconds=seconds)

    def set_station_ids(self, station_ids: list[str]) -> None:
        self._station_ids = station_ids

    async def async_load_saved_data(self) -> CoordinatorData | None:
        if self._saved_data is not None:
            return self._saved_data
        stored = await self._store.async_load()
        if stored:
            try:
                self._saved_data = CoordinatorData.from_dict(stored)
                return self._saved_data
            except (KeyError, ValueError, TypeError) as err:
                _LOGGER.warning("Could not load saved data: %s", err)
        return None

    async def _async_update_data(self) -> dict[str, StationData]:
        return await self._fetch_data()

    async def fetch_station_details(
        self, station_ids: list[str] | None = None
    ) -> dict[str, StationData]:
        targets = station_ids or self._station_ids
        result: dict[str, StationData] = {}
        for sid in targets:
            try:
                html = await fetch_detail_page(self._session, sid)
                detail = parse_detail_html(html, sid)
                result[sid] = detail
            except Exception as err:
                _LOGGER.warning("Failed to fetch detail for %s: %s", sid, err)
        return result

    async def _fetch_data(self) -> dict[str, StationData]:
        now = dt_util.now()
        stations: dict[str, StationData] = {}
        overview_ok = False
        overview_html: str | None = None

        try:
            overview_html = await fetch_overview(self._session)
            parsed_stations, descriptors = extract_all_stations_from_overview(overview_html)
            for sid in self._station_ids:
                if sid in parsed_stations:
                    stations[sid] = parsed_stations[sid]
                    overview_ok = True
                else:
                    _LOGGER.warning("Station %s not found in overview data", sid)
        except Exception as err:
            _LOGGER.warning("Failed to fetch overview page: %s", err)

        saved = await self.async_load_saved_data()

        if overview_ok:
            self.source_reachable = True
            self.cache_used = False

            for sid in self._station_ids:
                existing = None
                if saved and sid in saved.stations:
                    existing = saved.stations[sid]

                if sid not in stations:
                    if existing:
                        stations[sid] = existing
                    continue

                station = stations[sid]

                if existing:
                    station.operator = existing.operator or station.operator
                    station.easting = existing.easting or station.easting
                    station.northing = existing.northing or station.northing
                    station.catchment_area = existing.catchment_area or station.catchment_area
                    station.data_range = existing.data_range or station.data_range
                    station.main_values = existing.main_values or station.main_values

                    ev_w_none = station.thresholds.ev_w is None
                    ev_q_none = station.thresholds.ev_q is None
                    if ev_w_none and ev_q_none:
                        if (
                            existing.thresholds.ev_w is not None
                            or existing.thresholds.ev_q is not None
                        ):
                            station.thresholds = existing.thresholds

                    need_detail = False
                    if existing.detail_fetched_at:
                        age = now - existing.detail_fetched_at
                        if age > timedelta(hours=DETAIL_TTL_HOURS):
                            need_detail = True
                        if existing.operator:
                            station.operator = existing.operator
                        if existing.thresholds.ev_w is not None:
                            need_detail = False
                    else:
                        need_detail = True

                    if need_detail and sid in self._station_ids:
                        try:
                            detail_html = await fetch_detail_page(self._session, sid)
                            detail = parse_detail_html(detail_html, sid)
                            station.thresholds = detail.thresholds
                            station.operator = detail.operator or station.operator
                            station.easting = detail.easting or station.easting
                            station.northing = detail.northing or station.northing
                            station.catchment_area = (
                                detail.catchment_area or station.catchment_area
                            )
                            station.data_range = detail.data_range or station.data_range
                            station.main_values = detail.main_values or station.main_values
                            station.detail_fetched_at = now
                        except Exception as err:
                            _LOGGER.warning("Failed to fetch detail for %s: %s", sid, err)
                            if existing:
                                station.thresholds = existing.thresholds
                                station.detail_fetched_at = existing.detail_fetched_at
                else:
                    if existing:
                        station.operator = existing.operator
                        station.easting = existing.easting
                        station.northing = existing.northing
                        station.catchment_area = existing.catchment_area
                        station.data_range = existing.data_range
                        station.main_values = existing.main_values
                        station.thresholds = existing.thresholds
                        station.detail_fetched_at = existing.detail_fetched_at

            coordinator_data = CoordinatorData(
                stations=stations,
                last_update=now,
                source_reachable=True,
                cache_used=False,
            )
            await self._store.async_save(coordinator_data.to_dict())
            self._saved_data = coordinator_data
            return stations

        self.source_reachable = False

        if saved:
            self.cache_used = True
            _LOGGER.info("Overview unavailable, using cached data")
            stations = {}
            for sid in self._station_ids:
                if sid in saved.stations:
                    sd = saved.stations[sid]
                    sd.measured_at = sd.measured_at
                    stations[sid] = sd
            if stations:
                return stations

        raise UpdateFailed("Could not fetch data from Erftverband and no cache available")

    async def async_refresh_station_details(self, station_id: str) -> StationData | None:
        try:
            html = await fetch_detail_page(self._session, station_id)
            detail = parse_detail_html(html, station_id)
            return detail
        except Exception as err:
            _LOGGER.error("Failed to refresh detail for %s: %s", station_id, err)
            return None
