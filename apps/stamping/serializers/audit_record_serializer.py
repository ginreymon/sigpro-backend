from django.db import transaction
from rest_framework import serializers
from apps.stamping.models.audit_record import AuditRecord
from apps.stamping.models.audit_record_detail import AuditRecordDetail


class AuditRecordSerializer(serializers.ModelSerializer):
    """Aplana AuditRecordDetail + su AuditRecord padre para que la API siga
    exponiendo una fila por color, igual que antes de normalizar la tabla."""

    op_number = serializers.IntegerField(source='audit_record.op_number', read_only=True)
    op_rowid = serializers.IntegerField(source='audit_record.op_rowid', read_only=True)
    op_type = serializers.CharField(source='audit_record.op_type', read_only=True)
    total_ordered_quantity = serializers.IntegerField(source='audit_record.total_ordered_quantity', read_only=True)
    is_audited = serializers.BooleanField(source='audit_record.is_audited', read_only=True)

    created_at = serializers.DateTimeField(source='audit_record.created_at', read_only=True)
    updated_at = serializers.DateTimeField(source='audit_record.updated_at', read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(source='audit_record.created_by', read_only=True)
    created_by_username = serializers.CharField(source='audit_record.created_by.username', read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(source='audit_record.updated_by', read_only=True)
    updated_by_username = serializers.CharField(source='audit_record.updated_by.username', read_only=True)

    total_audited_quantity = serializers.SerializerMethodField()
    matches_total = serializers.SerializerMethodField()
    quantities_match = serializers.SerializerMethodField()

    class Meta:
        model = AuditRecordDetail
        fields = [
            'id',
            'op_number', 'op_rowid', 'op_type', 'total_ordered_quantity', 'is_audited',
            'color', 'sku_rowids', 'ordered_quantity', 'audited_quantity',
            'total_audited_quantity', 'matches_total', 'quantities_match',
            'created_at', 'updated_at',
            'created_by', 'created_by_username',
            'updated_by', 'updated_by_username',
        ]

    def get_total_audited_quantity(self, obj):
        return obj.audit_record.total_audited_quantity

    def get_matches_total(self, obj):
        return obj.audit_record.matches_total

    def get_quantities_match(self, obj):
        return obj.quantities_match


class AuditedOpSummarySerializer(serializers.ModelSerializer):
    """Una fila por OP auditada (no por color) — alimenta el listado global
    de OPs auditadas en la tab 'Auditoría'."""

    total_audited_quantity = serializers.SerializerMethodField()
    matches_total = serializers.SerializerMethodField()
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True, default=None)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = AuditRecord
        fields = [
            'id', 'op_number', 'op_rowid', 'op_type', 'total_ordered_quantity',
            'total_audited_quantity', 'matches_total', 'is_audited',
            'created_at', 'updated_at',
            'created_by', 'created_by_username',
            'updated_by', 'updated_by_username',
        ]

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
    total_ordered_quantity = serializers.IntegerField(min_value=0)
    colors = ColorAuditSerializer(many=True)

    def create(self, validated_data):
        colors = validated_data.pop("colors")
        user = self.context["request"].user

        with transaction.atomic():
            audit_record = AuditRecord.objects.create(
                op_number=validated_data.get("op_number"),
                op_rowid=validated_data.get("op_rowid"),
                op_type=validated_data.get("op_type"),
                total_ordered_quantity=validated_data["total_ordered_quantity"],
                created_by=user,
                updated_by=user,
            )
            details = [
                AuditRecordDetail.objects.create(
                    audit_record=audit_record,
                    color=entry["color"],
                    sku_rowids=entry["sku_rowids"],
                    ordered_quantity=entry["ordered_quantity"],
                    audited_quantity=entry["audited_quantity"],
                )
                for entry in colors
            ]
        return details

    def replace(self, validated_data):
        """Reemplaza el bloque completo de auditoría de una OP (delete + create).

        El delete de los AuditRecord padres elimina en cascada sus
        AuditRecordDetail hijos."""
        with transaction.atomic():
            AuditRecord.objects.filter(
                op_number=validated_data.get("op_number"),
                op_rowid=validated_data.get("op_rowid"),
                op_type=validated_data.get("op_type"),
            ).delete()
            return self.create(validated_data)
