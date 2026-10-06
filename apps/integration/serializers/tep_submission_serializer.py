import json

from rest_framework import serializers

from apps.integration.models import TepDetail, TepSubmission
from core.serializers.audit_serializer import AuditSerializer


class TepDetailSerializer(serializers.ModelSerializer):
    # Ids de los registros (production/stamping record) que respaldan el item.
    register_ids = serializers.SerializerMethodField()
    origin_id = serializers.SerializerMethodField()

    class Meta:
        model = TepDetail
        fields = [
            'id',
            'record_number',
            'op_document_type_id',
            'op_document_number',
            'operation_number',
            'operation_work_center_id',
            'operation_completed',
            'completed_quantity',
            'hours',
            'origin_id',
            'register_ids',
        ]

    def get_register_ids(self, obj):
        return [record.record_id for record in obj.records.all()]

    def get_origin_id(self, obj):
        records = obj.records.all()
        return records[0].origin_id if records else None


def _siesa_messages(error_detail: str | None) -> list[dict]:
    """Extrae los mensajes de error de SIESA de `error_detail` cuando es el
    dataset serializado a JSON por `siesa_webservice_client._parse_result`
    ({"_value_1": [{"Table": {...}}]}). Si es XML o un error de red (texto),
    devuelve [] y la UI muestra `error_detail` tal cual."""
    try:
        data = json.loads(error_detail or '')
    except ValueError:
        return []
    rows = data.get('_value_1') if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return []

    messages = []
    for row in rows:
        tables = row.get('Table') if isinstance(row, dict) else None
        for table in tables if isinstance(tables, list) else [tables]:
            if isinstance(table, dict):
                messages.append(
                    {
                        'line': table.get('f_nro_linea'),
                        'record_type': table.get('f_tipo_reg'),
                        'value': table.get('f_valor'),
                        'detail': table.get('f_detalle'),
                    }
                )
    return messages


class TepSubmissionSerializer(AuditSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    details = TepDetailSerializer(many=True, read_only=True)
    # Mensajes legibles de la respuesta de SIESA (ver _siesa_messages).
    siesa_messages = serializers.SerializerMethodField()

    def get_siesa_messages(self, obj):
        return _siesa_messages(obj.error_detail)

    class Meta:
        model = TepSubmission
        fields = [
            'id',
            'company_id',
            'operation_center_id',
            'document_type_id',
            'document_number',
            'date',
            'work_center_id',
            'status',
            'status_display',
            'error_type',
            'error_detail',
            'siesa_messages',
            'sent_at',
            'details',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_username',
            'updated_by',
            'updated_by_username',
        ]
