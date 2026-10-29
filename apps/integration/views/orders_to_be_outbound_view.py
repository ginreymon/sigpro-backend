from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.integration.serializers import (
    OrderByWorkCenterSerializer,
    OrderIntegrationStatusSerializer,
    OrderIntegrationSummarySerializer,
    OrderToBeOutboundSerializer,
)
from apps.integration.services.op_totals_service import INTEGRATION_STATUSES, OPTotalsService

SEARCH_FIELDS = ("origin", "code")
DETAIL_SEARCH_FIELDS = ("op_number", "op_type")
# Mismo tope que sp_totales_registrados_por_op_json (31 dias, ambos inclusive):
# cada dia ejecuta fn_trazabilidad_op, costosa.
MAX_RANGE_DAYS = 31


class OrdersToBeOutboundViewSet(viewsets.GenericViewSet):
    """Solo lectura: totales registrados por OP (sp_totales_registrados_por_op_json),
    pendientes de revision/aprobacion antes de salir hacia SIESA. Sin
    `date_from` trae todo; con `date_from`/`date_to` (AAAA-MM-DD) filtra por dia.

    Paginacion/busqueda se resuelven en memoria (no en el SP, que no tiene
    limit/offset): el set esperado (OPs pendientes) es acotado. Usa
    pagination_class por defecto del proyecto (LimitOffsetPagination) para
    que el frontend reutilice el mismo contrato PaginatedResponse que ya
    consume BaseCrudService."""

    permission_classes = [IsAuthenticated]
    serializer_class = OrderToBeOutboundSerializer

    def list(self, request):
        op_rowid = request.query_params.get("op_rowid")
        search = request.query_params.get("search")

        date_from = parse_date(request.query_params.get("date_from") or "")
        date_to = parse_date(request.query_params.get("date_to") or "")

        self._validate_date_range(date_from, date_to)

        data = OPTotalsService.get_totales_registrados_por_op(
            date_from,
            date_to,
            int(op_rowid) if op_rowid else None,
        )

        if search:
            search = search.lower()
            data = [row for row in data if self._matches(row, search)]

        page = self.paginate_queryset(data)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"], url_path="by-work-center",
            serializer_class=OrderByWorkCenterSerializer)
    def by_work_center(self, request):
        """Totals per work center without day split
        (sp_totales_registrados_por_op_work_center_json). Optional `op_rowid`,
        `first_start_from` and `last_end_to` (ISO datetimes, UTC)."""
        op_rowid, first_start_from, last_end_to = self._parse_period_filters(request)

        data = OPTotalsService.get_totales_por_work_center(
            op_rowid, first_start_from, last_end_to
        )

        page = self.paginate_queryset(data)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"], url_path="op-sku-detail")
    def op_sku_detail(self, request):
        """Color x size matrix of one Confección OP (sp_detalle_integracion_op_produccion),
        whatever the TEP state of its SKUs, so a sent submission can show what it integrated.
        Required `op_type` and `op_number`; `colorRows` is empty when the OP does not exist."""
        op_type = (request.query_params.get("op_type") or "").strip()
        op_number = request.query_params.get("op_number")

        errors = {}
        if not op_type:
            errors["op_type"] = "op_type es obligatorio."
        if not op_number or not op_number.isdigit():
            errors["op_number"] = "op_number debe ser un numero entero."
        if errors:
            raise ValidationError(errors)

        return Response(OPTotalsService.get_detalle_sku_op(op_type, int(op_number)))

    @action(detail=False, methods=["get"], url_path="integration-status",
            serializer_class=OrderIntegrationStatusSerializer)
    def integration_status(self, request):
        """Integrated / pending / missing quantities per OP and work center
        (dbo.fn_estado_integracion_op), including OPs already integrated. Optional
        `status` (PENDING, MISSING or INTEGRATED), `op_rowid`, `first_start_from`
        and `last_end_to` (ISO datetimes, UTC). The period is required (max
        MAX_RANGE_DAYS): the function resolves fn_trazabilidad_op per OP and now
        also sees the integrated history."""
        op_rowid, first_start_from, last_end_to = self._parse_bounded_period_filters(request)

        status = (request.query_params.get("status") or "").upper() or None
        if status and status not in INTEGRATION_STATUSES:
            raise ValidationError(
                {"status": f"status debe ser uno de: {', '.join(INTEGRATION_STATUSES)}."}
            )

        data = OPTotalsService.get_estado_integracion(
            op_rowid, first_start_from, last_end_to, status
        )

        page = self.paginate_queryset(data)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"], url_path="integration-summary",
            serializer_class=OrderIntegrationSummarySerializer)
    def integration_summary(self, request):
        """Counters of integration-status (rows and quantities per status), same
        filters (and the same required period) except `status`."""
        op_rowid, first_start_from, last_end_to = self._parse_bounded_period_filters(request)

        data = OPTotalsService.get_resumen_integracion(op_rowid, first_start_from, last_end_to)
        return Response(self.get_serializer(data).data)

    @staticmethod
    def _parse_period_filters(request):
        """`op_rowid`, `first_start_from` and `last_end_to` of the work-center
        endpoints; 400 when the range is inverted."""
        op_rowid = request.query_params.get("op_rowid")
        if op_rowid and not op_rowid.isdigit():
            raise ValidationError({"op_rowid": "op_rowid debe ser un numero entero."})

        first_start_from = parse_datetime(request.query_params.get("first_start_from") or "")
        last_end_to = parse_datetime(request.query_params.get("last_end_to") or "")

        if first_start_from and last_end_to:
            # Comparing a naive datetime with an aware one raises TypeError (500).
            if (first_start_from.tzinfo is None) != (last_end_to.tzinfo is None):
                raise ValidationError(
                    {"last_end_to": "first_start_from y last_end_to deben usar el mismo formato de zona horaria."}
                )
            if last_end_to < first_start_from:
                raise ValidationError(
                    {"last_end_to": "last_end_to no puede ser menor que first_start_from."}
                )

        return int(op_rowid) if op_rowid else None, first_start_from, last_end_to

    @classmethod
    def _parse_bounded_period_filters(cls, request):
        """Same as _parse_period_filters, but `first_start_from` and `last_end_to`
        are required and the range cannot exceed MAX_RANGE_DAYS."""
        op_rowid, first_start_from, last_end_to = cls._parse_period_filters(request)

        missing = {
            name: f"{name} es obligatorio."
            for name, value in (("first_start_from", first_start_from), ("last_end_to", last_end_to))
            if value is None
        }
        if missing:
            raise ValidationError(missing)

        if (last_end_to - first_start_from).days + 1 > MAX_RANGE_DAYS:
            raise ValidationError(
                {"last_end_to": f"El rango maximo es de {MAX_RANGE_DAYS} dias."}
            )

        return op_rowid, first_start_from, last_end_to

    @staticmethod
    def _validate_date_range(date_from, date_to):
        """El SP lanza error (-> 500) si el rango es invalido; se responde 400."""
        if date_from is None or date_to is None:
            return
        if date_to < date_from:
            raise ValidationError({"date_to": "date_to no puede ser menor que date_from."})
        if (date_to - date_from).days + 1 > MAX_RANGE_DAYS:
            raise ValidationError(
                {"date_to": f"El rango maximo es de {MAX_RANGE_DAYS} dias."}
            )

    @staticmethod
    def _matches(row, search):
        """`search` (en minusculas) contra el grupo (origin, code) o contra
        cualquier entrada de su detail (op_number, op_type)."""
        return any(search in str(row.get(field) or "").lower() for field in SEARCH_FIELDS) or any(
            search in str(item.get(field) or "").lower()
            for item in row["detail"]
            for field in DETAIL_SEARCH_FIELDS
        )
