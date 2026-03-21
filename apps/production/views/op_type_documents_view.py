from rest_framework import viewsets, status
from rest_framework.response import Response
from apps.production.serializers import OPTypeDocumentsSerializer
from apps.production.services.op_production_service import OPProductionService


class OPTypeDocumentsViewSet(viewsets.ViewSet):

    serializer_class = OPTypeDocumentsSerializer

    def list(self, request):
        data = OPProductionService.get_tipo_documentos_op()

        serializer = OPTypeDocumentsSerializer(data, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
