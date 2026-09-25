from rest_framework import serializers

from apps.integration.models import SiesaOutboundDocument


class SiesaOutboundDocumentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    flat_file_line_count = serializers.SerializerMethodField()

    class Meta:
        model = SiesaOutboundDocument
        fields = [
            'id',
            'document_type',
            'idempotency_key',
            'flat_file_line_count',
            'op_rowid',
            'op_number',
            'work_center_code',
            'work_center_rowid',
            'location_id',
            'status',
            'status_display',
            'attempts',
            'next_retry_at',
            'error_type',
            'error_detail',
            'sent_at',
            'created_at',
            'updated_at',
        ]

    def get_flat_file_line_count(self, obj):
        return len(obj.flat_file_lines) if obj.flat_file_lines else 0
