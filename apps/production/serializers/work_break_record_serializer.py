from rest_framework import serializers
from apps.production.models.work_break_record import WorkBreakRecord


class WorkBreakRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkBreakRecord
        fields = "__all__"
