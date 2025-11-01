"""Time utilities for FlowGuard."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def parse_range(range_value: str | None, default_minutes: int = 60) -> tuple[datetime, datetime]:
    """Return (start, end) datetimes for a range string like '1h' or '24h'."""
    end = utc_now()
    if not range_value:
        return end - timedelta(minutes=default_minutes), end

    value = range_value.strip().lower()
    try:
        if value.endswith("h"):
            hours = int(value[:-1])
            return end - timedelta(hours=hours), end
        if value.endswith("m"):
            minutes = int(value[:-1])
            return end - timedelta(minutes=minutes), end
        if value.endswith("d"):
            days = int(value[:-1])
            return end - timedelta(days=days), end
        minutes = int(value)
        return end - timedelta(minutes=minutes), end
    except ValueError:
        return end - timedelta(minutes=default_minutes), end


def to_unix_ms(dt: datetime) -> int:
    """Convert a datetime to milliseconds since epoch."""
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    return int((dt - epoch).total_seconds() * 1000)

