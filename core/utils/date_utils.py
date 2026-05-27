from datetime import datetime, timezone as dt_timezone

from django.utils import timezone as dj_timezone
from django.utils.dateparse import parse_datetime


def to_utc_naive(dt: datetime) -> datetime:
    """Convert any datetime (aware or naive) to UTC naive.

    Aware  → convert to UTC then strip tzinfo.
    Naive  → assumed already UTC, returned as-is.
    """
    if dt.tzinfo is not None:
        return dt.astimezone(dt_timezone.utc).replace(tzinfo=None)
    return dt


def apply_client_offset(naive_dt: datetime, client_now: datetime) -> datetime:
    """Correct a naive UTC datetime for clock drift between client and server.

    Computes: offset = server_now (UTC) - client_now (UTC aware)
    Returns:  naive_dt + offset

    With synced clocks offset ≈ 0. Corrects minor drift without timezone
    conversion (timezone is already handled before this call via parse_to_utc_naive).
    """
    offset = dj_timezone.now() - client_now
    return naive_dt + offset


def parse_to_utc_naive(date_str: str) -> datetime | None:
    """Parse an ISO 8601 string (with or without timezone) → UTC naive datetime.

    Returns None if the string cannot be parsed.

    Accepted formats:
        '2026-05-27T05:00:00Z'
        '2026-05-27T00:00:00-05:00'
        '2026-05-27T05:00:00'        (naive → assumed UTC, returned as-is)
    """
    dt = parse_datetime(date_str)
    if dt is None:
        return None
    return to_utc_naive(dt)
