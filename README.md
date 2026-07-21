# Erftverband River Levels

[![HACS Validation](https://github.com/loungelizard2018/ha-riverlevel-erftverband/actions/workflows/validate.yml/badge.svg)](https://github.com/loungelizard2018/ha-riverlevel-erftverband/actions/workflows/validate.yml)
[![Hassfest](https://github.com/loungelizard2018/ha-riverlevel-erftverband/actions/workflows/hassfest.yml/badge.svg)](https://github.com/loungelizard2018/ha-riverlevel-erftverband/actions/workflows/hassfest.yml)
[![Tests](https://github.com/loungelizard2018/ha-riverlevel-erftverband/actions/workflows/tests.yml/badge.svg)](https://github.com/loungelizard2018/ha-riverlevel-erftverband/actions/workflows/tests.yml)

Home Assistant-Integration für die Überwachung von Wasserstand und Abfluss der
Pegel des Erftverbands (HOWIS).

## Installation

### HACS (Custom Repository)

1. Installiere [HACS](https://hacs.xyz/)
2. Füge dieses Repository als Custom Repository hinzu:
   - URL: `https://github.com/loungelizard2018/ha-riverlevel-erftverband`
   - Kategorie: Integration
3. Klicke auf "Installieren"

### Manuell

Kopiere `custom_components/erftverband_riverlevel/` in dein
Home Assistant `config/custom_components/` Verzeichnis.

## Einrichtung

1. Gehe zu **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Suche nach **Erftverband River Levels**
3. Wähle einen oder mehrere Pegel aus
4. Bestätige

## Pegelauswahl

Du kannst beliebig viele Pegel gleichzeitig auswählen. Jeder ausgewählte Pegel
erzeugt ein eigenes Gerät mit folgenden Sensoren:

- Wasserstand (cm)
- Abfluss (m³/s)
- Wasserstand-Tendenz (cm/h)
- Abfluss-Tendenz (m³/s/h)
- Letzte Messung (Timestamp)
- Datenalter (Minuten)
- Hochwasserstatus (Normal / EV-Einsatzplan / HQ10 / HQ100 / HQextrem)
- Quelle erreichbar (binär)
- Daten veraltet (binär)
- Hochwasseralarm (binär, aktiv ab EV-Einsatzplan)

## Auswahl ändern

Nach der Einrichtung kannst du die Pegelauswahl über **Konfigurieren** ändern.

## Entitäten

Jeder Pegel erzeugt ein Gerät (Device) mit Identifier `(DOMAIN, station_id)`.
Die Entitäten nutzen `has_entity_name = true` und haben übersetzte Namen.

## Cache- und Stale-Verhalten

- Bei Ausfall der Live-Quelle wird der letzte gültige Messwert aus dem Cache
  verwendet.
- Das Datenalter wird automatisch neu berechnet.
- Original-Messzeitpunkte bleiben erhalten.
- Sensoren melden sich als "veraltet", wenn die Daten älter als die
  konfigurierte Schwelle sind.

## Diagnostics

Wenn du Unterstützung benötigst, erstelle bitte einen Diagnostics-Export
über das Gerätemenü in Home Assistant und füge ihn deinem Issue bei.

## Debug Logging

```yaml
logger:
  logs:
    custom_components.erftverband_riverlevel: debug
```

## Datenquelle

Diese Integration nutzt die öffentlich zugänglichen Messdaten des
Erftverbands HOWIS-Systems:

- [Übersichtsseite](https://www.erftverband.de/mapserver/arcshp/flussgebiet/klima_abfluss/howis/html/ev_w_tab_aktwerte.html)

## Haftungsausschluss

- Diese Integration steht in **keiner offiziellen Partnerschaft** mit dem
  Erftverband.
- Die bereitgestellten Daten dienen **ausschließlich zu Informationszwecken**.
- Diese Integration ist **kein Ersatz für ein offizielles
  Hochwasserwarnsystem**.
- Im Hochwasserfall informiere dich bitte über offizielle Kanäle.
