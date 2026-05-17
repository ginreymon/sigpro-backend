def _efficiency(sam_earned, employee_count, activity_seconds):
    """
    Efficiency = SAM earned / (employees × activity minutes)
    Returns None if denominator is zero or missing.
    """
    if not employee_count or not activity_seconds:
        return None
    activity_minutes = activity_seconds / 60
    return round(float(sam_earned) / (employee_count * activity_minutes) * 100, 2)


def enrich_rows(data: list[dict]) -> list[dict]:
    for row in data:
        row["efficiency"] = _efficiency(
            sam_earned=row.get("total_sam_earned") or 0,
            employee_count=row.get("employee_count") or 0,
            activity_seconds=row.get("total_activity_seconds") or 0,
        )
    return data
