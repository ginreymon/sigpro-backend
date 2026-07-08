from rest_framework import serializers
from core.serializers.audit_serializer import AuditSerializer
from apps.production.serializers import SkuItemReferenceDetailSerializer
from apps.stamping.models import StampingReferenceSam


class StampingReferenceSamSerializer(AuditSerializer):

    reference_detail = serializers.SerializerMethodField()

    class Meta:
        model = StampingReferenceSam
        fields = '__all__'

    def get_reference_detail(self, obj):
        sku_map = self.context.get('sku_map') or {}
        sku = sku_map.get(obj.rowid_item)
        return SkuItemReferenceDetailSerializer(sku).data if sku else None
