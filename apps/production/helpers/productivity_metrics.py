def _efficiency(sam, employee_count, productive_seconds, total_completed):

    sam, employee_count, productive_seconds, total_completed = (
        float(sam),
        float(employee_count),
        float(productive_seconds),
        float(total_completed),
    )
    if not employee_count or not productive_seconds or not sam:
        return None
    
    productive_units = _productivity_target(sam, employee_count, productive_seconds)
    return round(total_completed / productive_units * 100, 2)


def _productivity_target(sam, employee_count, productive_seconds):
    sam, employee_count, productive_seconds = (
        float(sam),
        float(employee_count),
        float(productive_seconds),
    )
    if not sam:
        return None
    productive_minutes = productive_seconds / 60
    return employee_count * productive_minutes / sam


def enrich_rows(data: list[dict]) -> list[dict]:
    for row in data:
        sam = row.get("sku_sam") or 0
        employee_count = row.get("employee_count") or 0
        productive_seconds = row.get("total_productive_seconds") or 0

        row["productivity_target"] = _productivity_target(
            sam,
            employee_count,
            productive_seconds,
        )

        row["efficiency"] = _efficiency(
            sam,
            employee_count,
            productive_seconds,
            total_completed=row.get("total_completed") or 0,
        )
    return data
