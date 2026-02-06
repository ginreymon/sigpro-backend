from rest_framework import serializers
from apps.production.models.production_record import ProductionRecord


class ProductionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionRecord
        fields = "__all__"
