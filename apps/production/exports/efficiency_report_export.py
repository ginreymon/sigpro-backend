import io
from datetime import date, time
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from apps.production.reports.productivity_columns import (
    CATALOG, REPORT_COLUMNS, EXCLUDED_FIELDS, ROUND_FIELDS, UTC_FIELDS, UNKNOWN_COLUMN_DESCRIPTION,
)
from apps.production.helpers.excel_formatters import (
    fmt_datetime_local, fmt_breaks_text, fmt_employees_text, fmt_additional_times_text,
    fmt_production_orders_text, fmt_references_text,
)

DICTIONARY_SHEET = "Descripción de columnas"

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
_WRAP   = Alignment(horizontal="left",   vertical="top", wrap_text=True)

# JSON arrays returned by the SQL functions -> readable text in the same column.
_TEXT_FORMATTERS = {
    "breaks":            fmt_breaks_text,
    "employees":         fmt_employees_text,
    "additional_times":  fmt_additional_times_text,
    "production_orders": fmt_production_orders_text,
    "references":        fmt_references_text,
}


def _preprocess(record: dict) -> dict:
    out = dict(record)
    for field in UTC_FIELDS:
        out[field] = fmt_datetime_local(out.get(field))
    for field, formatter in _TEXT_FORMATTERS.items():
        if field in out:
            out[field] = formatter(out[field])
    return out


def _fmt(field: str, value):
    if value is None or value == "":
        return ""
    if isinstance(value, date) and not isinstance(value, bool):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if isinstance(value, Decimal):
        value = float(value)
    if field in ROUND_FIELDS and isinstance(value, (int, float)):
        places = ROUND_FIELDS[field]
        rounded = round(float(value), places)
        return int(rounded) if places == 0 else rounded
    return value


def _present_columns(records: list[dict]) -> list[str]:
    """Catalog order first, then unknown keys; drops columns empty in every record."""
    keys = []
    for record in records:
        for key in record:
            if key not in keys and key not in EXCLUDED_FIELDS:
                keys.append(key)
    ordered = [c[0] for c in REPORT_COLUMNS if c[0] in keys] + [k for k in keys if k not in CATALOG]
    return [k for k in ordered if any(_fmt(k, r.get(k)) != "" for r in records)]


def _style_header(ws, labels):
    for col_idx, label in enumerate(labels, start=1):
        cell = ws.cell(row=1, column=col_idx, value=label)
        cell.font      = _HEADER_FONT
        cell.fill      = _HEADER_FILL
        cell.alignment = _CENTER
        cell.border    = _CELL_BORDER


def build_efficiency_report_excel(data: list[dict], has_employee: bool = False) -> bytes:
    # has_employee is kept for the caller's signature: employee_* columns are
    # NULL (hence dropped) unless the report was filtered by an employee.
    records = [_preprocess(r) for r in data]
    fields = _present_columns(records)
    labels = {f: CATALOG.get(f, (f, UNKNOWN_COLUMN_DESCRIPTION))[0] for f in fields}

    wb = Workbook()
    ws = wb.active
    ws.title = "Eficiencia"
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 22

    # ── Headers ──────────────────────────────────────────────────────────────
    _style_header(ws, [labels[f] for f in fields])

    # ── Rows ─────────────────────────────────────────────────────────────────
    for row_idx, record in enumerate(records, start=2):
        for col_idx, field in enumerate(fields, start=1):
            value = _fmt(field, record.get(field))
            cell  = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font      = _CELL_FONT
            cell.border    = _CELL_BORDER
            cell.alignment = _CENTER if isinstance(value, (int, float)) else _LEFT

    # ── Column widths ────────────────────────────────────────────────────────
    for col_idx, field in enumerate(fields, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = max(len(labels[field]) + 4, 14)

    # ── Data dictionary (only the columns present in the main sheet) ─────────
    dic = wb.create_sheet(DICTIONARY_SHEET)
    dic.freeze_panes = "A2"
    _style_header(dic, ["Nombre técnico", "Nombre descriptivo", "Descripción"])
    for row_idx, field in enumerate(fields, start=2):
        label, desc = CATALOG.get(field, (field, UNKNOWN_COLUMN_DESCRIPTION))
        for col_idx, value in enumerate((field, label, desc), start=1):
            cell = dic.cell(row=row_idx, column=col_idx, value=value)
            cell.font, cell.border, cell.alignment = _CELL_FONT, _CELL_BORDER, _WRAP
    dic.column_dimensions["A"].width = 28
    dic.column_dimensions["B"].width = 30
    dic.column_dimensions["C"].width = 100

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
