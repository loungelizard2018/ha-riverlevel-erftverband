from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StationDescriptor:
    station_id: str
    station_name: str
    waterbody: str
    detail_url: str


@dataclass
class StationThresholds:
    mw_cm: float | None = None
    mhw_cm: float | None = None
    ev_alarm_cm: float | None = None
    ev_alarm_m3s: float | None = None
    hq10_cm: float | None = None
    hq10_m3s: float | None = None
    hq100_cm: float | None = None
    hq100_m3s: float | None = None
    hqextrem_cm: float | None = None
    hqextrem_m3s: float | None = None


@dataclass
class StationMetadata:
    station_id: str
    station_name: str
    waterbody: str
    detail_url: str
    thresholds: StationThresholds = field(default_factory=StationThresholds)
    catchment_area_km2: float | None = None
    fetched_at: str | None = None

    def __post_init__(self) -> None:
        """Rehydrate nested threshold data loaded from Home Assistant storage."""
        if isinstance(self.thresholds, dict):
            self.thresholds = StationThresholds(**self.thresholds)
        elif self.thresholds is None:
            self.thresholds = StationThresholds()


@dataclass
class StationMeasurement:
    measured_at: str | None
    age_minutes: int | None
    water_level_cm: float | None
    water_trend_cm_h: float | None
    discharge_m3s: float | None
    discharge_trend_m3s_h: float | None


@dataclass
class CoordinatorData:
    ok: bool = False
    live_fetch_ok: bool = False
    cache_used: bool = False
    source_reachable: bool = False
    fetched_at: str | None = None
    error: str | None = None
    stations: dict[str, StationMeasurement] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        stations_dict: dict[str, dict[str, Any]] = {}
        for sid, m in self.stations.items():
            stations_dict[sid] = {
                "measured_at": m.measured_at,
                "age_minutes": m.age_minutes,
                "water_level_cm": m.water_level_cm,
                "water_trend_cm_h": m.water_trend_cm_h,
                "discharge_m3s": m.discharge_m3s,
                "discharge_trend_m3s_h": m.discharge_trend_m3s_h,
            }
        return {
            "ok": self.ok,
            "live_fetch_ok": self.live_fetch_ok,
            "cache_used": self.cache_used,
            "source_reachable": self.source_reachable,
            "fetched_at": self.fetched_at,
            "error": self.error,
            "stations": stations_dict,
        }
