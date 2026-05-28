def _available_minutes(elapsed_seconds: float, break_seconds: float) -> float:
    return max(elapsed_seconds - break_seconds, 0) / 60


def _productivity_target(sam: float, employee_count: float, elapsed_seconds: float, break_seconds: float):
    if not sam or not employee_count:
        return None
    minutes = _available_minutes(elapsed_seconds, break_seconds)
    if not minutes:
        return None
    return employee_count * minutes / sam


def _efficiency(sam: float, employee_count: float, elapsed_seconds: float, break_seconds: float, total_completed: float):
    target = _productivity_target(sam, employee_count, elapsed_seconds, break_seconds)
    if not target:
        return None
    return round(total_completed / target * 100, 2)


def enrich_rows(data: list[dict]) -> list[dict]:
    for row in data:
        sam            = float(row.get("sku_sam") or 0)
        employee_count = float(row.get("employee_count") or 0)
        elapsed        = float(row.get("elapsed_shift_seconds") or 0)
        breaks         = float(row.get("total_break_seconds") or 0)
        completed      = float(row.get("total_completed") or 0)

        row["productivity_target"] = _productivity_target(sam, employee_count, elapsed, breaks)
        row["efficiency"]          = _efficiency(sam, employee_count, elapsed, breaks, completed)
    return data
