from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.production.views.productivity_view import _parse_required_dates, _parse_optional_int
from apps.stamping.services.stamping_productivity_service import StampingProductivityService


class StampingProductivityViewSet(viewsets.ViewSet):

    # GET /stamping/productivity/efficiency/
    @action(detail=False, methods=["get"], url_path="efficiency")
    def efficiency(self, request):
        start_date, end_date, client_now, error = _parse_required_dates(request.query_params)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        module_id = _parse_optional_int(request.query_params, "module_id")
        shift_id  = _parse_optional_int(request.query_params, "shift_id")

        data = StampingProductivityService.get_efficiency_period(
            start_date, end_date, client_now,
            module_id=module_id,
            shift_id=shift_id,
        )
        return Response(data, status=status.HTTP_200_OK)

    # GET /stamping/productivity/module-shift-summary/[?core_module_id=N]
    @action(detail=False, methods=["get"], url_path="module-shift-summary")
    def module_shift_summary(self, request):
        core_module_id = _parse_optional_int(request.query_params, "core_module_id")
        data = StampingProductivityService.get_module_shift_summary(core_module_id)
        return Response(data, status=status.HTTP_200_OK)

    # GET /stamping/productivity/module-efficiency/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD[&module_id=N]
    @action(detail=False, methods=["get"], url_path="module-efficiency")
    def module_efficiency(self, request):
        start_date = request.query_params.get("start_date")
        end_date   = request.query_params.get("end_date")

        if not start_date or not end_date:
            return Response({"error": "start_date and end_date are required"}, status=status.HTTP_400_BAD_REQUEST)

        module_id = _parse_optional_int(request.query_params, "module_id")

        data = StampingProductivityService.get_module_efficiency(start_date, end_date, module_id)
        return Response(data, status=status.HTTP_200_OK)
