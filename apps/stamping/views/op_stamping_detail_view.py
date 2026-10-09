from rest_framework import viewsets
from rest_framework.decorators import action
from apps.common.http import missing_params_response, ok_or_404
from apps.stamping.services.op_stamping_service import OPStampingService


class OPStampingDetailViewSet(viewsets.ViewSet):

    @action(detail=False, methods=["get"], url_path="detail")
    def get_detail(self, request):
        doc_type = request.query_params.get("type")
        doc_number = request.query_params.get("number")

        error = missing_params_response(
            request.query_params, "type", "number", message="type and number are required"
        )
        if error:
            return error

        data = OPStampingService.get_detalle_estampacion_op_json(doc_type, int(doc_number))

        return ok_or_404(data)

    @action(detail=False, methods=["get"], url_path="traceability")
    def traceability(self, request):
        doc_number = request.query_params.get("number")
        doc_type = request.query_params.get("type")

        error = missing_params_response(
            request.query_params, "number", message="number is required"
        )
        if error:
            return error

        data = OPStampingService.get_trazabilidad_op_json(int(doc_number), doc_type)

        return ok_or_404(data)
