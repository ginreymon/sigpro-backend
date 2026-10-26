from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse

from apps.common.views.productivity_params import parse_optional_int
from core.exceptions import error_response
from apps.common.views.productivity_view import BaseProductivityViewSet
from apps.production.services.productivity_service import ProductivityService
from apps.production.exports.efficiency_report_export import build_efficiency_report_excel


class ProductivityViewSet(BaseProductivityViewSet):
    service = ProductivityService

    # GET /productivity/efficiency-report/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD[&module_id=N&shift_id=N&employee_id=N]
    @action(detail=False, methods=["get"], url_path="efficiency-report")
    def efficiency_report(self, request):
        start_date = request.query_params.get("start_date")
        end_date   = request.query_params.get("end_date")

        if not start_date or not end_date:
            return error_response(
                "start_date and end_date are required", code="missing_params",
                legacy={"error": "start_date and end_date are required"},
            )

        module_id       = parse_optional_int(request.query_params, "module_id")
        shift_id        = parse_optional_int(request.query_params, "shift_id")
        employee_id     = parse_optional_int(request.query_params, "employee_id")
        core_module_id  = parse_optional_int(request.query_params, "core_module_id")

        data = ProductivityService.get_efficiency_report(
            start_date, end_date,
            module_id=module_id,
            shift_id=shift_id,
            employee_id=employee_id,
            core_module_id=core_module_id,
        )
        return Response(data, status=status.HTTP_200_OK)

    # GET /productivity/efficiency-report/export/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD[&module_id=N&shift_id=N&employee_id=N&core_module_id=N]
    @action(detail=False, methods=["get"], url_path="efficiency-report/export")
    def efficiency_report_export(self, request):
        start_date = request.query_params.get("start_date")
        end_date   = request.query_params.get("end_date")

        if not start_date or not end_date:
            return error_response(
                "start_date and end_date are required", code="missing_params",
                legacy={"error": "start_date and end_date are required"},
            )

        module_id       = parse_optional_int(request.query_params, "module_id")
        shift_id        = parse_optional_int(request.query_params, "shift_id")
        employee_id     = parse_optional_int(request.query_params, "employee_id")
        core_module_id  = parse_optional_int(request.query_params, "core_module_id")

        data = ProductivityService.get_efficiency_report(
            start_date, end_date,
            module_id=module_id,
            shift_id=shift_id,
            employee_id=employee_id,
            core_module_id=core_module_id,
        )

        xlsx = build_efficiency_report_excel(data, has_employee=employee_id is not None)
        filename = f"eficiencia_{start_date}_{end_date}.xlsx"

        response = HttpResponse(
            xlsx,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

