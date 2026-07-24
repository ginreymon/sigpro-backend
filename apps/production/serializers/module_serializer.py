from rest_framework import serializers
from apps.production.models.module import Module
from apps.production.models.work_center_local import WorkCenterLocal
from apps.production.models.production_area import ProductionArea
from apps.stamping.models import StampingMachine, StampingModuleMachine
from .work_center_local_serializer import WorkCenterLocalSerializer
from .production_area_serializer import ProductionAreaSerializer
from core.serializers.audit_serializer import AuditSerializer


class ModuleSerializer(AuditSerializer):
    work_center = WorkCenterLocalSerializer(read_only=True)

    work_center_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkCenterLocal.objects.all(), source="work_center", write_only=True
    )

    location = ProductionAreaSerializer(read_only=True)

    location_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductionArea.objects.all(),
        source="location",
        write_only=True,
        required=False,
        allow_null=True,
    )

    machine = serializers.SerializerMethodField()

    machine_id = serializers.PrimaryKeyRelatedField(
        queryset=StampingMachine.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Module
        fields = "__all__"

    employees = serializers.SerializerMethodField()

    def get_employees(self, obj):
        assignees = obj.moduleassignee_set.select_related("employee")
        return [
            {
                "id": a.employee.id,
                "first_name": a.employee.first_name,
                "last_name1": a.employee.last_name1,
                "last_name2": a.employee.last_name2,
            }
            for a in assignees
        ]

    def get_machine(self, obj):
        assignment = getattr(obj, "stamping_machine_assignment", None)
        if not assignment:
            return None
        return {"id": assignment.machine_id, "name": assignment.machine.name}

    def create(self, validated_data):
        machine_provided = "machine_id" in validated_data
        machine = validated_data.pop("machine_id", None)
        instance = super().create(validated_data)
        if machine_provided:
            self._sync_machine(instance, machine)
        return instance

    def update(self, instance, validated_data):
        machine_provided = "machine_id" in validated_data
        machine = validated_data.pop("machine_id", None)
        instance = super().update(instance, validated_data)
        if machine_provided:
            self._sync_machine(instance, machine)
        return instance

    def _sync_machine(self, module, machine):
        existing = StampingModuleMachine.objects.filter(module=module).first()

        if machine is None:
            if existing:
                existing.delete()
            return

        conflict = StampingModuleMachine.objects.filter(machine=machine).exclude(module=module).first()
        if conflict:
            raise serializers.ValidationError(
                {"machine_id": f'La máquina "{machine.name}" ya está asignada al módulo "{conflict.module.name}".'}
            )

        if existing:
            existing.machine = machine
            existing.updated_by = module.updated_by
            existing.save(update_fields=["machine", "updated_by"])
        else:
            StampingModuleMachine.objects.create(
                module=module,
                machine=machine,
                created_by=module.created_by,
                updated_by=module.updated_by,
            )
