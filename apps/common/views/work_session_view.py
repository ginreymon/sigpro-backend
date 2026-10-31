from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.services.work_session_service import WorkSessionService

# Same cap as the stored procedure (@Limit is clamped to 1..100).
MAX_PAGE_SIZE = 100


class WorkSessionView(APIView):
    """GET /api/v1/dashboard/work-sessions/

    Optional filters: `start`, `end` (YYYY-MM-DD, inclusive, local date), `op_number`,
    `op_type`, `reference` (contains), `module_name` (contains). Pagination is done
    in the database: `limit` / `offset`, same response contract as LimitOffsetPagination.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        params = request.query_params
        start = self._date_param(params, "start")
        end = self._date_param(params, "end")
        if start and end and end < start:
            raise ValidationError({"end": "end no puede ser menor que start."})

        op_number = params.get("op_number")
        if op_number and not op_number.isdigit():
            raise ValidationError({"op_number": "op_number debe ser un numero entero."})

        paginator = LimitOffsetPagination()
        limit = min(paginator.get_limit(request), MAX_PAGE_SIZE)
        offset = paginator.get_offset(request)

        count, rows = WorkSessionService.list_work_sessions(
            start_date=start.isoformat() if start else None,
            end_date=end.isoformat() if end else None,
            op_number=int(op_number) if op_number else None,
            op_type=(params.get("op_type") or "").strip() or None,
            reference=(params.get("reference") or "").strip() or None,
            module_name=(params.get("module_name") or "").strip() or None,
            offset=offset,
            limit=limit,
        )

        # The SP already returned only this page: fill the paginator state by hand.
        paginator.count, paginator.limit, paginator.offset, paginator.request = (
            count,
            limit,
            offset,
            request,
        )
        return paginator.get_paginated_response(rows)

    @staticmethod
    def _date_param(params, name):
        value = params.get(name)
        if not value:
            return None
        parsed = parse_date(value)
        if parsed is None:
            raise ValidationError({name: f"{name} debe tener formato YYYY-MM-DD."})
        return parsed
