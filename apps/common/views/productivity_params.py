from django.utils.dateparse import parse_datetime

from core.utils.date_utils import parse_to_utc_naive


def parse_required_dates(params):
    """
    Parses start_date, end_date and client_now from the query params.
    Returns (start_date, end_date, client_now, error); error is None when valid.
    """
    start_str      = params.get("start_date")
    end_str        = params.get("end_date")
    client_now_str = params.get("client_now")

    if not start_str or not end_str or not client_now_str:
        return None, None, None, "start_date, end_date and client_now are required"

    start_date = parse_to_utc_naive(start_str)
    end_date   = parse_to_utc_naive(end_str)

    if start_date is None or end_date is None:
        return None, None, None, "start_date and end_date must be ISO 8601 with timezone (e.g. 2026-05-27T05:00:00Z)"

    client_now = parse_datetime(client_now_str)
    if client_now is None or client_now.tzinfo is None:
        return None, None, None, "client_now must be a timezone-aware ISO 8601 datetime (e.g. 2025-12-20T11:00:00Z)"

    return start_date, end_date, client_now, None


def parse_optional_int(params, key):
    """Returns the query param as int, or None if missing or not a valid integer."""
    val = params.get(key)
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
