from datetime import datetime, timezone

import pytest

from shared.datetime_helper import DateTimeHelper


def _to_utc_string(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def test_parse_date_summer_uses_utc_plus_two():
    assert _to_utc_string(DateTimeHelper.parse_date("01-06-2026 10:00:00")) == "2026-06-01 08:00:00"


def test_parse_date_winter_uses_utc_plus_one():
    assert _to_utc_string(DateTimeHelper.parse_date("15-01-2025 10:00:00")) == "2025-01-15 09:00:00"


def test_parse_date_rejects_invalid_format():
    with pytest.raises(ValueError):
        DateTimeHelper.parse_date("2026/06/01 10:00")


def test_validate_date_range_accepts_ordered_dates():
    assert DateTimeHelper.validate_date_range(
        "01-06-2026 10:00:00", "01-06-2026 11:00:00", "01-06-2026 12:00:00"
    ) is True


def test_validate_date_range_rejects_unordered_dates():
    with pytest.raises(ValueError):
        DateTimeHelper.validate_date_range(
            "01-06-2026 12:00:00", "01-06-2026 11:00:00", "01-06-2026 10:00:00"
        )
