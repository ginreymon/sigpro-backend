from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.views.productivity_params import parse_required_dates, parse_optional_int
from core.exceptions import error_response


class BaseProductivityViewSet(viewsets.ViewSet):
    """
    Productivity endpoints shared by production and stamping. Subclasses set
    `service` (a BaseProductivityService subclass).
    """

    service = None

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
