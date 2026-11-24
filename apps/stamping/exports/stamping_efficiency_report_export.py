import io
from datetime import datetime, time

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from apps.common.exports.employee_efficiency_sheets import (
    EMPLOYEE_SHEET_DESCRIPTIONS, add_employee_efficiency_sheets, inject_dynamic_array_metadata,
)
from apps.production.exports.efficiency_report_export import (
    _build_dictionary_sheet, _build_records_sheet, _fmt, _preprocess, _record_value, _style_header,
    _CELL_BORDER, _CELL_FONT, _CENTER, _LEFT,
)
from apps.production.helpers.excel_formatters import fmt_datetime_local, utc_to_local
from apps.production.reports.productivity_columns import RECORD_DESCRIPTIONS, RECORD_LABELS, UNKNOWN_COLUMN_DESCRIPTION
from apps.stamping.reports.stamping_columns import STAMPING_COLUMNS, STAMPING_LABELS, STAMPING_RECORD_FIELDS


def _num(value):
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _as_time(value) -> time | None:
    if isinstance(value, time):
        return value
    if isinstance(value, str) and value:
        return time.fromisoformat(value)
    return None


def _local_naive(value) -> datetime | None:
    local = utc_to_local(value)
    return local.replace(tzinfo=None) if local else None


def _last_record_by_workday(records: list[dict]) -> dict:
    """(workday start, module number) -> timestamp of the workday's last record (UTC)."""
    last = {}
    for r in records:
        key = (r.get("fecha"), r.get("numero_modulo"))
        stamp = r.get("hora_registro")
        if stamp is not None and (key not in last or stamp > last[key]):
            last[key] = stamp
    return last


def _derive(row: dict, last_record) -> dict:
    """Stamping-only columns, computed from the SQL row (the SQL itself is not modified).

    Shift End is the workday's last record; ended_at (session close) can be days later
    when a workday is left open, so it is only the fallback."""
    out = _preprocess(row)

    start = _local_naive(row.get("shift_start_utc"))
    workday_end = _local_naive(row.get("ended_at"))
    shift_end_utc = last_record or row.get("ended_at")
    shift_start = _as_time(row.get("shift_start_time"))
    shift_end = _as_time(row.get("shift_end_time"))

    out["elapsed_hours"] = round((workday_end - start).total_seconds() / 3600, 2) if start and workday_end else None
    out["shift_end"] = fmt_datetime_local(shift_end_utc)
    if shift_start and shift_end:
        out["shift_label"] = f"{shift_start:%H:%M} - {shift_end:%H:%M}"

    # Pieces per unit of the workday: total pieces to stamp / total ordered units.
    ordered, completed, target = _num(row.get("total_ordered")), _num(row.get("total_completed")), _num(row.get("unit_target"))
    factor = (_num(row.get("total_pieces_to_stamp")) or 0) / ordered if ordered else None
    out["pieces_produced"] = round(completed * factor, 2) if factor is not None and completed is not None else None
    out["target_pieces"] = round(target * factor, 2) if factor is not None and target is not None else None

    return out


def _has_output(row: dict) -> bool:
    """Rows with zero efficiency or no pieces produced are left out of the report."""
    return bool(_num(row.get("efficiency"))) and bool(_num(row.get("pieces_produced")))


def _build_efficiency_sheet(wb, rows: list[dict]):
    ws = wb.create_sheet("Eficiencia")
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 22
    fields = [key for key, *_ in STAMPING_COLUMNS]
    _style_header(ws, [STAMPING_LABELS[f] for f in fields])
    for row_idx, record in enumerate(rows, start=2):
        for col_idx, field in enumerate(fields, start=1):
            value = _fmt(field, record.get(field))
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = _CELL_FONT
            cell.border = _CELL_BORDER
            cell.alignment = _CENTER if isinstance(value, (int, float)) else _LEFT
            if field == "productividad" and isinstance(value, float):
                cell.number_format = "0.00%"  # SQL ratio (produced / installed) shown as a percentage
            elif isinstance(value, float):
                cell.number_format = "General"
    for col_idx, field in enumerate(fields, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = max(len(STAMPING_LABELS[field]) + 4, 14)
    return ws


def build_stamping_efficiency_report_excel(data: list[dict], has_employee: bool = False, records: list[dict] | None = None) -> bytes:
    # has_employee is kept for the shared view's signature (employee columns are not part of this report).
    last_records = _last_record_by_workday(records or [])
    rows = [
        r for r in (_derive(d, last_records.get((d.get("shift_start_utc"), d.get("module_number")))) for d in data)
        if _has_output(r)
    ]

    record_values = [{f: _record_value(f, r.get(f)) for f in STAMPING_RECORD_FIELDS} for r in (records or [])]
    record_fields = [f for f in STAMPING_RECORD_FIELDS if any(v[f] != "" for v in record_values)]

    entries = {label: desc for _, label, desc in STAMPING_COLUMNS}
    entries.update(EMPLOYEE_SHEET_DESCRIPTIONS)
    for f in record_fields:
        entries.setdefault(RECORD_LABELS.get(f, f), RECORD_DESCRIPTIONS.get(f, UNKNOWN_COLUMN_DESCRIPTION))

    wb = Workbook()
    _build_dictionary_sheet(wb.active, list(entries.items()))
    efficiency_ws = _build_efficiency_sheet(wb, rows)
    dynamic_cells = add_employee_efficiency_sheets(wb, efficiency_ws, len(rows))
    _build_records_sheet(wb, record_fields, record_values)

    buf = io.BytesIO()
    wb.save(buf)
    return inject_dynamic_array_metadata(buf.getvalue(), wb.sheetnames, dynamic_cells)
