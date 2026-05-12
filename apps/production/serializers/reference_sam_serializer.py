from rest_framework import serializers
from core.serializers.audit_serializer import AuditSerializer
from apps.production.models.reference_sam import ReferenceSam


class ReferenceSamSerializer(AuditSerializer):

    skus_count = serializers.SerializerMethodField()
    reference  = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = ReferenceSam
        fields = "__all__"

    def get_skus_count(self, obj):
        return obj.skus_count or 0
