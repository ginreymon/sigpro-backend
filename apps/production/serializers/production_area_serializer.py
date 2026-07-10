from rest_framework import serializers
from core.models import Module as CoreModule
from apps.production.models.production_area import ProductionArea
from core.serializers.audit_serializer import AuditSerializer
from core.serializers.module_serializer import ModuleSerializer as CoreModuleSerializer


class ProductionAreaSerializer(AuditSerializer):
    core_module = CoreModuleSerializer(read_only=True)

    core_module_id = serializers.PrimaryKeyRelatedField(
        queryset=CoreModule.objects.all(),
        source="core_module",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ProductionArea
        fields = "__all__"
