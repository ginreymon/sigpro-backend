from rest_framework import serializers
from apps.production.models.module import Module
from apps.production.models.work_center_local import WorkCenterLocal
from .work_center_local_serializer import WorkCenterLocalSerializer


class ModuleSerializer(serializers.ModelSerializer):
    work_center = WorkCenterLocalSerializer(read_only=True)

    work_center_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkCenterLocal.objects.all(),
        source="work_center",
        write_only=True
    )

    class Meta:
        model = Module
        fields = "__all__"
