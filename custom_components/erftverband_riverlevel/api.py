from __future__ import annotations

from datetime import datetime
from html.parser import HTMLParser
from typing import Any
from zoneinfo import ZoneInfo

from aiohttp import ClientSession, ClientTimeout

from .const import DETAIL_URL_TEMPLATE, OVERVIEW_URL, REQUEST_TIMEOUT, USER_AGENT
from .models import StationData, StationDescriptor, StationThresholds

TZ_BERLIN = ZoneInfo("Europe/Berlin")


def parse_german_number(value: str) -> float | None:
    value = value.strip()
    if not value:
        return None
    value = value.replace("\xa0", "").replace("&nbsp;", "").replace("&thinsp;", "")
    stripped = value.strip()
    if not stripped or stripped in ("-", "\u2014", "\u2013", "---", "k.A."):
        return None
    value = stripped
    negative = False
    if value.startswith("-"):
        negative = True
        value = value[1:].lstrip()
    if value.startswith("+"):
        value = value[1:].lstrip()
    last_dot = value.rfind(".")
    last_comma = value.rfind(",")
    if last_comma > last_dot:
        value = value.replace(".", "")
        value = value.replace(",", ".")
    elif last_dot > last_comma:
        value = value.replace(",", "")
    if not value.replace(".", "").replace("-", "").isdigit():
        return None
    try:
        result = float(value)
        return -result if negative else result
    except ValueError, TypeError:
        return None


def parse_german_datetime(value: str) -> datetime | None:
    value = value.strip()
    for fmt in ("%d.%m.%Y %H:%M", "%d.%m.%y %H:%M", "%d.%m.%Y %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=TZ_BERLIN)
        except ValueError:
            continue
    return None


async def fetch_overview(session: ClientSession) -> str:
    headers = {"User-Agent": USER_AGENT}
    timeout = ClientTimeout(total=REQUEST_TIMEOUT)
    async with session.get(OVERVIEW_URL, headers=headers, timeout=timeout) as resp:
        resp.raise_for_status()
        return await resp.text()


async def fetch_detail_page(session: ClientSession, station_id: str) -> str:
    url = DETAIL_URL_TEMPLATE.format(station_id=station_id)
    headers = {"User-Agent": USER_AGENT}
    timeout = ClientTimeout(total=REQUEST_TIMEOUT)
    async with session.get(url, headers=headers, timeout=timeout) as resp:
        resp.raise_for_status()
        return await resp.text()


def extract_station_id_from_href(href: str) -> str | None:
    if not href or "_zr.html" not in href:
        return None
    start = href.rfind("/")
    if start == -1:
        start = 0
    else:
        start += 1
    name_part = href[start:]
    if name_part.startswith("Pegel_"):
        name_part = name_part[6:]
    if name_part.endswith("_zr.html"):
        name_part = name_part[: -len("_zr.html")]
    return name_part if name_part else None


def parse_station_name_cell(cell_text: str) -> tuple[str, str] | None:
    text = cell_text.strip()
    if "(" in text and text.endswith(")"):
        name = text[: text.index("(")].strip()
        waterbody = text[text.index("(") + 1 : text.rindex(")")].strip()
        if name and waterbody:
            return name, waterbody
    return None


class LinkAndTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._text = ""
        self._href = ""
        self._in_a = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._in_a = True
            self._text = ""
            self._href = ""
            for name, value in attrs:
                if name == "href" and value:
                    self._href = value

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_a:
            self._in_a = False
            text = self._text.strip()
            if text and self._href and "_zr.html" in self._href:
                self.links.append((text, self._href))
            self._text = ""
            self._href = ""

    def handle_data(self, data: str) -> None:
        if self._in_a:
            self._text += data

    def handle_entityref(self, name: str) -> None:
        if self._in_a:
            char = {
                "auml": "\u00e4",
                "ouml": "\u00f6",
                "uuml": "\u00fc",
                "Auml": "\u00c4",
                "Ouml": "\u00d6",
                "Uuml": "\u00dc",
                "szlig": "\u00df",
            }.get(name, f"&{name};")
            self._text += char


def parse_overview_stations(html: str) -> list[StationDescriptor]:
    parser = LinkAndTextParser()
    parser.feed(html)
    stations: list[StationDescriptor] = []
    seen_ids: set[str] = set()
    for text, href in parser.links:
        parts = parse_station_name_cell(text)
        if parts is None:
            continue
        name, waterbody = parts
        station_id = extract_station_id_from_href(href)
        if station_id and station_id not in seen_ids:
            seen_ids.add(station_id)
            stations.append(
                StationDescriptor(
                    station_id=station_id,
                    name=name,
                    waterbody=waterbody,
                    href=href,
                )
            )
    return stations


def parse_overview_table(html: str) -> dict[str, dict[str, Any]]:
    stations = parse_overview_stations(html)
    result: dict[str, dict[str, Any]] = {}
    for station in stations:
        result[f"{station.name}|{station.waterbody}"] = {
            "name": station.name,
            "waterbody": station.waterbody,
            "measured_at": None,
            "water_level_cm": None,
            "wl_trend": None,
            "discharge_m3s": None,
            "q_trend": None,
        }
    station_vals = _extract_table_values(html)
    for vals in station_vals:
        key = f"{vals['name']}|{vals['waterbody']}"
        if key in result:
            result[key].update(vals)
    return result


def _extract_table_values(html: str) -> list[dict[str, Any]]:
    """Extract station measurement rows from the HOWIS overview table."""
    parser = OverviewTableParser()
    parser.feed(html)
    return parser.rows


class OverviewTableParser(HTMLParser):
    """Simplified flat parser for the HOWIS overview table.

    The HOWIS overview table has a complex, malformed HTML structure
    with interleaved tbody/tr elements. This parser ignores nesting
    and instead tracks state based on tag types alone.
    """

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, Any]] = []
        self._cells: list[str] = []
        self._current_cell: str | None = None
        self._in_table = False
        self._in_station_row = False
        self._collected_data_cells = 0
        self._has_collected_station = False
        self._station_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._in_table = True
        if not self._in_table:
            return
        if tag == "tr":
            if self._in_station_row:
                self._flush_station_row()
            self._cells = []
            self._in_station_row = True
        elif tag in ("td", "th") and self._in_station_row:
            self._current_cell = ""
        elif tag == "br" and self._current_cell is not None:
            self._current_cell += " "

    def handle_endtag(self, tag: str) -> None:
        if tag == "table":
            if self._in_station_row:
                self._flush_station_row()
            self._in_table = False
            self._in_station_row = False
        if not self._in_table:
            return
        if tag in ("td", "th") and self._current_cell is not None:
            text = self._current_cell.strip()
            self._cells.append(text)
            self._current_cell = None
        elif tag == "tr" and self._in_station_row:
            self._flush_station_row()
            self._in_station_row = False

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell += data

    def handle_entityref(self, name: str) -> None:
        if self._current_cell is not None:
            char = {
                "auml": "\u00e4",
                "ouml": "\u00f6",
                "uuml": "\u00fc",
                "Auml": "\u00c4",
                "Ouml": "\u00d6",
                "Uuml": "\u00dc",
                "szlig": "\u00df",
                "nbsp": "\u00a0",
                "sup3": "\u00b3",
            }.get(name, f"&{name};")
            self._current_cell += char

    def _flush_station_row(self) -> None:
        if len(self._cells) < 12:
            self._in_station_row = False
            return
        first_cell = self._cells[0].strip()
        if not first_cell or "(" not in first_cell:
            self._in_station_row = False
            return
        parts = parse_station_name_cell(first_cell)
        if parts is None:
            self._in_station_row = False
            return
        name, waterbody = parts
        measured_at = parse_german_datetime(self._cells[1]) if len(self._cells) > 1 else None
        wl = parse_german_number(self._cells[2]) if len(self._cells) > 2 else None
        wl_t = parse_german_number(self._cells[3]) if len(self._cells) > 3 else None
        q = parse_german_number(self._cells[4]) if len(self._cells) > 4 else None
        q_t = parse_german_number(self._cells[5]) if len(self._cells) > 5 else None
        self.rows.append(
            {
                "name": name,
                "waterbody": waterbody,
                "measured_at": measured_at,
                "water_level_cm": wl,
                "wl_trend": wl_t,
                "discharge_m3s": q,
                "q_trend": q_t,
            }
        )


def extract_all_stations_from_overview(
    html: str,
) -> tuple[dict[str, StationData], list[StationDescriptor]]:
    descriptors = parse_overview_stations(html)
    table_data = parse_overview_table(html)
    stations: dict[str, StationData] = {}
    for desc in descriptors:
        station = StationData(
            station_id=desc.station_id,
            name=desc.name,
            waterbody=desc.waterbody,
        )
        row_key = f"{desc.name}|{desc.waterbody}"
        if row_key in table_data:
            row = table_data[row_key]
            station.water_level_cm = row.get("water_level_cm")
            station.discharge_m3s = row.get("discharge_m3s")
            station.wl_trend = row.get("wl_trend")
            station.q_trend = row.get("q_trend")
            station.measured_at = row.get("measured_at")
        stations[desc.station_id] = station
    return stations, descriptors


def parse_detail_html(html: str, station_id: str) -> StationData:
    parser = DetailPageParser(station_id)
    parser.feed(html)
    return parser.get_station_data()


class DetailPageParser(HTMLParser):
    """Parser for HOWIS detail pages.

    Each detail page has <section> elements containing:
    1. Stammdaten (metadata table)
    2. Hauptwerte (statistical values table)
    3. Hochwasser-Kategorien (thresholds table)
    4. Aktuelle Werte (current measurements table)

    Each section starts with an <h4> followed by a <table>.
    """

    def __init__(self, station_id: str) -> None:
        super().__init__()
        self._station_id = station_id
        self._current_section = ""
        self._in_table = False
        self._in_row = False
        self._current_cell: str | None = None
        self._cells: list[str] = []
        self._rows: list[list[str]] = []
        self._sections: dict[str, list[list[str]]] = {}
        self._in_h4 = False
        self._h4_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h4":
            self._in_h4 = True
            self._h4_text = ""
        elif tag == "table":
            self._flush_row()
            self._rows = []
            self._in_table = True
        elif tag == "tr":
            if self._in_table:
                self._flush_row()
                self._in_row = True
                self._cells = []
        elif tag in ("td", "th"):
            if self._in_table:
                self._current_cell = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "h4":
            self._in_h4 = False
            self._current_section = self._h4_text.strip()
            self._h4_text = ""
        elif tag == "table":
            self._flush_row()
            if self._rows:
                self._sections[self._current_section] = self._rows
            self._in_table = False
            self._rows = []
            self._current_cell = None
        elif tag == "tr":
            self._flush_row()
        elif tag in ("td", "th"):
            if self._current_cell is not None:
                self._cells.append(self._current_cell.strip())
                self._current_cell = None

    def _flush_row(self) -> None:
        if self._in_row and any(c.strip() for c in self._cells):
            self._rows.append(self._cells)
        self._in_row = False
        self._cells = []

    def handle_data(self, data: str) -> None:
        if self._in_h4:
            self._h4_text += data
        elif self._current_cell is not None:
            self._current_cell += data

    def handle_entityref(self, name: str) -> None:
        char = {
            "auml": "\u00e4",
            "ouml": "\u00f6",
            "uuml": "\u00fc",
            "Auml": "\u00c4",
            "Ouml": "\u00d6",
            "Uuml": "\u00dc",
            "szlig": "\u00df",
            "nbsp": "\u00a0",
        }.get(name, f"&{name};")
        if self._in_h4:
            self._h4_text += char
        elif self._current_cell is not None:
            self._current_cell += char

    def get_station_data(self) -> StationData:
        data = StationData(station_id=self._station_id, name="", waterbody="")
        self._parse_metadata(data)
        self._parse_thresholds(data)
        self._parse_main_values(data)
        self._parse_current_values(data)

        if not data.name:
            data.name = self._station_id

        data.detail_fetched_at = datetime.now(tz=TZ_BERLIN)
        return data

    def _get_section(self, keyword: str) -> list[list[str]]:
        for section_name, table in self._sections.items():
            if keyword in section_name:
                return table
        return []

    def _parse_metadata(self, data: StationData) -> None:
        table = self._get_section("Stammdaten")
        for row in table:
            if len(row) < 2:
                continue
            key = row[0].strip()
            val = row[1].strip()
            if key == "Pegel":
                data.name = val
            elif "Gew" in key and ("sser" in key or "sser" in key):
                data.waterbody = val
            elif key == "Betreiber":
                data.operator = val
            elif key == "Rechtswert":
                try:
                    data.easting = int(val)
                except ValueError, TypeError:
                    pass
            elif key == "Hochwert":
                try:
                    data.northing = int(val)
                except ValueError, TypeError:
                    pass
            elif "Einzugsgebiet" in key:
                data.catchment_area = parse_german_number(val)

        for section_name in self._sections:
            if "Hauptwerte" in section_name:
                idx = section_name.find("(")
                if idx != -1:
                    end_idx = section_name.find(")", idx)
                    if end_idx != -1:
                        data.data_range = section_name[idx : end_idx + 1]

    def _parse_thresholds(self, data: StationData) -> None:
        table = self._get_section("Hochwasser-Kategorien")
        th = StationThresholds()
        for row in table:
            if len(row) < 3:
                continue
            label = row[0].strip()
            w_val = parse_german_number(row[1]) if len(row) > 1 else None
            q_val = parse_german_number(row[2]) if len(row) > 2 else None
            if "EV" in label or "Einsatzplan" in label:
                th.ev_w = w_val
                th.ev_q = q_val
            elif "HQ10" in label and "HQ100" not in label and "HQExtrem" not in label:
                th.hq10_w = w_val
                th.hq10_q = q_val
            elif "HQ100" in label and "HQExtrem" not in label:
                th.hq100_w = w_val
                th.hq100_q = q_val
            elif "HQExtrem" in label:
                th.hqextrem_w = w_val
                th.hqextrem_q = q_val
        data.thresholds = th

    def _parse_main_values(self, data: StationData) -> None:
        table = self._get_section("Hauptwerte")
        for row in table:
            if len(row) < 3:
                continue
            label = row[0].strip()
            w_val = parse_german_number(row[1]) if len(row) > 1 else None
            q_val = parse_german_number(row[2]) if len(row) > 2 else None
            key = label.split(" ")[0].replace("/", "_")
            data.main_values[key] = (w_val, q_val)

    def _parse_current_values(self, data: StationData) -> None:
        table = self._get_section("Aktuelle Werte")
        for row in table:
            if len(row) < 2:
                continue
            label = row[0].strip()
            w_val = parse_german_number(row[1]) if len(row) > 1 else None
            q_val = parse_german_number(row[2]) if len(row) > 2 else None
            dt = parse_german_datetime(label)
            if dt is not None:
                data.measured_at = dt
                data.water_level_cm = w_val
                data.discharge_m3s = q_val
            elif "Tendenz" in label:
                data.wl_trend = w_val
                data.q_trend = q_val
