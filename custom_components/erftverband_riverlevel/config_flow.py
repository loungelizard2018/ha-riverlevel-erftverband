from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ErftverbandApi, extract_station_descriptors
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_STALE_THRESHOLD,
    CONF_STATION_IDS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STALE_THRESHOLD,
    DOMAIN,
    LOGGER,
    MAX_SCAN_INTERVAL,
    MAX_STALE_THRESHOLD,
    MIN_SCAN_INTERVAL,
    MIN_STALE_THRESHOLD,
)
from .models import StationDescriptor


async def validate_stations(
    hass: HomeAssistant,
    station_ids: list[str],
) -> dict[str, StationDescriptor]:
    session = async_get_clientsession(hass)
    api = ErftverbandApi(session)
    try:
        html = await api.fetch_overview()
    except Exception as err:
        raise CannotConnectError(f"Failed to connect: {err}") from err
    descriptors = extract_station_descriptors(html)
    result: dict[str, StationDescriptor] = {}
    for sid in station_ids:
        if sid in descriptors:
            result[sid] = descriptors[sid]
        else:
            raise InvalidStationError(f"Station {sid} not found")
    return result


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            station_ids: list[str] = user_input.get(CONF_STATION_IDS, [])
            if not station_ids:
                errors["base"] = "no_stations"
            else:
                try:
                    await validate_stations(self.hass, station_ids)
                except CannotConnectError:
                    errors["base"] = "cannot_connect"
                except InvalidStationError:
                    errors["base"] = "invalid_station"
                except Exception:
                    LOGGER.exception("Unexpected error")
                    errors["base"] = "unknown"

                if not errors:
                    return self.async_create_entry(
                        title="Erftverband HOWIS",
                        data={
                            CONF_STATION_IDS: list(station_ids),
                            CONF_SCAN_INTERVAL: user_input.get(
                                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                            ),
                            CONF_STALE_THRESHOLD: user_input.get(
                                CONF_STALE_THRESHOLD, DEFAULT_STALE_THRESHOLD
                            ),
                        },
                    )

        session = async_get_clientsession(self.hass)
        api = ErftverbandApi(session)
        try:
            html = await api.fetch_overview()
            descriptors = extract_station_descriptors(html)
        except Exception:
            descriptors = {}

        options: list[selector.SelectOptionDict] = [
            selector.SelectOptionDict(
                value=sid,
                label=f"{desc.station_name} ({desc.waterbody})",
            )
            for sid, desc in sorted(
                descriptors.items(),
                key=lambda x: (x[1].station_name.lower(), x[1].waterbody.lower()),
            )
        ]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATION_IDS): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                    vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                    vol.Required(CONF_STALE_THRESHOLD, default=DEFAULT_STALE_THRESHOLD): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_STALE_THRESHOLD, max=MAX_STALE_THRESHOLD),
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    CONF_STALE_THRESHOLD: user_input.get(
                        CONF_STALE_THRESHOLD, DEFAULT_STALE_THRESHOLD
                    ),
                },
            )

        current_scan = self._config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        current_stale = self._config_entry.options.get(
            CONF_STALE_THRESHOLD,
            self._config_entry.data.get(CONF_STALE_THRESHOLD, DEFAULT_STALE_THRESHOLD),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current_scan): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                    vol.Required(CONF_STALE_THRESHOLD, default=current_stale): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_STALE_THRESHOLD, max=MAX_STALE_THRESHOLD),
                    ),
                }
            ),
        )


class CannotConnectError(HomeAssistantError):
    pass


class InvalidStationError(HomeAssistantError):
    pass
