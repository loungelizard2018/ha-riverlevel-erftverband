# Architektur der Integration `erftverband_riverlevel`

## Überblick

```
custom_components/erftverband_riverlevel/
├── __init__.py       # Einstiegspunkt, Plattform-Setup
├── api.py            # HTML-Parsing, HTTP-Fetch, Zahlenparsing
├── binary_sensor.py  # Binäre Sensoren
├── config_flow.py    # Setup-, Reconfigure- und Options-Flows
├── const.py          # Konstanten, Enum, URLs
├── coordinator.py    # DataUpdateCoordinator mit Caching
├── diagnostics.py    # Diagnoseunterstützung
├── entity.py         # Basis-Entity
├── manifest.json     # HA-Manifest
├── models.py         # Dataclasses
├── sensor.py         # Sensorentitäten
├── quality_scale.yaml
└── translations/
    ├── de.json
    └── en.json
```

## Datenfluss

```
Erftverband HOWIS                  Home Assistant
─────────────────                 ────────────────
                                    Config Flow (Benutzer wählt Pegel)
                                          │
                                          ▼
Übersichtsseite ◄─────────────  Coordinator (DataUpdateCoordinator)
  HTML-Parsing │                          │
  ┌────────────┤                          │
  │ Stationen  │    alle 300s             │
  │ erkennen   │◄─────────────────────────┘
  │ Werte      │                          │
  │ extrahieren│                    ┌──────┴──────┐
  └────────────┘                    │             │
  Detailseite (24h TTL)       Sensoren     Binary Sensors
  ┌─────────────────          ┌──────────┐  ┌───────────────┐
  │ Metadaten       │         │Wasserstand│ │Quelle erreichbar│
  │ Schwellenwerte  │         │Abfluss    │ │Daten veraltet   │
  │ Hauptwerte      │         │Trends     │ │Hochwasseralarm  │
  └─────────────────┘         │Messzeit   │ └───────────────┘
                              │Datenalter │
                              │Status     │
                              └──────────┘
```

## Entscheidungen

### 1. Ein Request pro Poll
Die Übersichtsseite enthält alle aktuellen Messwerte aller Pegel in einer Tabelle.
Pro Aktualisierungszyklus wird **genau ein HTTP-Request** zur Übersichtsseite
durchgeführt. Detailseiten werden nur bei Bedarf geladen (Ersteinrichtung, neue
Pegel, 24h-TTL).

### 2. Href-basierte Stations-ID
Die ID wird aus dem `<a href="...">`-Attribut extrahiert, nicht aus dem
Stationsnamen. Dies verhindert Brüche bei kosmetischen Namensänderungen.

### 3. Robuster Zahlenparser
`parse_german_number()` verwendet die Regel "letztes Trennzeichen ist der
Dezimaltrenner", um beide Formate (Komma und Punkt) korrekt zu parsen.

### 4. Fallback auf Cache
Bei Ausfall der Live-Quelle wird der letzte gültige Zustand aus
`Store` (JSON) geladen. Datenalter wird neu berechnet, Messzeitpunkte
bleiben original.

### 5. Status-Priorität
Die FloodStatus-Berechnung prüft von extrem nach normal:

```
HQextrem → HQ100 → HQ10 → EV-Einsatzplan → Normal
```

Wasserstand und Abfluss werden separat geprüft, der höchste erreichte
Status gewinnt. Fehlende Schwellen werden übersprungen (nie als 0
interpretiert).

### 6. Device-Modell
Ein HA-Device pro Pegel, Identifier `(DOMAIN, station_id)`. Alle
Sensoren eines Pegels werden diesem Device zugeordnet.

## Abhängigkeiten

- **Keine** externen Python-Bibliotheken außer aiohttp (HA-intern)
- HTML-Parsing über `html.parser.HTMLParser` (Standardbibliothek)
- `zoneinfo` für Zeitzonen (Python 3.9+)
