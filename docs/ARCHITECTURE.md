# Architecture

## Overview

```
custom_components/erftverband_riverlevel/
├── __init__.py        # HA integration entry point
├── api.py             # HTTP client and HTML parsers
├── binary_sensor.py   # Binary sensor platform
├── config_flow.py     # Config flow, reconfigure, options
├── const.py           # Constants and configuration
├── coordinator.py     # DataUpdateCoordinator
├── diagnostics.py     # Diagnostics support
├── entity.py          # Base entity class
├── manifest.json      # HA manifest
├── models.py          # Typed dataclasses
├── sensor.py          # Sensor platform
├── quality_scale.yaml # Quality scale config
└── translations/
    ├── de.json        # German translations
    └── en.json        # English translations
```

## Data Flow

```
User Setup (Config Flow)
  │
  ├─ 1. Fetch overview page
  ├─ 2. Extract station descriptors (ID, name, waterbody, URL)
  ├─ 3. User selects stations
  └─ 4. Config entry created

Polling (every N seconds)
  │
  ├─ 1. Coordinator._async_update_data()
  ├─ 2. Fetch overview page (ONE HTTP request)
  ├─ 3. Parse all selected stations' measurements
  ├─ 4. Update coordinator.data
  ├─ 5. Entities read from coordinator.data
  │
  ├─ First time / TTL expired:
  │  ├─ Fetch detail pages for metadata
  │  └─ Store thresholds, catchment area
  │
  └─ On live fetch failure:
     ├─ Load cached last-good data
     ├─ Recalculate data age
     └─ Set source_reachable = false

Entities read coordinator.data for each station.
```

## Key Design Decisions

### 1. One HTTP request per poll
The overview page contains ALL current measurements. Detail pages are only fetched for metadata (thresholds), which changes very rarely (TTL: 24h).

### 2. Station ID from href
Station names can change or contain special characters. The URL-safe identifier from the detail page link (`Pegel_{ID}_zr.html`) is the stable technical identifier.

### 3. Threshold handling
- Missing thresholds = `None` (never 0)
- Status calculation: compare water level AND discharge separately
- Highest matching status wins
- Stale data → status = `unknown`, not `normal`

### 4. Cache fallback
- Last good data stored via `homeassistant.helpers.storage.Store`
- On live fetch failure: serve cached data, recalculate age
- Never invent values or timestamps

### 5. Device per station
- One HA device per station
- Device identifier: `(DOMAIN, station_id)`
- Configuration URL → detail page

### 6. Entity naming
- `has_entity_name = true`
- Translated names via `translation_key`
- Unique IDs based on station_id + sensor type

## Component Responsibilities

| Component | Responsibility |
|---|---|
| `api.py` | HTTP fetching, HTML parsing, number/datetime parsing |
| `models.py` | Dataclasses for all data types |
| `const.py` | All constants, config keys, state enums |
| `coordinator.py` | Polling orchestration, cache, metadata management |
| `entity.py` | Base entity with device info |
| `sensor.py` | 7 sensor types per station |
| `binary_sensor.py` | 3 binary sensor types |
| `config_flow.py` | User/reconfigure/options flow |
| `diagnostics.py` | Config entry + device diagnostics |
| `__init__.py` | Setup/unload/migration |

## States and Thresholds

```
State priority: normal < ev_action < hq10 < hq100 < extreme

For each station:
  status = normal
  if water_level >= hqextrem_cm or discharge >= hqextrem_m3s: extreme
  if water_level >= hq100_cm or discharge >= hq100_m3s: hq100
  if water_level >= hq10_cm or discharge >= hq10_m3s: hq10
  if water_level >= ev_alarm_cm or discharge >= ev_alarm_m3s: ev_action
  if data is stale: unknown
```

Flood Alert binary sensor activates at `ev_action` level or higher.
