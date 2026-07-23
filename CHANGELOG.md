# Changelog

## v0.2.1

- Fix loading cached flood thresholds from Home Assistant storage
- Fix flood status sensors failing when the state is `unknown`
- Restore flood status and flood alarm entities after upgrading to v0.2.0

## v0.2.0

- Own responsive Lovelace card (`custom:erftverband-riverlevel-card`)
- Dynamic HOWIS station catalog (load all available stations)
- Station selection per card instance
- Water level, discharge, and trend display
- SVG history chart (no ApexCharts dependency)
- Data freshness indicator (green/yellow/red dot)
- Flood warning levels (ev_action, HQ10, HQ100, HQextreme)
- 15-minute update interval
- Valid null value handling (unavailable/unknown/stale)
- Corrected station assignments with proper waterbody metadata
- German and English options UI
- Embedded background image
- HACS/Home Assistant brand icon
- Static path registration for card assets
- Tests for API, metadata, setup, config flow, coordinator, frontend
