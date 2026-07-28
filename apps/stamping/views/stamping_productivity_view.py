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
