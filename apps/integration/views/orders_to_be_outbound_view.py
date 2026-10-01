from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.integration.serializers import OrderToBeOutboundSerializer
from apps.integration.services.op_totals_service import OPTotalsService

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
