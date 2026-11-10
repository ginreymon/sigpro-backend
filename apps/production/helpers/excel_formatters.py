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


def _fmt_list_text(items, render) -> str:
    """Joins render(item) with "; ". Null/empty/non-list input or malformed items give ""."""
    if not isinstance(items, list):
        return ""
    parts = []
    for item in items:
        if isinstance(item, dict):
            text = render(item).strip()
            if text:
                parts.append(text)
    return "; ".join(parts)


def _join(*values) -> str:
    return " ".join(str(v).strip() for v in values if v not in (None, ""))


def fmt_breaks_text(breaks) -> str:
    return _fmt_list_text(
        breaks,
        lambda b: (b.get("name") or "").strip() or (b.get("description") or b.get("custom_reason") or ""),
    )


def fmt_employees_text(employees) -> str:
    return _fmt_list_text(employees, lambda e: _join(e.get("full_name"), e.get("id_number")))


def fmt_production_orders_text(orders) -> str:
    return _fmt_list_text(orders, lambda o: _join(o.get("op_type"), o.get("op_number")))


def fmt_references_text(references) -> str:
    """Unique references of the row's orders (several orders may share one reference)."""
    if not isinstance(references, list):
        return ""
    unique = dict.fromkeys(
        str(r["reference"]).strip() for r in references
        if isinstance(r, dict) and r.get("reference") not in (None, "")
    )
    return "; ".join(unique)


def fmt_sam_text(references):
    """SAM of each unique reference, in the same order as fmt_references_text.

    One reference -> a real float (numeric Excel cell, full precision).
    Several references -> text joined with "; " using repr(float), no digit lost.
    """
    if not isinstance(references, list):
        return ""
    unique = {}
    for r in references:
        if isinstance(r, dict) and r.get("reference") not in (None, ""):
            unique.setdefault(str(r["reference"]).strip(), r.get("sam"))
    sams = list(unique.values())
    if len(sams) == 1:
        return "" if sams[0] is None else float(sams[0])
    # An empty slot keeps the Nth SAM aligned with the Nth reference.
    return "; ".join("" if s is None else repr(float(s)) for s in sams)


def fmt_additional_times_text(additional_times) -> str:
    return _fmt_list_text(
        additional_times,
        lambda t: _join(
            t.get("code_number"), t.get("process"),
            f"x{t['quantity']}" if t.get("quantity") is not None else None,
        ),
    )
