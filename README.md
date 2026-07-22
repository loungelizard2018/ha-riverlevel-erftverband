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

### Update via HACS

1. HACS shows an update is available
2. Click "Update"
3. Restart Home Assistant

### Manual

1. Copy `custom_components/erftverband_riverlevel/` into your Home Assistant `custom_components/` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "Erftverband River Levels"
3. Select one or more gauging stations from the list, or enable "Load all available stations"
4. Configure update interval (default: 900s / 15 min) and stale threshold (default: 180 min)

### Difference between integration selection and card filter

- **Integration selection:** Controls which stations are loaded as entities in Home Assistant
- **Card filter:** Limits which of the loaded stations are displayed in a specific card instance
- You can create multiple cards with different station filters

### Dynamic HOWIS catalog

When "Load all available stations" is enabled, the integration automatically discovers all stations from the HOWIS overview page. New stations added by the Erftverband appear without reconfiguration.

### Changing the selection

- **Reconfigure:** Add or remove stations without deleting the config entry
- **Options:** Change update interval, stale threshold, and load-all-stations setting

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
|---|---|---|
| Source Reachable | Whether the HOWIS server is reachable |
| Data Stale | Whether data exceeds the stale threshold |
| Flood Alert | On when flood status ≥ ev_action |

## Cache and Stale Behavior

- On live fetch failure, the last good data is served from cache
- Original measurement timestamps are preserved
- Data age is recalculated against current time
- `source_reachable` is set to `false`
- No values or timestamps are fabricated
- Data freshness indicator:
  - Green: less than 60 minutes old
  - Yellow: 60 minutes to 12 hours old
  - Red: older than 12 hours or no data

## Update Interval

- The integration updates at most every 15 minutes (default: 900 seconds)
- History data is cached for 15 minutes in the card

## Diagnostics

Go to **Settings → Devices & Services → ... → System Health → Diagnostics** to generate a diagnostics dump for debugging.

## Lovelace Card

This integration ships a responsive Lovelace card (`custom:erftverband-riverlevel-card`) with an embedded background image and HACS brand icon.

### Card Installation

1. Install/update the integration via HACS
2. Restart Home Assistant
3. Add the resource once:
   - **Settings → Dashboards → Resources → Add Resource**
   - URL: `/api/erftverband_riverlevel/static/erftverband-riverlevel-card.js?v=0.2.0`
   - Type: **JavaScript Module**
4. Fully reload the browser

### Add the Card

```yaml
type: custom:erftverband-riverlevel-card
```

With station filter and all options:

```yaml
type: custom:erftverband-riverlevel-card
stations:
  - essig
  - morenhoven
hours_to_show: 24
show_history: true
show_discharge: true
show_source_status: true
sort_by: waterbody
```

### Configuration Options

| Option | Default | Description |
|---|---|---|
| `stations` | (all) | Filter to specific station IDs (omit for all) |
| `hours_to_show` | `24` | History chart time range (1–168 hours) |
| `show_history` | `true` | Show SVG history chart per station |
| `show_discharge` | `true` | Show discharge values and chart line |
| `show_source_status` | `true` | Show HOWIS reachability indicator |
| `sort_by` | `name` | Station sort order (`name`, `water_level`, `flood_status`, `waterbody`, `data_age`) |

### Features

- **No dependencies:** Auto-Entities, Button-Card, ApexCharts, Decluttering-Card not required
- **Automatic station detection:** All configured stations appear automatically
- **Responsive:** CSS Grid adapts from multi-column (desktop) to single-column (mobile) – works in sections, tablets, and smartphones
- **Sections support:** Uses full section width with `getGridOptions()`
- **State indicators:** Water level, discharge, trend, data age, flood status badge
- **Stale & alarm warnings:** Yellow "Daten veraltet" or red "HOCHWASSERALARM" badges
- **Source status:** Green/red dot for HOWIS reachability
- **History chart:** Native SVG chart – no ApexCharts needed
- **More-info:** Click values to open the Home Assistant detail dialog
- **Source link:** Opens HOWIS detail page in new tab
- **Visual editor:** Optional via the card picker UI
- **Background image:** Embedded water/landscape background
- **HACS/Home Assistant brand icon:** Included in the integration
- **Title format:** Waterbody – Station name

### Behaviour

- Adding or removing stations in the integration config immediately reflects in the card after reload
- Unavailable/unknown values display `—` without breaking the layout
- Stale data shows appropriate badges
- History chart loads on first render, cached for 15 minutes
- History errors don't affect current value display

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
