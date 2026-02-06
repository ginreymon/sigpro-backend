from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.production.serializers import OPProductionDetailSerializer
from apps.production.services.op_production_service import OPProductionService


class OPProductionDetailView(APIView):

    def get(self, request):
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
