from django.db import transaction
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


class ColorAuditSerializer(serializers.Serializer):
    color = serializers.CharField(max_length=100)
    sku_rowids = serializers.ListField(child=serializers.IntegerField())
    ordered_quantity = serializers.IntegerField(min_value=0)
    audited_quantity = serializers.IntegerField(min_value=0)


class AuditRecordBulkCreateSerializer(serializers.Serializer):
    op_number = serializers.IntegerField(required=False, allow_null=True)
    op_rowid = serializers.IntegerField(required=False, allow_null=True)
    op_type = serializers.CharField(required=False, allow_null=True, max_length=10)
    total_op_quantity = serializers.IntegerField(min_value=0)
    colors = ColorAuditSerializer(many=True)

    def create(self, validated_data):
        colors = validated_data.pop("colors")
        user = self.context["request"].user

        instances = []
        with transaction.atomic():
            for entry in colors:
                instances.append(
                    AuditRecord.objects.create(
                        op_number=validated_data.get("op_number"),
                        op_rowid=validated_data.get("op_rowid"),
                        op_type=validated_data.get("op_type"),
                        total_op_quantity=validated_data["total_op_quantity"],
                        color=entry["color"],
                        sku_rowids=entry["sku_rowids"],
                        ordered_quantity=entry["ordered_quantity"],
                        audited_quantity=entry["audited_quantity"],
                        created_by=user,
                        updated_by=user,
                    )
                )
        return instances
