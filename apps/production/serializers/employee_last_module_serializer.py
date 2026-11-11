from rest_framework import serializers
from apps.people.serializers import EmployeeLocalSerializer
from apps.production.models.module import Module


class ModuleSummarySerializer(serializers.ModelSerializer):
    """Flat, read-only module columns (FKs as ids): no per-row queries."""

    class Meta:
        model = Module
        fields = "__all__"


class EmployeeWithLastModuleSerializer(EmployeeLocalSerializer):
    """EmployeeLocalSerializer + `last_module`; used only when core_module_id is sent.

    Expects the queryset to prefetch assignments into `last_module_assignments`
    (see EmployeeLocalViewSet.get_queryset).
    """

    last_module = serializers.SerializerMethodField()

    class Meta(EmployeeLocalSerializer.Meta):
        pass

    def get_last_module(self, obj):
        assignments = getattr(obj, "last_module_assignments", None)
        if not assignments:
            return None
        return ModuleSummarySerializer(assignments[0].module).data
