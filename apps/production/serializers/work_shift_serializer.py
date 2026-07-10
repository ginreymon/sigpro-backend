from rest_framework import serializers
from apps.production.models.work_shift import WorkShift
from apps.production.models.production_area import ProductionArea
from core.serializers.audit_serializer import AuditSerializer
from core.serializers.module_serializer import ModuleSerializer
from .production_area_serializer import ProductionAreaSerializer


class WorkShiftSerializer(AuditSerializer):
    app_module_detail = ModuleSerializer(source="app_module", read_only=True)

    location = ProductionAreaSerializer(read_only=True)

    location_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductionArea.objects.all(),
        source="location",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = WorkShift
        fields = "__all__"
