from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.integration.serializers import OrderToBeOutboundSerializer
from apps.integration.services.op_totals_service import OPTotalsService

SEARCH_FIELDS = ("op_number", "op_type", "origin")


class OrdersToBeOutboundViewSet(viewsets.GenericViewSet):
    """Solo lectura: totales registrados por OP (sp_totales_registrados_por_op),
    pendientes de revision/aprobacion antes de salir hacia SIESA.

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

        data = OPTotalsService.get_totales_registrados_por_op(
            int(op_rowid) if op_rowid else None
        )

        if search:
            search = search.lower()
            data = [
                row for row in data
                if any(search in str(row.get(field) or "").lower() for field in SEARCH_FIELDS)
            ]

        page = self.paginate_queryset(data)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
