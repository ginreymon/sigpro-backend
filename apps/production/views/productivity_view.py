from datetime import datetime, timedelta
from io import BytesIO

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils.dateparse import parse_datetime

from apps.production.services.productivity_service import ProductivityService
from apps.production.reports.productivity_columns import SUMMARY_COLUMNS, EMPLOYEE_COLUMNS
from apps.production.helpers.productivity_metrics import enrich_rows

_SECONDS_FIELDS = {
    "shift_total_seconds",
    "total_productive_seconds",
    "total_break_seconds",
    "total_activity_seconds",
    "elapsed_shift_seconds",
}


def _secs_to_mins(data: list[dict]) -> list[dict]:
    return [
        {k: (round(v / 60, 2) if k in _SECONDS_FIELDS and v is not None else v) for k, v in row.items()}
        for row in data
    ]


_DATETIME_FIELDS = {"first_record_start", "last_record_end"}


def _localize_datetimes(data: list[dict], utc_offset_minutes: int) -> list[dict]:
    delta = timedelta(minutes=utc_offset_minutes)
    result = []
    for row in data:
        row = dict(row)
        for field in _DATETIME_FIELDS:
            val = row.get(field)
            if val is not None and isinstance(val, datetime):
                row[field] = val + delta
        result.append(row)
    return result


def _parse_required_dates(params):
    start_str = params.get("start_date")
    end_str = params.get("end_date")
    client_now_str = params.get("client_now")

    if not start_str or not end_str or not client_now_str:
        return None, None, None, "start_date, end_date and client_now are required"

    try:
        start_date = datetime.fromisoformat(start_str)
        end_date = datetime.fromisoformat(end_str)
    except ValueError:
        return None, None, None, "start_date and end_date must be ISO 8601 format (e.g. 2025-12-20T06:00:00)"

    client_now = parse_datetime(client_now_str)
    if client_now is None or client_now.tzinfo is None:
        return None, None, None, "client_now must be a timezone-aware ISO 8601 datetime (e.g. 2025-12-20T11:00:00Z)"

    return start_date, end_date, client_now, None


def _parse_optional_int(params, key):
    val = params.get(key)
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _build_excel(data: list[dict], columns: list[tuple], sheet_title: str) -> BytesIO:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(fill_type="solid", fgColor="1E3A5F")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for col_idx, (_, label) in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=col_idx, value=label)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align

    for row_idx, row in enumerate(data, start=2):
        for col_idx, (key, _) in enumerate(columns, start=1):
            val = row.get(key)
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            if isinstance(val, datetime):
                cell.number_format = "DD/MM/YYYY HH:MM:SS"

    for col_idx in range(1, len(columns) + 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].auto_size = True

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def _excel_response(buf: BytesIO, filename: str) -> HttpResponse:
    return HttpResponse(
        buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class ProductivityViewSet(viewsets.ViewSet):

    #  GET /productivity/summary/
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        start_date, end_date, client_now, error = _parse_required_dates(request.query_params)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        employee_id = _parse_optional_int(request.query_params, "employee_id")
        module_id   = _parse_optional_int(request.query_params, "module_id")
        shift_id    = _parse_optional_int(request.query_params, "shift_id")

        data = ProductivityService.get_base_productivity(
            start_date, end_date, client_now,
            employee_id=employee_id,
            module_id=module_id,
            shift_id=shift_id,
        )
        return Response(data, status=status.HTTP_200_OK)

    # GET /productivity/summary/export/excel
    @action(detail=False, methods=["get"], url_path="summary/export/excel")
    def summary_excel(self, request):
        start_date, end_date, client_now, error = _parse_required_dates(request.query_params)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        employee_id = _parse_optional_int(request.query_params, "employee_id")
        module_id   = _parse_optional_int(request.query_params, "module_id")
        shift_id    = _parse_optional_int(request.query_params, "shift_id")

        data = ProductivityService.get_base_productivity(
            start_date, end_date, client_now,
            employee_id=employee_id,
            module_id=module_id,
            shift_id=shift_id,
        )
        data = enrich_rows(data)
        COLUMNS = EMPLOYEE_COLUMNS if employee_id else SUMMARY_COLUMNS
        utc_offset_minutes = _parse_optional_int(request.query_params, "utc_offset_minutes") or 0
        buf = _build_excel(_secs_to_mins(_localize_datetimes(data, utc_offset_minutes)), COLUMNS, "Productividad")
        return _excel_response(buf, f"productividad_resumen_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.xlsx")
    
    @action(detail=False, methods=["get"], url_path="efficiency")
    def efficiency(self, request):
        start_date, end_date, client_now, error = _parse_required_dates(request.query_params)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        employee_id = _parse_optional_int(request.query_params, "employee_id")
        module_id   = _parse_optional_int(request.query_params, "module_id")
        shift_id    = _parse_optional_int(request.query_params, "shift_id")

        data = ProductivityService.get_efficiency_period(
            start_date, end_date, client_now,
            employee_id=employee_id,
            module_id=module_id,
            shift_id=shift_id,
        )
        return Response(data, status=status.HTTP_200_OK)
