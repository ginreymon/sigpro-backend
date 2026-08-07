from rest_framework import serializers
from core.serializers.audit_serializer import AuditSerializer
from apps.production.serializers import SkuItemReferenceDetailSerializer
from apps.stamping.models import StampingReferenceSam


class StampingReferenceSamSerializer(AuditSerializer):

    reference = serializers.SerializerMethodField()
    tasks_per_hour = serializers.ReadOnlyField()
    machine_type_name = serializers.SerializerMethodField()
    piece_name = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()
    stamp_type_description_name = serializers.SerializerMethodField()
    fabric_type_name = serializers.SerializerMethodField()
    technique_name = serializers.SerializerMethodField()
    layout_form_name = serializers.SerializerMethodField()

    class Meta:
        model = StampingReferenceSam
        fields = '__all__'

    def get_reference(self, obj):
        sku_map = self.context.get('sku_map') or {}
        sku = sku_map.get(obj.rowid_item)
        return SkuItemReferenceDetailSerializer(sku).data if sku else None

    def get_machine_type_name(self, obj):
        return obj.machine_type.name if obj.machine_type else None

    def get_piece_name(self, obj):
        return obj.piece.name if obj.piece else None

    def get_location_name(self, obj):
        return obj.location.name if obj.location else None

    def get_stamp_type_description_name(self, obj):
        return obj.stamp_type_description.name if obj.stamp_type_description else None

    def get_fabric_type_name(self, obj):
        return obj.fabric_type.name if obj.fabric_type else None

    def get_technique_name(self, obj):
        return obj.technique.name if obj.technique else None

    def get_layout_form_name(self, obj):
        return obj.layout_form.name if obj.layout_form else None
