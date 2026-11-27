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
            'color', 'sku_rowids', 'ordered_quantity', 'audited_quantity', 'audited_meters',
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
    cut_completed = serializers.SerializerMethodField()
    cut_tracking = serializers.SerializerMethodField()
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True, default=None)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = AuditRecord
        fields = [
            'id', 'op_number', 'op_rowid', 'op_type', 'total_ordered_quantity',
            'total_audited_quantity', 'matches_total', 'is_audited',
            'cut_completed', 'cut_tracking',
            'created_at', 'updated_at',
            'created_by', 'created_by_username',
            'updated_by', 'updated_by_username',
        ]

    def get_total_audited_quantity(self, obj):
        return obj.total_audited_quantity

    def get_matches_total(self, obj):
        return obj.matches_total

    def get_cut_completed(self, obj):
        tracking = getattr(obj, 'cut_tracking', None)
        return tracking.get('isCompleted') if tracking else None

    def get_cut_tracking(self, obj):
        tracking = getattr(obj, 'cut_tracking', None)
        if not tracking:
            return None
        return {
            'qty_to_execute': tracking.get('qtyToExecute'),
            'qty_completed': tracking.get('qtyCompleted'),
            'is_completed': tracking.get('isCompleted'),
            'operation': tracking.get('operation'),
        }


class ColorAuditSerializer(serializers.Serializer):
    color = serializers.CharField(max_length=100)
    sku_rowids = serializers.ListField(child=serializers.IntegerField())
    ordered_quantity = serializers.IntegerField(min_value=0)
    audited_quantity = serializers.IntegerField(min_value=0)
    # Meters (CALANDRA only). Optional: when the key is absent the service keeps the
    # value already saved for that color instead of erasing it.
    audited_meters = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False, allow_null=True,
    )


class AuditRecordBulkCreateSerializer(serializers.Serializer):
    op_number = serializers.IntegerField(required=False, allow_null=True)
    op_rowid = serializers.IntegerField(required=False, allow_null=True)
    op_type = serializers.CharField(required=False, allow_null=True, max_length=10)
    total_ordered_quantity = serializers.IntegerField(min_value=0)
    colors = ColorAuditSerializer(many=True)


REQUIRED_PARAM_MESSAGE = "Este parámetro es obligatorio."
INTEGER_PARAM_MESSAGE = "Debe ser un número entero."


def _required_messages(**extra):
    return {"required": REQUIRED_PARAM_MESSAGE, "blank": REQUIRED_PARAM_MESSAGE,
            "null": REQUIRED_PARAM_MESSAGE, "invalid": INTEGER_PARAM_MESSAGE, **extra}


class OpBlockParamsSerializer(serializers.Serializer):
    """Query params that identify the audit block of an OP."""

    op_number = serializers.IntegerField(error_messages=_required_messages())
    op_rowid = serializers.IntegerField(error_messages=_required_messages())
    op_type = serializers.CharField(error_messages=_required_messages())


class OpDocumentParamsSerializer(serializers.Serializer):
    """Query params of the audit status lookup by document (?docType=OP&docNumber=40346)."""

    docType = serializers.CharField(error_messages=_required_messages())
    docNumber = serializers.IntegerField(error_messages=_required_messages())


def validate_query_params(serializer_class, query_params) -> dict:
    """Validates query params and raises a ValidationError shaped {field: message}
    (one message per field, as the audit endpoints always returned)."""
    serializer = serializer_class(data=query_params)
    if not serializer.is_valid():
        raise serializers.ValidationError(
            {field: messages[0] for field, messages in serializer.errors.items()}
        )
    return serializer.validated_data