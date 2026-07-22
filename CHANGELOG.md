# Changelog

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
