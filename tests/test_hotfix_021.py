from __future__ import annotations

from custom_components.erftverband_riverlevel.const import (
    FLOOD_STATES,
    STATE_UNKNOWN,
    VERSION,
)
from custom_components.erftverband_riverlevel.models import (
    StationMetadata,
    StationThresholds,
)


def test_stored_threshold_dict_is_rehydrated() -> None:
    metadata = StationMetadata(
        station_id="essig",
        station_name="Essig",
        waterbody="Orbach",
        detail_url="https://example.invalid/Pegel_Essig_zr.html",
        thresholds={
            "ev_alarm_cm": 100.0,
            "hq10_cm": 150.0,
        },
    )

    assert isinstance(metadata.thresholds, StationThresholds)
    assert metadata.thresholds.ev_alarm_cm == 100.0
    assert metadata.thresholds.hq10_cm == 150.0


def test_missing_stored_thresholds_get_empty_model() -> None:
    metadata = StationMetadata(
        station_id="essig",
        station_name="Essig",
        waterbody="Orbach",
        detail_url="https://example.invalid/Pegel_Essig_zr.html",
        thresholds=None,
    )

    assert isinstance(metadata.thresholds, StationThresholds)
    assert metadata.thresholds.ev_alarm_cm is None


def test_unknown_is_valid_flood_enum_option() -> None:
    assert STATE_UNKNOWN in FLOOD_STATES


def test_hotfix_version() -> None:
    assert VERSION == "0.2.1"
