from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from apps.stamping.services.op_stamping_service import OPStampingService


class ProductionOrderProcessesViewSet(viewsets.ViewSet):

    @action(detail=False, methods=["get"], url_path="processes")
    def processes(self, request):
        doc_type = request.query_params.get("type")
        doc_number = request.query_params.get("number")
        id_plan = request.query_params.get("id_plan", "300")

        if not doc_type or not doc_number:
            return Response(
                {"error": "type and number are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = OPStampingService.get_ordenes_produccion_proceso_json(doc_type, int(doc_number), id_plan)

        if not data:
            return Response(
                {"error": "No data found"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_200_OK)
