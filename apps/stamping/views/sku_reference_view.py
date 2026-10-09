from rest_framework import status, viewsets
from rest_framework.response import Response
from apps.stamping.services.sku_reference_service import SkuReferenceService


class SkuReferenceViewSet(viewsets.ViewSet):

    def list(self, request):
        data = SkuReferenceService.get_references()

        if not data:
            return Response(
                {"error": "No data found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(data, status=status.HTTP_200_OK)
