# Analysis: Erftverband HOWIS Live Data Source

## Overview Page

**URL:** `https://www.erftverband.de/mapserver/arcshp/flussgebiet/klima_abfluss/howis/html/ev_w_tab_aktwerte.html`

**Structure:** Single HTML `<table>` containing all stations grouped by river section.

**Columns (12 data columns + 1 station name column):**
1. Pegel (Gewässer) – station name with waterbody in parentheses, contains `<a href>` to detail page
2. letzter Messwert – datetime (DD.MM.YY HH:MM)
3. Wasserstand [cm] – Wert
4. Wasserstand Tendenz – cm/h
5. Abfluss [m³/s] – Wert
6. Abfluss Tendenz – m³/s/h
7. MQ – Mittelwasserabfluss
8. HQ1
9. HQ2
10. HQ10
11. HQ100
12. HQExtrem

**Station ID extraction:**
- Each station row has an `<a href="./pegel/Pegel_{STATION_ID}_zr.html">`
- The station_id is the URL-safe identifier (e.g. `Essig`, `Kirchheim`, `Moeschemer_M`)
- This is used as the stable technical identifier

**All 28 identified stations:**

| Station ID | Station Name | Waterbody | Details |
|---|---|---|---|
| Schoenau | Schönau | Erft | full data |
| Eicherscheid | Eicherscheid | Erft | full data |
| Moeschemer_M | Möschemer Mühle | Eschweilerbach | umlaut in URL |
| Arloff | Arloff | Erft | full data |
| Hausweiler | Hausweiler | Erft | full data |
| Horchheim | Horchheim | Erft | full data |
| Vussem | Vussem | Veybach | missing all HQ thresholds |
| Burg_Veynau | Burg Veynau | Veybach | full data |
| Kirchheim | Kirchheim | Steinbach | full data |
| Essig | Essig | Orbach | full data |
| Morenhoven | Morenhoven | Swist | full data |
| Weilerswist | Weilerswist | Swist | full data |
| Schwerfen | Schwerfen | Rotbach | full data |
| Wichterich | Wichterich | Bleibach | missing all HQ thresholds |
| Muelheim | Mülheim | Rotbach | umlaut in URL |
| Niederberg | Niederberg | Rotbach | only water level, no discharge |
| Friesheim | Friesheim | Rotbach | full data |
| Bliesheim | Bliesheim | Erft | full data |
| Horrem | Horrem | Kleine Erft | missing HQ10/HQ100/HQExtrem |
| Gymnich | Gymnich | Erft | full data |
| Moedrath | Mödrath | Erft | umlaut in URL |
| Fuessenich_OW | Füssenich OW | Neffelbach | umlaut, special notes, missing HQ |
| Fuessenich | Füssenich | Neffelbach | umlaut, missing HQ100/HQExtrem |
| Bessenich | Bessenich | Neffelbach | full data |
| Langenich | Langenich | Neffelbach | full data |
| Zieverich | Zieverich | Erft | water level only (no discharge) |
| Glesch | Glesch | Erft | full data |
| Bedburg | Bedburg | Erft | full data |
| Neubrueck | Neubrück | Erft | umlaut in URL |
| Gill | Gill | Gillbach | full data |
| Anstel | Anstel | Gillbach | full data |
| Glehn | Glehn | Jüchener Bach | missing HQ10/HQ100/HQExtrem |

## Detail Pages

**URL Pattern:** `https://www.erftverband.de/mapserver/arcshp/flussgebiet/klima_abfluss/howis/html/pegel/Pegel_{STATION_ID}_zr.html`

**Structure per page:**
1. Stammdaten table: Pegel name, Betreiber, Gewässer, Rechtswert, Hochwert, Einzugsgebiet (km²)
2. Hauptwerte table: MNW/MNQ, MW/MQ, MHW/MHQ, HQ1, HQ2 with W[cm] and Q[m³/s]
3. Hochwasser-Kategorien table: EV-Einsatzplan, HQ10, HQ100, HQExtrem thresholds
4. Aktuelle Werte table: datetime, water level, discharge, trends, Stauwert

**Reliable metadata from detail pages:**
- Station name and waterbody (also in overview, redundant)
- Catchment area (km²) – not always available
- Threshold values: MW_cm, MHW_cm, EV-Einsatzplan (W+Q), HQ10 (W+Q), HQ100 (W+Q), HQExtrem (W+Q)
- Missing thresholds are shown as "-" or "k.A."

**Edge cases confirmed:**
- Zieverich: water level only, discharge = "-", all thresholds = "-" or "k.A."
- Vussem: water level + discharge available, but no HQ thresholds at all
- Niederberg: water level only, no discharge, no thresholds
- Fuessenich_OW: water level + discharge (0.00), only EV-Einsatzplan threshold, discharge trend = "-"
- Moeschemer_M: URL-safe name with underscores, Betreiber field contains HTML link
- Mödrath/Mülheim/Füssenich/Neubrück: URL-safe names (umlauts replaced in URL)

## Key Findings

1. **Stable station ID** is extracted from `<a href="./pegel/Pegel_{ID}_zr.html">` – never from station name alone
2. **One request** to the overview page retrieves all current measurements for all stations
3. **Detail pages** are only needed for metadata (thresholds, catchment area)
4. **Missing thresholds** are common – must be handled as `None`, never as `0`
5. **Water level only** stations (Zieverich, Niederberg) have no discharge data
6. **German number format** with comma as decimal separator, points for thousands
7. **Datetime format**: `DD.MM.YY HH:MM` or `DD.MM.YYYY HH:MM`, Europe/Berlin timezone
8. **Trend values** can have leading spaces or `+` signs
9. **Negative trends** with spaces: `- 14` should be parsed as -14
10. **HTML entities** are used for special characters (ä=ä, ü=ü, etc.)
