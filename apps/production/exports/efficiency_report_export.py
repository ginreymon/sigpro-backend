import io
from datetime import date, time

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from apps.production.reports.productivity_columns import (
    SUMMARY_COLUMNS, EMPLOYEE_COLUMNS, ROUND_FIELDS, UTC_FIELDS, COMPUTED_FIELDS,
    ADDITIONAL_TIMES_COLUMN,
)
from apps.production.helpers.excel_formatters import (
    fmt_datetime_local, fmt_breaks_text, fmt_employees_text, fmt_additional_times_text,
)

_HEADER_FILL = PatternFill("solid", fgColor="1F3864")
_HEADER_FONT = Font(color="FFFFFF", bold=True, size=10)
_CELL_FONT   = Font(size=10)
_BORDER_SIDE = Side(style="thin", color="D9D9D9")
_CELL_BORDER = Border(
    left=_BORDER_SIDE, right=_BORDER_SIDE,
    top=_BORDER_SIDE,  bottom=_BORDER_SIDE,
)
_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=False)
_LEFT   = Alignment(horizontal="left",   vertical="center")


def _preprocess(record: dict) -> dict:
    out = dict(record)
    for field in UTC_FIELDS:
        out[field] = fmt_datetime_local(out.get(field))
    out["breaks_text"] = fmt_breaks_text(out.get("breaks"))
    out["employees_text"] = fmt_employees_text(out.get("employees"))
    out["additional_times_text"] = fmt_additional_times_text(out.get("additional_times"))
    return out


def _fmt(field: str, value):
    if value is None or value == "":
        return ""
    if isinstance(value, date) and not isinstance(value, bool):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if field in ROUND_FIELDS and isinstance(value, (int, float)):
        places = ROUND_FIELDS[field]
        rounded = round(float(value), places)
        return int(rounded) if places == 0 else rounded
    return value


def build_efficiency_report_excel(data: list[dict], has_employee: bool = False) -> bytes:
    columns = EMPLOYEE_COLUMNS if has_employee else SUMMARY_COLUMNS
    if data and "additional_times" in data[0]:
        columns = columns + [ADDITIONAL_TIMES_COLUMN]
    records = [_preprocess(r) for r in data]

    wb = Workbook()
    ws = wb.active
    ws.title = "Eficiencia"
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 22

    # ── Headers ──────────────────────────────────────────────────────────────
    for col_idx, (_, label) in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=col_idx, value=label)
        cell.font      = _HEADER_FONT
        cell.fill      = _HEADER_FILL
        cell.alignment = _CENTER
        cell.border    = _CELL_BORDER

    # ── Rows ─────────────────────────────────────────────────────────────────
    for row_idx, record in enumerate(records, start=2):
        for col_idx, (field, _) in enumerate(columns, start=1):
            raw   = record.get(field)
            value = _fmt(field, raw)
            cell  = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font      = _CELL_FONT
            cell.border    = _CELL_BORDER
            cell.alignment = _CENTER if isinstance(value, (int, float)) else _LEFT

    # ── Column widths ────────────────────────────────────────────────────────
    for col_idx, (_, label) in enumerate(columns, start=1):
        letter = get_column_letter(col_idx)
        ws.column_dimensions[letter].width = max(len(label) + 4, 14)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
