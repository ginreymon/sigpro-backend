from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.http import build_export_filename
from apps.common.views.productivity_params import parse_required_dates, parse_optional_int
from core.exceptions import error_response


class BaseProductivityViewSet(viewsets.ViewSet):
    """
    Productivity endpoints shared by production and stamping. Subclasses set
    `service` (a BaseProductivityService subclass).
    """

    service = None
    # Callable (data, has_employee) -> xlsx bytes; set by each area's subclass.
    efficiency_report_export_builder = None

    # GET .../productivity/efficiency/
    @action(detail=False, methods=["get"], url_path="efficiency")
    def efficiency(self, request):
        start_date, end_date, client_now, error = parse_required_dates(request.query_params)
        if error:
            return error_response(error, code="invalid_params", legacy={"error": error})

        module_id = parse_optional_int(request.query_params, "module_id")
        shift_id  = parse_optional_int(request.query_params, "shift_id")

        data = self.service.get_efficiency_period(
            start_date, end_date, client_now,
            module_id=module_id,
            shift_id=shift_id,
        )
        return Response(data, status=status.HTTP_200_OK)

    # GET .../productivity/shift-summary/
    @action(detail=False, methods=["get"], url_path="shift-summary")
    def shift_summary(self, request):
        start_date, end_date, client_now, error = parse_required_dates(request.query_params)
        if error:
            return error_response(error, code="invalid_params", legacy={"error": error})

        shift_id  = parse_optional_int(request.query_params, "shift_id")
        module_id = parse_optional_int(request.query_params, "module_id")

        if shift_id is None or module_id is None:
            return error_response(
                "shift_id and module_id are required", code="missing_params",
                legacy={"error": "shift_id and module_id are required"},
            )

        employee_id = parse_optional_int(request.query_params, "employee_id")

        data = self.service.get_shift_summary(
            start_date, end_date, client_now,
            shift_id=shift_id,
            module_id=module_id,
            employee_id=employee_id,
        )
        return Response(data, status=status.HTTP_200_OK)

    # GET .../productivity/balance-summary/
    @action(detail=False, methods=["get"], url_path="balance-summary")
    def balance_summary(self, request):
        start_date, end_date, client_now, error = parse_required_dates(request.query_params)
        if error:
            return error_response(error, code="invalid_params", legacy={"error": error})

        module_id = parse_optional_int(request.query_params, "module_id")

        data = self.service.get_balance_summary(
            start_date, end_date, client_now, module_id=module_id
        )
        return Response(data, status=status.HTTP_200_OK)

    # GET .../productivity/module-shift-summary/[?core_module_id=N]
    @action(detail=False, methods=["get"], url_path="module-shift-summary")
    def module_shift_summary(self, request):
        core_module_id = parse_optional_int(request.query_params, "core_module_id")
        data = self.service.get_module_shift_summary(core_module_id)
        return Response(data, status=status.HTTP_200_OK)

    # GET .../productivity/module-efficiency/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD[&module_id=N]
    @action(detail=False, methods=["get"], url_path="module-efficiency")
    def module_efficiency(self, request):
        start_date = request.query_params.get("start_date")
        end_date   = request.query_params.get("end_date")

        if not start_date or not end_date:
            return error_response(
                "start_date and end_date are required", code="missing_params",
                legacy={"error": "start_date and end_date are required"},
            )

        module_id = parse_optional_int(request.query_params, "module_id")

        data = self.service.get_module_efficiency(start_date, end_date, module_id)
        return Response(data, status=status.HTTP_200_OK)

    @staticmethod
    def _parse_efficiency_report_params(request):
        start_date = request.query_params.get("start_date")
        end_date   = request.query_params.get("end_date")
        if not start_date or not end_date:
            return None, error_response(
                "start_date and end_date are required", code="missing_params",
                legacy={"error": "start_date and end_date are required"},
            )
        filters = {
            "module_id":      parse_optional_int(request.query_params, "module_id"),
            "shift_id":       parse_optional_int(request.query_params, "shift_id"),
            "employee_id":    parse_optional_int(request.query_params, "employee_id"),
            "core_module_id": parse_optional_int(request.query_params, "core_module_id"),
        }
        return (start_date, end_date, filters), None

    # GET .../productivity/efficiency-report/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD[&module_id=N&shift_id=N&employee_id=N&core_module_id=N]
    @action(detail=False, methods=["get"], url_path="efficiency-report")
    def efficiency_report(self, request):
        parsed, error = self._parse_efficiency_report_params(request)
        if error:
            return error
        start_date, end_date, filters = parsed

        data = self.service.get_efficiency_report(start_date, end_date, **filters)
        return Response(data, status=status.HTTP_200_OK)

    # GET .../productivity/efficiency-report/export/ (same params; returns the .xlsx)
    @action(detail=False, methods=["get"], url_path="efficiency-report/export")
    def efficiency_report_export(self, request):
        parsed, error = self._parse_efficiency_report_params(request)
        if error:
            return error
        start_date, end_date, filters = parsed

        data = self.service.get_efficiency_report(start_date, end_date, **filters)
        records = self.service.get_records_report(start_date, end_date, **filters)
        xlsx = self.efficiency_report_export_builder(
            data, has_employee=filters["employee_id"] is not None, records=records,
        )

        response = HttpResponse(
            xlsx,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        area_name = self.service.get_area_name(filters["core_module_id"])
        filename = build_export_filename(area_name, start_date, end_date, fallback="eficiencia")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
