import io
from datetime import date, time
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from apps.production.reports.productivity_columns import (
    CATALOG, REPORT_COLUMNS, EXCLUDED_FIELDS, ROUND_FIELDS, UTC_FIELDS, UNKNOWN_COLUMN_DESCRIPTION,
    RECORD_COLUMNS, RECORD_LABELS, RECORD_DESCRIPTIONS, RECORD_EXCLUDED_FIELDS, RECORD_UTC_FIELDS,
)
from apps.production.helpers.excel_formatters import (
    fmt_datetime_local, fmt_breaks_text, fmt_employees_text, fmt_additional_times_text,
    fmt_production_orders_text, fmt_references_text, fmt_sam_text,
)

DICTIONARY_SHEET = "Descripción de columnas"
RECORDS_SHEET = "Detalle registros"

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
    out["sam"] = fmt_sam_text(out.get("references"))  # before references becomes text
    if out.get("additional_time_seconds") is not None:
        out["additional_minutes"] = float(out["additional_time_seconds"]) / 60
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


def _style_header(ws, labels, row=1):
    for col_idx, label in enumerate(labels, start=1):
        cell = ws.cell(row=row, column=col_idx, value=label)
        cell.font      = _HEADER_FONT
        cell.fill      = _HEADER_FILL
        cell.alignment = _CENTER
        cell.border    = _CELL_BORDER


def _build_dictionary_sheet(dic, entries):
    """First sheet: SIGPRO banner (row 1), table header (row 2), one row per (label, description)."""
    dic.title = DICTIONARY_SHEET
    dic.merge_cells("A1:B1")
    banner = dic["A1"]
    banner.value     = "SIGPRO"
    banner.font      = Font(name="Calibri", size=24, bold=True, color="FFFFFF")
    banner.fill      = _HEADER_FILL
    banner.alignment = _CENTER
    dic.row_dimensions[1].height = 42
    dic.freeze_panes = "A3"
    _style_header(dic, ["Nombre", "Descripción"], row=2)
    for row_idx, (label, desc) in enumerate(entries, start=3):
        for col_idx, value in enumerate((label, desc), start=1):
            cell = dic.cell(row=row_idx, column=col_idx, value=value)
            cell.font, cell.border, cell.alignment = _CELL_FONT, _CELL_BORDER, _WRAP
    dic.column_dimensions["A"].width = 30
    dic.column_dimensions["B"].width = 100
    dic.oddHeader.center.text = "SIGPRO"
    dic.oddHeader.center.size = 16
    dic.oddHeader.center.font = "Calibri,Bold"


def _fmt_record_schedule(value) -> str:
    """'HH:MM:SS-HH:MM:SS' from SQL -> 'HH:MM-HH:MM', like the shift times of Eficiencia."""
    return "-".join(part[:5] for part in str(value).split("-")) if value else ""


def _record_value(field: str, value):
    if field in RECORD_UTC_FIELDS:
        return fmt_datetime_local(value)
    if field == "horario":
        return _fmt_record_schedule(value)
    return _fmt(field, value)


def _prepare_records(rows: list[dict]):
    """(fields, values) of the third sheet: present columns in catalog order, display-ready values."""
    keys = []
    for row in rows:
        for key in row:
            if key not in keys and key not in RECORD_EXCLUDED_FIELDS:
                keys.append(key)
    ordered = [k for k, *_ in RECORD_COLUMNS if k in keys] + [k for k in keys if k not in RECORD_LABELS]
    values = [{k: _record_value(k, r.get(k)) for k in ordered} for r in rows]
    fields = [k for k in ordered if any(v[k] != "" for v in values)]
    return fields, values


def _build_records_sheet(wb, fields: list[str], values: list[dict]):
    """Third sheet: one row per record straight from dbo.fn_reporte_registros."""
    ws = wb.create_sheet(RECORDS_SHEET)
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 22
    labels = [RECORD_LABELS.get(f, f) for f in fields]
    _style_header(ws, labels)
    for row_idx, record in enumerate(values, start=2):
        for col_idx, field in enumerate(fields, start=1):
            value = record[field]
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font      = _CELL_FONT
            cell.border    = _CELL_BORDER
            cell.alignment = _CENTER if isinstance(value, (int, float)) else _LEFT
            if isinstance(value, float):
                cell.number_format = "General"  # shows every available decimal
    for col_idx, label in enumerate(labels, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = max(len(label) + 4, 14)


def build_efficiency_report_excel(data: list[dict], has_employee: bool = False, records: list[dict] | None = None) -> bytes:
    # has_employee is kept for the caller's signature: employee_* columns are
    # NULL (hence dropped) unless the report was filtered by an employee.
    efficiency_rows = [_preprocess(r) for r in data]
    fields = _present_columns(efficiency_rows)
    labels = {f: CATALOG.get(f, (f, UNKNOWN_COLUMN_DESCRIPTION))[0] for f in fields}

    record_fields, record_values = _prepare_records(records or [])

    # Eficiencia columns first, then the Detalle-only ones; a shared name is listed once.
    entries = {labels[f]: CATALOG.get(f, (f, UNKNOWN_COLUMN_DESCRIPTION))[1] for f in fields}
    for f in record_fields:
        entries.setdefault(RECORD_LABELS.get(f, f), RECORD_DESCRIPTIONS.get(f, UNKNOWN_COLUMN_DESCRIPTION))

    wb = Workbook()
    _build_dictionary_sheet(wb.active, list(entries.items()))

    ws = wb.create_sheet("Eficiencia")
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 22

    # ── Headers ──────────────────────────────────────────────────────────────
    _style_header(ws, [labels[f] for f in fields])

    # ── Rows ─────────────────────────────────────────────────────────────────
    for row_idx, record in enumerate(efficiency_rows, start=2):
        for col_idx, field in enumerate(fields, start=1):
            value = _fmt(field, record.get(field))
            cell  = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font      = _CELL_FONT
            cell.border    = _CELL_BORDER
            cell.alignment = _CENTER if isinstance(value, (int, float)) else _LEFT
            if isinstance(value, float):
                cell.number_format = "General"  # shows every available decimal

    # ── Column widths ────────────────────────────────────────────────────────
    for col_idx, field in enumerate(fields, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = max(len(labels[field]) + 4, 14)

    _build_records_sheet(wb, record_fields, record_values)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
