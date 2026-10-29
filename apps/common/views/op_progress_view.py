from datetime import date

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.services.op_progress_service import OpProgressService
from core.exceptions import error_response


def _parse_iso_date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


class OpProgressView(APIView):
    """GET /api/v1/dashboard/op-progress/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD[&area_id=N]"""

    def get(self, request):
        params = request.query_params
        start_str = params.get("start_date")
        end_str = params.get("end_date")

        if not start_str or not end_str:
            msg = "start_date and end_date are required"
            return error_response(msg, code="missing_params", legacy={"error": msg})

        start = _parse_iso_date(start_str)
        end = _parse_iso_date(end_str)
        if start is None or end is None:
            msg = "start_date and end_date must be in YYYY-MM-DD format"
            return error_response(msg, code="invalid_params", legacy={"error": msg})
        if start > end:
            msg = "start_date must be less than or equal to end_date"
            return error_response(msg, code="invalid_params", legacy={"error": msg})

        area_id = None
        area_str = params.get("area_id")
        if area_str not in (None, ""):
            try:
                area_id = int(area_str)
            except ValueError:
                msg = "area_id must be an integer"
                return error_response(msg, code="invalid_params", legacy={"error": msg})

        data = OpProgressService.get_op_progress(start_str, end_str, area_id)
        return Response(data, status=status.HTTP_200_OK)
