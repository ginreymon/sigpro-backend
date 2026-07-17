from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils.dateparse import parse_datetime

from apps.production.services.productivity_service import ProductivityService
from apps.production.exports.efficiency_report_export import build_efficiency_report_excel
from core.utils.date_utils import parse_to_utc_naive


def _parse_required_dates(params):
    start_str      = params.get("start_date")
    end_str        = params.get("end_date")
    client_now_str = params.get("client_now")

    if not start_str or not end_str or not client_now_str:
        return None, None, None, "start_date, end_date and client_now are required"

    start_date = parse_to_utc_naive(start_str)
    end_date   = parse_to_utc_naive(end_str)

    if start_date is None or end_date is None:
        return None, None, None, "start_date and end_date must be ISO 8601 with timezone (e.g. 2026-05-27T05:00:00Z)"

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


class ProductivityViewSet(viewsets.ViewSet):

    # GET /productivity/shift-summary/
    @action(detail=False, methods=["get"], url_path="shift-summary")
    def shift_summary(self, request):
        start_date, end_date, client_now, error = _parse_required_dates(request.query_params)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        shift_id  = _parse_optional_int(request.query_params, "shift_id")
        module_id = _parse_optional_int(request.query_params, "module_id")

        if shift_id is None or module_id is None:
            return Response({"error": "shift_id and module_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        employee_id = _parse_optional_int(request.query_params, "employee_id")

        data = ProductivityService.get_shift_summary(
            start_date, end_date, client_now,
            shift_id=shift_id,
            module_id=module_id,
            employee_id=employee_id,
        )
        return Response(data, status=status.HTTP_200_OK)

    # GET /productivity/balance-summary/
    @action(detail=False, methods=["get"], url_path="balance-summary")
    def balance_summary(self, request):
        start_date, end_date, client_now, error = _parse_required_dates(request.query_params)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        module_id = _parse_optional_int(request.query_params, "module_id")

        data = ProductivityService.get_balance_summary(
            start_date, end_date, client_now, module_id=module_id
        )
        return Response(data, status=status.HTTP_200_OK)

    # GET /productivity/module-shift-summary/[?core_module_id=N]
    @action(detail=False, methods=["get"], url_path="module-shift-summary")
    def module_shift_summary(self, request):
        core_module_id = _parse_optional_int(request.query_params, "core_module_id")
        data = ProductivityService.get_module_shift_summary(core_module_id)
        return Response(data, status=status.HTTP_200_OK)

    # GET /productivity/module-efficiency/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD[&module_id=N]
    @action(detail=False, methods=["get"], url_path="module-efficiency")
    def module_efficiency(self, request):
        start_date = request.query_params.get("start_date")
        end_date   = request.query_params.get("end_date")

        if not start_date or not end_date:
            return Response({"error": "start_date and end_date are required"}, status=status.HTTP_400_BAD_REQUEST)

        module_id = _parse_optional_int(request.query_params, "module_id")

        data = ProductivityService.get_module_efficiency(start_date, end_date, module_id)
        return Response(data, status=status.HTTP_200_OK)

    # GET /productivity/efficiency-report/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD[&module_id=N&shift_id=N&employee_id=N]
    @action(detail=False, methods=["get"], url_path="efficiency-report")
    def efficiency_report(self, request):
        start_date = request.query_params.get("start_date")
        end_date   = request.query_params.get("end_date")

        if not start_date or not end_date:
            return Response({"error": "start_date and end_date are required"}, status=status.HTTP_400_BAD_REQUEST)

        module_id   = _parse_optional_int(request.query_params, "module_id")
        shift_id    = _parse_optional_int(request.query_params, "shift_id")
        employee_id = _parse_optional_int(request.query_params, "employee_id")

        data = ProductivityService.get_efficiency_report(
            start_date, end_date,
            module_id=module_id,
            shift_id=shift_id,
            employee_id=employee_id,
        )
        return Response(data, status=status.HTTP_200_OK)

    # GET /productivity/efficiency-report/export/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD[&module_id=N&shift_id=N&employee_id=N]
    @action(detail=False, methods=["get"], url_path="efficiency-report/export")
    def efficiency_report_export(self, request):
        start_date = request.query_params.get("start_date")
        end_date   = request.query_params.get("end_date")

        if not start_date or not end_date:
            return Response({"error": "start_date and end_date are required"}, status=status.HTTP_400_BAD_REQUEST)

        module_id   = _parse_optional_int(request.query_params, "module_id")
        shift_id    = _parse_optional_int(request.query_params, "shift_id")
        employee_id = _parse_optional_int(request.query_params, "employee_id")

        data = ProductivityService.get_efficiency_report(
            start_date, end_date,
            module_id=module_id,
            shift_id=shift_id,
            employee_id=employee_id,
        )

        xlsx = build_efficiency_report_excel(data, has_employee=employee_id is not None)
        filename = f"eficiencia_{start_date}_{end_date}.xlsx"

        response = HttpResponse(
            xlsx,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    # GET /productivity/efficiency/
    @action(detail=False, methods=["get"], url_path="efficiency")
    def efficiency(self, request):
        start_date, end_date, client_now, error = _parse_required_dates(request.query_params)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        module_id = _parse_optional_int(request.query_params, "module_id")
        shift_id  = _parse_optional_int(request.query_params, "shift_id")

        data = ProductivityService.get_efficiency_period(
            start_date, end_date, client_now,
            module_id=module_id,
            shift_id=shift_id,
        )
        return Response(data, status=status.HTTP_200_OK)
