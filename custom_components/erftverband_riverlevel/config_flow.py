from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from aiohttp import ClientSession
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import fetch_overview, parse_overview_stations
from .const import (
    CONF_STALE_THRESHOLD,
    CONF_STATIONS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_STALE_THRESHOLD,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_STALE_THRESHOLD,
    MAX_UPDATE_INTERVAL,
    MIN_STALE_THRESHOLD,
    MIN_UPDATE_INTERVAL,
    NAME,
)
from .models import StationDescriptor

_LOGGER = logging.getLogger(__name__)


async def _fetch_station_list(hass: HomeAssistant) -> list[StationDescriptor]:
    session: ClientSession = async_get_clientsession(hass)
    html = await fetch_overview(session)
    stations = parse_overview_stations(html)
    return stations


class ErftverbandConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            selected = user_input.get(CONF_STATIONS, [])
            if not selected:
                errors[CONF_STATIONS] = "at_least_one"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=NAME,
                    data={
                        CONF_STATIONS: selected,
                    },
                    options={
                        CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
                        CONF_STALE_THRESHOLD: DEFAULT_STALE_THRESHOLD,
                    },
                )

        try:
            stations = await _fetch_station_list(self.hass)
        except Exception as err:
            _LOGGER.error("Failed to fetch station list: %s", err)
            return self.async_abort(
                reason="cannot_connect",
                description_placeholders={"error": str(err)},
            )

        if not stations:
            return self.async_abort(reason="no_stations_found")

        station_options = [
            selector.SelectOptionDict(
                value=s.station_id,
                label=f"{s.name} ({s.waterbody})",
            )
            for s in stations
        ]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATIONS): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=station_options,
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        ),
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ErftverbandOptionsFlow()


class ErftverbandOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        self._current_stations = list(self.config_entry.data.get(CONF_STATIONS, []))
        return await self.async_step_stations()

    async def async_step_stations(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            selected = user_input.get(CONF_STATIONS, [])
            if not selected:
                errors[CONF_STATIONS] = "at_least_one"
            else:
                self._current_stations = selected
                return await self.async_step_settings()

        try:
            stations = await _fetch_station_list(self.hass)
        except Exception as err:
            return self.async_abort(
                reason="cannot_connect",
                description_placeholders={"error": str(err)},
            )

        station_options = [
            selector.SelectOptionDict(
                value=s.station_id,
                label=f"{s.name} ({s.waterbody})",
            )
            for s in stations
        ]

        return self.async_show_form(
            step_id="stations",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_STATIONS,
                        default=self._current_stations,
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=station_options,
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        ),
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            stale_threshold = user_input.get(CONF_STALE_THRESHOLD, DEFAULT_STALE_THRESHOLD)
            return self.async_create_entry(
                title="",
                data={
                    CONF_STATIONS: self._current_stations,
                    CONF_UPDATE_INTERVAL: update_interval,
                    CONF_STALE_THRESHOLD: stale_threshold,
                },
            )

        options = self.config_entry.options
        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                    vol.Required(
                        CONF_STALE_THRESHOLD,
                        default=options.get(CONF_STALE_THRESHOLD, DEFAULT_STALE_THRESHOLD),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_STALE_THRESHOLD, max=MAX_STALE_THRESHOLD),
                    ),
                }
            ),
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_stations()
