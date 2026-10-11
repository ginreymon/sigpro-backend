from rest_framework import status, viewsets
from rest_framework.response import Response
from apps.stamping.services.sku_reference_service import SkuReferenceService
from core.exceptions import error_response


class SkuReferenceViewSet(viewsets.ViewSet):

    def list(self, request):
        data = SkuReferenceService.get_references()

        if not data:
            return error_response(
                "No data found", status_code=status.HTTP_404_NOT_FOUND, code="not_found",
                legacy={"error": "No data found"},
            )

        return Response(data, status=status.HTTP_200_OK)
