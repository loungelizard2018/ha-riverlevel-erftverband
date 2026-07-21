# Analyse der Erftverband-HOWIS-Datenquelle

## Übersicht

Der Erftverband betreibt das HOWIS-System (Hochwasserinformationssystem) unter:

```
https://www.erftverband.de/mapserver/arcshp/flussgebiet/klima_abfluss/howis/
```

Die Daten werden auf zwei Arten bereitgestellt:

1. **Übersichtsseite** (`ev_w_tab_aktwerte.html`): Sammeltabelle aller Pegel
2. **Detailseiten** (`pegel/Pegel_{Name}_zr.html`): Einzelseite pro Pegel

## Übersichtsseite

Enthält eine einzige HTML-Tabelle mit allen 32 Pegeln, gruppiert nach Gewässerabschnitten:

| Abschnitt | Anzahl Pegel |
|-----------|-------------|
| Obere Erft | 6 |
| Veybach | 2 |
| Swist | 4 |
| Rotbach | 5 |
| Mittlere Erft | 4 |
| Neffelbach | 4 |
| Untere Erft | 4 |
| Gillbach | 2 |
| Jüchener Bach | 1 |

### Tabellenspalten

| Spalte | Inhalt | Format |
|--------|--------|--------|
| 0 | Pegel (Gewässer) | Als `<a href>`-Link |
| 1 | Gesetzl. Zeit | `DD.MM.YY HH:MM` |
| 2 | Wasserstand [cm] | Ganzzahl, space-padded |
| 3 | Tendenz W [cm] | Vorzeichen + space-padded Zahl |
| 4 | Abfluss [m³/s] | Dezimal mit Punkt |
| 5 | Tendenz Q [m³/s/h] | Dezimal mit Punkt |
| 6 | MQ | Dezimal |
| 7 | HQ1 | Dezimal mit **Komma** |
| 8 | HQ2 | Dezimal mit **Komma** |
| 9 | HQ10 | Dezimal |
| 10 | HQ100 | Dezimal |
| 11 | HQExtrem | Dezimal |

### Stations-ID aus href

Jeder Pegel ist über ein `<a href>`-Tag verlinkt:

```html
<a href="./pegel/Pegel_Essig_zr.html">Essig (Orbach)</a>
```

Die ID wird aus dem href extrahiert: Alles zwischen `Pegel_` und `_zr.html`:

| href | Station ID |
|------|-----------|
| `./pegel/Pegel_Essig_zr.html` | `Essig` |
| `./pegel/Pegel_Moeschemer_M_zr.html` | `Moeschemer_M` |
| `./pegel/Pegel_Fuessenich_OW_zr.html` | `Fuessenich_OW` |
| `./pegel/Pegel_Neubrueck_zr.html` | `Neubrueck` |

Besonderheiten:
- Umlaute werden transliteriert: `ö` → `oe`, `ü` → `ue`, `ß` → `ss`
- Namenszusätze wie `_OW` (Oberwasser) bleiben in der ID
- `_M` (Möschemer Mühle) bleibt in der ID
- Die ID wird nie als `int` verwendet, immer als String.

### Zahlenformate

Die HOWIS-Seite mischt **beide** Dezimaltrennzeichen:

| Beispiel | Tatsächlicher Wert | Erkanntes Muster |
|----------|-------------------|------------------|
| `2,0` | 2.0 | Komma = Dezimal |
| `12.4` | 12.4 | Punkt = Dezimal |
| `0.00` | 0.0 | Punkt = Dezimal |
| `84,2` | 84.2 | Komma = Dezimal |
| `215` | 215 | Ganzzahl |

Regel: Das **zuletzt** auftretende Trennzeichen (`,` oder `.`) ist das
Dezimaltrennzeichen. Dies wird durch `parse_german_number()` umgesetzt.

### Fehlende Werte

- `-` (einfacher Bindestrich): Pegel ohne Abfluss (Niederberg, Zieverich)
- ` - ` (Leerzeichen-Bindestrich-Leerzeichen): Fehlende HQ-Werte (Vussem, Wichterich,
  Glehn)
- `k.A.` (Detailseite): "keine Angabe", z. B. Niederberg ohne Q-Werte

## Detailseiten

Eine Detailseite enthält:

### Stammdaten (immer vorhanden)

| Feld | Beispiel | Typ |
|------|----------|-----|
| Pegel | Essig | String |
| Betreiber | Erftverband | String |
| Gewässer | Orbach | String |
| Rechtswert | 2563036 | int |
| Hochwert | 5613930 | int |
| Einzugsgebiet | 41,1 | float (Komma!) |

### Hauptwerte

| Kennung | W [cm] | Q [m³/s] |
|---------|--------|-----------|
| MNW/MNQ | 0 | 0.001 |
| MW/MQ | 15 | 0.12 |
| MHW/MHQ | 82 | 9.53 |
| HQ1 | — | 2,0 (Komma!) |
| HQ2 | — | 3,0 (Komma!) |

### Hochwasser-Kategorien (Schwellenwerte)

| Kategorie | W [cm] | Q [m³/s] | Essig | Kirchheim | Niederberg |
|-----------|--------|-----------|-------|-----------|------------|
| EV-Einsatzplan | 60 | 1.6 | ✅ | ✅ | k.A. |
| HQ10 | 144 | 12.4 | ✅ | ✅ | - |
| HQ100 | - | 78 | W fehlt | ✅ | - |
| HQExtrem | - | 215 | W fehlt | W fehlt | - |

**Wichtig**: Nicht alle Stationen haben vollständige Schwellenwerte. Jeder Wert
**muss** einzeln auf `None` geprüft werden.

### Aktuelle Werte

| Zeile | W [cm] | Q [m³/s] |
|-------|--------|-----------|
| Datum/Zeit | 0 | 0.00 |
| Tendenz | -14 | -0.000 |
| Stauwert |  0.4 | — |

## Edge Cases

1. **Reine Wasserstandsstationen** (Niederberg, Zieverich): Alle Q-Werte sind `-`
   oder `k.A.`. Sensoren für Abfluss müssen `None` anzeigen, nicht 0.
2. **Fehlende Schwellenwerte**: Essig hat kein HQ100_W und HQExtrem_W. Status kann
   nur anhand Q berechnet werden.
3. **Vussem/Wichterich**: Alle HQ-Werte sind `-`. Keine Schwellen verfügbar.
4. **Umlaute**: HTML-Entities (`&auml;`, `&ouml;`, `&uuml;`) werden in den Links als
   ASCII-Umschrift verwendet.
5. **Zahlenformat-Mix**: HQ1/HQ2 verwenden Komma, alles andere Punkt.
6. **Datenstand**: Einzelne Pegel können bis zu 1 Stunde älter sein als der
   Seitenstand.
7. **Stauwert**: Zusätzliche Zeile in den aktuellen Werten, kein Messwert.
8. **Betreiber**: Kirchheim wird von e-regio betrieben, alle anderen vom Erftverband.

## Stabile ID-Strategie

Jeder Pegel erhält eine stabile textuelle ID aus dem href-Attribut:
- Extraktion: `Pegel_{ID}_zr.html` → `{ID}`
- Diese ID ändert sich nur, wenn der Erftverband die URL-Struktur ändert
- Keine Abhängigkeit von der Anzeigeposition in der Tabelle
- Keine Abhängigkeit vom Stationsnamen (der sich theoretisch ändern könnte)
