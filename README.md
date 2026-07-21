# Erftverband River Levels

[![Validate](https://github.com/loungelizard2018/ha-riverlevel-erftverband/actions/workflows/validate.yml/badge.svg)](https://github.com/loungelizard2018/ha-riverlevel-erftverband/actions/workflows/validate.yml)
[![Hassfest](https://github.com/loungelizard2018/ha-riverlevel-erftverband/actions/workflows/hassfest.yml/badge.svg)](https://github.com/loungelizard2018/ha-riverlevel-erftverband/actions/workflows/hassfest.yml)
[![Tests](https://github.com/loungelizard2018/ha-riverlevel-erftverband/actions/workflows/tests.yml/badge.svg)](https://github.com/loungelizard2018/ha-riverlevel-erftverband/actions/workflows/tests.yml)

Home Assistant integration for real-time water levels and discharge of Erftverband gauging stations in North Rhine-Westphalia, Germany.

Data source: [Erftverband HOWIS](https://www.erftverband.de/mapserver/arcshp/flussgebiet/klima_abfluss/howis/html/ev_w_tab_aktwerte.html)

## Installation

### HACS (recommended)

1. Add this repository as a custom repository in HACS:
   - URL: `https://github.com/loungelizard2018/ha-riverlevel-erftverband`
   - Category: Integration
2. Click "Install"
3. Restart Home Assistant

### Manual

1. Copy `custom_components/erftverband_riverlevel/` into your Home Assistant `custom_components/` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "Erftverband River Levels"
3. Select one or more gauging stations from the list
4. Configure update interval (default: 300s) and stale threshold (default: 180 min)

### Changing the selection

- **Reconfigure:** Add or remove stations without deleting the config entry
- **Options:** Change update interval and stale threshold

## Entities

Each selected station creates:

### Sensors
| Entity | Unit | Description |
|---|---|---|
| Water Level | cm | Current water level |
| Discharge | m³/s | Current discharge |
| Water Level Trend | cm/h | Trend of water level change |
| Discharge Trend | m³/s/h | Trend of discharge change |
| Last Measurement | (timestamp) | Time of last measurement |
| Data Age | min | Age of the measurement data |
| Flood Status | (enum) | `normal`, `ev_action`, `hq10`, `hq100`, `extreme`, `unknown` |

### Binary Sensors
| Entity | Description |
|---|---|
| Source Reachable | Whether the HOWIS server is reachable |
| Data Stale | Whether data exceeds the stale threshold |
| Flood Alert | On when flood status ≥ ev_action |

## Cache and Stale Behavior

- On live fetch failure, the last good data is served from cache
- Original measurement timestamps are preserved
- Data age is recalculated against current time
- `source_reachable` is set to `false`
- No values or timestamps are fabricated

## Diagnostics

Go to **Settings → Devices & Services → ... → System Health → Diagnostics** to generate a diagnostics dump for debugging.

## Debug Logging

```yaml
logger:
  default: warning
  logs:
    custom_components.erftverband_riverlevel: debug
```

## Data Source

This integration uses the public [Erftverband HOWIS](https://www.erftverband.de/mapserver/arcshp/flussgebiet/klima_abfluss/howis/html/ev_w_tab_aktwerte.html) web pages. All data is provided by the [Erftverband](https://www.erftverband.de).

## Disclaimer

- This integration is **not** an official product of the Erftverband
- There is **no partnership** with the Erftverband
- This is **not a replacement** for official flood warning systems
- Always consult official sources for flood warnings and emergency information
