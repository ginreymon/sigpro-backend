from django.contrib.auth.models import User
from django.db.models import Max
from rest_framework import serializers
from apps.production.models.module import Module
from apps.production.models.module_user_account import ModuleUserAccount
from apps.production.models.work_center_local import WorkCenterLocal
from apps.production.models.production_area import ProductionArea
from apps.stamping.models import StampingMachine, StampingModuleMachine
from .work_center_local_serializer import WorkCenterLocalSerializer
from .production_area_serializer import ProductionAreaSerializer
from core.serializers.audit_serializer import AuditSerializer


class ModuleSerializer(AuditSerializer):
    number = serializers.IntegerField(required=False, allow_null=True)

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

    uses_processes_search = serializers.BooleanField(write_only=True, required=False, default=False)

    assigned_users = serializers.SerializerMethodField()

    assigned_user_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        write_only=True,
        required=False,
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
        return {
            "id": assignment.machine_id,
            "name": assignment.machine.name,
            "machine_type_id": assignment.machine.machine_type_id,
            "uses_processes_search": assignment.uses_processes_search,
        }

    def get_assigned_users(self, obj):
        links = obj.assigned_users.select_related("user")
        return [{"id": link.user.id, "username": link.user.username} for link in links]

    def create(self, validated_data):
        if not validated_data.get("number"):
            validated_data["number"] = self._next_number()
        machine_provided = "machine_id" in validated_data
        machine = validated_data.pop("machine_id", None)
        uses_processes_search = validated_data.pop("uses_processes_search", False)
        users_provided = "assigned_user_ids" in validated_data
        users = validated_data.pop("assigned_user_ids", None)
        instance = super().create(validated_data)
        if machine_provided:
            self._sync_machine(instance, machine, uses_processes_search)
        if users_provided:
            self._sync_users(instance, users)
        return instance

    def update(self, instance, validated_data):
        if "number" in validated_data and not validated_data.get("number"):
            validated_data["number"] = self._next_number()
        machine_provided = "machine_id" in validated_data
        machine = validated_data.pop("machine_id", None)
        uses_processes_search = validated_data.pop("uses_processes_search", False)
        users_provided = "assigned_user_ids" in validated_data
        users = validated_data.pop("assigned_user_ids", None)
        instance = super().update(instance, validated_data)
        if machine_provided:
            self._sync_machine(instance, machine, uses_processes_search)
        if users_provided:
            self._sync_users(instance, users)
        return instance

    def _next_number(self):
        last_number = Module.objects.aggregate(max_number=Max("number"))["max_number"]
        return (last_number or 0) + 1

    def _sync_machine(self, module, machine, uses_processes_search=False):
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
            existing.uses_processes_search = uses_processes_search
            existing.updated_by = module.updated_by
            existing.save(update_fields=["machine", "uses_processes_search", "updated_by"])
        else:
            StampingModuleMachine.objects.create(
                module=module,
                machine=machine,
                uses_processes_search=uses_processes_search,
                created_by=module.created_by,
                updated_by=module.updated_by,
            )

    def _sync_users(self, module, users):
        users = users or []

        conflict = (
            ModuleUserAccount.objects.filter(user__in=users)
            .exclude(module=module)
            .select_related("user", "module")
            .first()
        )
        if conflict:
            raise serializers.ValidationError(
                {
                    "assigned_user_ids": (
                        f'La cuenta "{conflict.user.username}" ya está asociada '
                        f'al módulo "{conflict.module.name}".'
                    )
                }
            )

        ModuleUserAccount.objects.filter(module=module).exclude(user__in=users).delete()
        existing_user_ids = set(
            ModuleUserAccount.objects.filter(module=module).values_list("user_id", flat=True)
        )
        for user in users:
            if user.id in existing_user_ids:
                continue
            ModuleUserAccount.objects.create(
                module=module,
                user=user,
                created_by=module.created_by,
                updated_by=module.updated_by,
            )
