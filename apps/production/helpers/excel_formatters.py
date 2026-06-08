from datetime import datetime, timezone, timedelta

_LOCAL_OFFSET = timedelta(hours=-5)  # Colombia UTC-5


def utc_to_local(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value + _LOCAL_OFFSET


def fmt_datetime_local(value) -> str:
    local = utc_to_local(value)
    return local.strftime("%Y-%m-%d %H:%M") if local else ""


def fmt_breaks_text(breaks: list) -> str:
    if not breaks:
        return ""
    parts = []
    for b in breaks:
        name = (b.get("name") or "").strip()
        desc = (b.get("description") or b.get("custom_reason") or "").strip()
        parts.append(name or desc)
    return " ; ".join(parts)
