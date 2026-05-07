from apps.production.models.production_record import ProductionRecord
from core.serializers.audit_serializer import AuditSerializer
from rest_framework import serializers
from django.utils import timezone


class ProductionRecordSerializer(AuditSerializer):
    server_now = serializers.SerializerMethodField()

    class Meta:
        model = ProductionRecord
        fields = "__all__"
        read_only_fields = ["start_time", "end_time", "server_now"]

    def get_server_now(self, obj):
        return timezone.now()
    
    def update(self, instance, validated_data):
        quantity_fields = [
            "ordered_quantity",
            "planned_quantity",
            "completed_quantity",
            "scrap_quantity",
            "rejected_quantity",
        ]
      
        for field in quantity_fields:
            if field in validated_data and getattr(instance, field) != validated_data[field]:
                instance.end_time = timezone.now()
                break

        return super().update(instance, validated_data)
