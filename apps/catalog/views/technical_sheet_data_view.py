from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from apps.catalog.services.technical_sheet_service import TechnicalSheetService


class TechnicalSheetDataViewSet(viewsets.ViewSet):

    def list(self, request):
        sheet_id = request.query_params.get("sheet_id")

        if not sheet_id:
            return Response(
                {"error": "sheet_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = TechnicalSheetService.get_technical_sheet_json(int(sheet_id))

        if not data:
            return Response(
                {"error": "No data found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(data, status=status.HTTP_200_OK)

    def referencias(self, request):
        data = TechnicalSheetService.get_referencias()

        if not data:
            return Response(
                {"error": "No data found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(data, status=status.HTTP_200_OK)

    def referencia_info(self, request):
        rowid_item = request.query_params.get("rowid_item")

        if not rowid_item:
            return Response(
                {"error": "rowid_item is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = TechnicalSheetService.get_sku_reference_info(int(rowid_item))

        if not data:
            return Response(
                {"error": "No data found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(data, status=status.HTTP_200_OK)
