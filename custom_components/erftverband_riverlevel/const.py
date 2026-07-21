from __future__ import annotations

from enum import StrEnum

DOMAIN = "erftverband_riverlevel"
NAME = "Erftverband River Levels"
VERSION = "0.1.0"
MANUFACTURER = "Erftverband"

CONF_STATIONS = "stations"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_STALE_THRESHOLD = "stale_threshold"

DEFAULT_UPDATE_INTERVAL = 300
MIN_UPDATE_INTERVAL = 60
MAX_UPDATE_INTERVAL = 3600
DEFAULT_STALE_THRESHOLD = 180
MIN_STALE_THRESHOLD = 15
MAX_STALE_THRESHOLD = 1440

DETAIL_TTL_HOURS = 24

OVERVIEW_URL = "https://www.erftverband.de/mapserver/arcshp/flussgebiet/klima_abfluss/howis/html/ev_w_tab_aktwerte.html"
DETAIL_URL_TEMPLATE = "https://www.erftverband.de/mapserver/arcshp/flussgebiet/klima_abfluss/howis/html/pegel/Pegel_{station_id}_zr.html"

USER_AGENT = "HomeAssistant-ErftverbandRiverLevel/1.0"
REQUEST_TIMEOUT = 20

STORAGE_KEY = f"{DOMAIN}.coordinator_data"
STORAGE_VERSION = 1

ATTR_STATION_ID = "station_id"
ATTR_STATION_NAME = "station_name"
ATTR_WATERBODY = "waterbody"
ATTR_MEASURED_AT = "measured_at"
ATTR_AGE_MINUTES = "age_minutes"
ATTR_WATER_LEVEL_CM = "water_level_cm"
ATTR_DISCHARGE_M3S = "discharge_m3s"
ATTR_WL_TREND = "wl_trend"
ATTR_Q_TREND = "q_trend"
ATTR_SOURCE_REACHABLE = "source_reachable"
ATTR_CACHE_USED = "cache_used"
ATTR_THRESHOLDS = "thresholds"

SENSOR_TYPES = {
    "water_level": {"name": "Water Level", "unit": "cm", "icon": "mdi:waves"},
    "discharge": {"name": "Discharge", "unit": "m\u00b3/s", "icon": "mdi:pipe"},
    "wl_trend": {"name": "Water Level Trend", "unit": "cm/h", "icon": "mdi:trending-up"},
    "q_trend": {"name": "Discharge Trend", "unit": "m\u00b3/s/h", "icon": "mdi:trending-up"},
    "measured_at": {"name": "Last Measurement", "unit": None, "icon": "mdi:clock-outline"},
    "data_age": {"name": "Data Age", "unit": "min", "icon": "mdi:clock-alert"},
    "flood_status": {"name": "Flood Status", "unit": None, "icon": "mdi:flood"},
}

BINARY_SENSOR_TYPES = {
    "source_reachable": {"name": "Source Reachable"},
    "data_stale": {"name": "Data Stale"},
    "flood_alert": {"name": "Flood Alert"},
}


class FloodStatus(StrEnum):
    NORMAL = "normal"
    EV_ACTION = "ev_action"
    HQ10 = "hq10"
    HQ100 = "hq100"
    EXTREME = "extreme"
    UNKNOWN = "unknown"
