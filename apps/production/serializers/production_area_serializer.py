from rest_framework import serializers
from core.models import Module as CoreModule
from apps.production.models.production_area import ProductionArea
from apps.production.models.production_area_cost_center import ProductionAreaCostCenter
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

    # `ProductionArea.cost_centers` es una property (respaldada por
    # ProductionAreaCostCenter) — se declara explícito porque `fields = "__all__"`
    # solo recoge campos de modelo reales, no properties.
    cost_centers = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_null=True, allow_empty=True
    )

    class Meta:
        model = ProductionArea
        fields = "__all__"

    def create(self, validated_data):
        cost_centers = validated_data.pop("cost_centers", None) or []
        audit_user = validated_data.get("created_by")
        instance = super().create(validated_data)
        self._sync_cost_centers(instance, cost_centers, audit_user)
        return instance

    def update(self, instance, validated_data):
        cost_centers = validated_data.pop("cost_centers", None)
        audit_user = validated_data.get("updated_by")
        instance = super().update(instance, validated_data)
        if cost_centers is not None:
            self._sync_cost_centers(instance, cost_centers, audit_user)
        return instance

    def _sync_cost_centers(self, instance, cost_center_rowids, audit_user):
        existing = set(instance.cost_center_links.values_list("cost_center_rowid", flat=True))
        incoming = set(cost_center_rowids)

        ProductionAreaCostCenter.objects.bulk_create([
            ProductionAreaCostCenter(
                production_area=instance,
                cost_center_rowid=rowid,
                created_by=audit_user,
                updated_by=audit_user,
            )
            for rowid in incoming - existing
        ])
        if existing - incoming:
            instance.cost_center_links.filter(cost_center_rowid__in=existing - incoming).delete()
