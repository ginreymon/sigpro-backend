from rest_framework import serializers
from apps.production.models.work_break import WorkBreak


class WorkBreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkBreak
        fields = "__all__"
