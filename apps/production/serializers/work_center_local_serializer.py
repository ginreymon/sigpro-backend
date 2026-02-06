from rest_framework import serializers
from apps.production.models.work_center_local import WorkCenterLocal


class WorkCenterLocalSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkCenterLocal
        fields = "__all__"
