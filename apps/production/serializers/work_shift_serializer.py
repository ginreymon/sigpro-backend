from rest_framework import serializers
from apps.production.models.work_shift import WorkShift


class WorkShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkShift
        fields = "__all__"
