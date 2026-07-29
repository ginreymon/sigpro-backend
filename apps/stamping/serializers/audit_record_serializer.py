from rest_framework import serializers
from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models.audit_record import AuditRecord


class AuditRecordSerializer(AuditSerializer):

    total_audited_quantity = serializers.SerializerMethodField()
    matches_total = serializers.SerializerMethodField()

    class Meta:
        model = AuditRecord
        fields = "__all__"

    def get_total_audited_quantity(self, obj):
        return obj.total_audited_quantity

    def get_matches_total(self, obj):
        return obj.matches_total
