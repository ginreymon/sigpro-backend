from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from apps.common.http import missing_params_response, ok_or_404
from apps.production.serializers import OPProductionDetailSerializer
from apps.production.services.op_production_service import OPProductionService


class OPProductionDetailViewSet(viewsets.ViewSet):

    serializer_class = OPProductionDetailSerializer

    def list(self, request):
        doc_type = request.query_params.get("type")
        doc_number = request.query_params.get("number")

        error = missing_params_response(
            request.query_params, "type", "number", message="type and number are required"
        )
        if error:
            return error

        data = OPProductionService.get_detalle_produccion_op(doc_type, int(doc_number))

        serializer = OPProductionDetailSerializer(data, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="detail")
    def get_detail(self, request):
        doc_type = request.query_params.get("type")
        doc_number = request.query_params.get("number")
        id_plan = request.query_params.get("id_plan", 300)

        error = missing_params_response(
            request.query_params, "type", "number", message="type and number are required"
        )
        if error:
            return error

        data = OPProductionService.get_detalle_produccion_op_json_with_tracking(
            doc_type, int(doc_number), int(id_plan)
        )

        return ok_or_404(data)

    @action(detail=False, methods=["get"], url_path="sku-detail")
    def sku_detail(self, request):
        doc_type = request.query_params.get("type")
        doc_number = request.query_params.get("number")
        sku_rowid = request.query_params.get("sku_rowid")
        id_plan = request.query_params.get("id_plan", 300)

        error = missing_params_response(
            request.query_params,
            "type",
            "number",
            "sku_rowid",
            message="type, number and sku_rowid are required",
        )
        if error:
            return error

        data = OPProductionService.get_sku_detail(
            doc_type, int(doc_number), int(id_plan), int(sku_rowid)
        )

        return ok_or_404(data, "SKU not found in production order")

    @action(detail=False, methods=["get"], url_path="materials")
    def materials(self, request):
        doc_type = request.query_params.get("type")
        doc_number = request.query_params.get("number")

        error = missing_params_response(
            request.query_params, "type", "number", message="type and number are required"
        )
        if error:
            return error

        data = OPProductionService.get_materiales_op_json(doc_type, int(doc_number))

        return ok_or_404(data)
