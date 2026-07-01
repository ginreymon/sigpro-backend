from rest_framework import serializers
from apps.catalog.models.technical_sheet_status import TechnicalSheetStatus


class TechnicalSheetStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalSheetStatus
        fields = ['id', 'name']
