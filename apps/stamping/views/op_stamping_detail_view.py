from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from apps.stamping.services.op_stamping_service import OPStampingService


class OPStampingDetailViewSet(viewsets.ViewSet):

    @action(detail=False, methods=["get"], url_path="detail")
    def get_detail(self, request):
        doc_type = request.query_params.get("type")
        doc_number = request.query_params.get("number")

        if not doc_type or not doc_number:
            return Response(
                {"error": "type and number are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = OPStampingService.get_detalle_estampacion_op_json(doc_type, int(doc_number))

        if not data:
            return Response(
                {"error": "No data found"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="traceability")
    def traceability(self, request):
        doc_number = request.query_params.get("number")
        doc_type = request.query_params.get("type")

        if not doc_number:
            return Response(
                {"error": "number is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = OPStampingService.get_trazabilidad_op_json(int(doc_number), doc_type)

        if not data:
            return Response(
                {"error": "No data found"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_200_OK)
