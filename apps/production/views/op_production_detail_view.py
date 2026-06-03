from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from apps.production.serializers import OPProductionDetailSerializer
from apps.production.services.op_production_service import OPProductionService


class OPProductionDetailViewSet(viewsets.ViewSet):

    serializer_class = OPProductionDetailSerializer

    def list(self, request):
        doc_type = request.query_params.get("type")
        doc_number = request.query_params.get("number")        

        if not doc_type or not doc_number:
            return Response(
                {"error": "type and number are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = OPProductionService.get_detalle_produccion_op(doc_type, int(doc_number))

        serializer = OPProductionDetailSerializer(data, many=True)       

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="flat")
    def json_format(self, request):
        doc_type = request.query_params.get("type")
        doc_number = request.query_params.get("number")
        id_plan = request.query_params.get("id_plan", 300)

        if not doc_type or not doc_number:
            return Response(
                {"error": "type and number are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = OPProductionService.get_detalle_produccion_op_json(
            doc_type, int(doc_number), int(id_plan)
        )

        if not data:
            return Response(
                {"error": "No data found"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="sku-detail")
    def sku_detail(self, request):
        doc_type = request.query_params.get("type")
        doc_number = request.query_params.get("number")
        sku_rowid = request.query_params.get("sku_rowid")
        id_plan = request.query_params.get("id_plan", 300)

        if not doc_type or not doc_number or not sku_rowid:
            return Response(
                {"error": "type, number and sku_rowid are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = OPProductionService.get_sku_detail(
            doc_type, int(doc_number), int(id_plan), int(sku_rowid)
        )

        if not data:
            return Response(
                {"error": "SKU not found in production order"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="materials")
    def materials(self, request):
        doc_type = request.query_params.get("type")
        doc_number = request.query_params.get("number")

        if not doc_type or not doc_number:
            return Response(
                {"error": "type and number are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = OPProductionService.get_materiales_op_json(doc_type, int(doc_number))

        if not data:
            return Response({"error": "No data found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(data, status=status.HTTP_200_OK)
