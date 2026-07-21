from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class StationDescriptor:
    station_id: str
    name: str
    waterbody: str
    href: str


@dataclass
class StationThresholds:
    ev_w: float | None = None
    ev_q: float | None = None
    hq10_w: float | None = None
    hq10_q: float | None = None
    hq100_w: float | None = None
    hq100_q: float | None = None
    hqextrem_w: float | None = None
    hqextrem_q: float | None = None

    def to_dict(self) -> dict[str, float | None]:
        return {
            "ev_w": self.ev_w,
            "ev_q": self.ev_q,
            "hq10_w": self.hq10_w,
            "hq10_q": self.hq10_q,
            "hq100_w": self.hq100_w,
            "hq100_q": self.hq100_q,
            "hqextrem_w": self.hqextrem_w,
            "hqextrem_q": self.hqextrem_q,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StationThresholds:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class StationData:
    station_id: str
    name: str
    waterbody: str
    operator: str | None = None
    easting: int | None = None
    northing: int | None = None
    catchment_area: float | None = None
    data_range: str | None = None
    thresholds: StationThresholds = field(default_factory=StationThresholds)
    water_level_cm: float | None = None
    discharge_m3s: float | None = None
    wl_trend: float | None = None
    q_trend: float | None = None
    measured_at: datetime | None = None
    main_values: dict[str, tuple[float | None, float | None]] = field(default_factory=dict)
    detail_fetched_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "station_id": self.station_id,
            "name": self.name,
            "waterbody": self.waterbody,
            "operator": self.operator,
            "easting": self.easting,
            "northing": self.northing,
            "catchment_area": self.catchment_area,
            "data_range": self.data_range,
            "thresholds": self.thresholds.to_dict(),
            "water_level_cm": self.water_level_cm,
            "discharge_m3s": self.discharge_m3s,
            "wl_trend": self.wl_trend,
            "q_trend": self.q_trend,
            "measured_at": self.measured_at.isoformat() if self.measured_at else None,
            "main_values": {k: (v[0], v[1]) for k, v in self.main_values.items()},
            "detail_fetched_at": (
                self.detail_fetched_at.isoformat() if self.detail_fetched_at else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StationData:
        thresholds_data = data.get("thresholds", {})
        if isinstance(thresholds_data, dict):
            thresholds = StationThresholds.from_dict(thresholds_data)
        else:
            thresholds = StationThresholds()

        measured_at = None
        if data.get("measured_at"):
            measured_at = datetime.fromisoformat(data["measured_at"])

        detail_fetched_at = None
        if data.get("detail_fetched_at"):
            detail_fetched_at = datetime.fromisoformat(data["detail_fetched_at"])

        main_values = {}
        for k, v in data.get("main_values", {}).items():
            if isinstance(v, list) and len(v) == 2:
                main_values[k] = (v[0], v[1])
            elif isinstance(v, tuple) and len(v) == 2:
                main_values[k] = v

        return cls(
            station_id=data["station_id"],
            name=data["name"],
            waterbody=data["waterbody"],
            operator=data.get("operator"),
            easting=data.get("easting"),
            northing=data.get("northing"),
            catchment_area=data.get("catchment_area"),
            data_range=data.get("data_range"),
            thresholds=thresholds,
            water_level_cm=data.get("water_level_cm"),
            discharge_m3s=data.get("discharge_m3s"),
            wl_trend=data.get("wl_trend"),
            q_trend=data.get("q_trend"),
            measured_at=measured_at,
            main_values=main_values,
            detail_fetched_at=detail_fetched_at,
        )


@dataclass
class CoordinatorData:
    stations: dict[str, StationData] = field(default_factory=dict)
    last_update: datetime | None = None
    source_reachable: bool = True
    cache_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "stations": {k: v.to_dict() for k, v in self.stations.items()},
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "source_reachable": self.source_reachable,
            "cache_used": self.cache_used,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CoordinatorData:
        stations = {}
        for k, v in data.get("stations", {}).items():
            stations[k] = StationData.from_dict(v)
        last_update = None
        if data.get("last_update"):
            last_update = datetime.fromisoformat(data["last_update"])
        return cls(
            stations=stations,
            last_update=last_update,
            source_reachable=data.get("source_reachable", True),
            cache_used=data.get("cache_used", False),
        )
