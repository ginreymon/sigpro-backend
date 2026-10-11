from rest_framework import serializers

from apps.production.serializers.module_extensions import ModuleSerializerExtension
from apps.stamping.models import StampingMachine, StampingModuleMachine


class ModuleMachineField(serializers.Field):
    """Read-only `machine` of a module: its stamping machine assignment, if any."""

    def __init__(self, **kwargs):
        kwargs["source"] = "*"
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def to_representation(self, module):
        assignment = getattr(module, "stamping_machine_assignment", None)
        if not assignment:
            return None
        return {
            "id": assignment.machine_id,
            "name": assignment.machine.name,
            "machine_type_id": assignment.machine.machine_type_id,
            "uses_processes_search": assignment.uses_processes_search,
        }


class ModuleMachineExtension(ModuleSerializerExtension):
    """Adds the stamping machine assignment (machine / machine_id /
    uses_processes_search) to ModuleSerializer."""

    def get_fields(self) -> dict:
        return {
            "machine": ModuleMachineField(),
            "machine_id": serializers.PrimaryKeyRelatedField(
                queryset=StampingMachine.objects.all(),
                write_only=True,
                required=False,
                allow_null=True,
            ),
            "uses_processes_search": serializers.BooleanField(
                write_only=True, required=False, default=False
            ),
        }

    def extract(self, validated_data: dict):
        provided = "machine_id" in validated_data
        machine = validated_data.pop("machine_id", None)
        uses_processes_search = validated_data.pop("uses_processes_search", False)
        return provided, machine, uses_processes_search

    def apply(self, module, state) -> None:
        provided, machine, uses_processes_search = state
        if provided:
            self._sync_machine(module, machine, uses_processes_search)

    @staticmethod
    def _sync_machine(module, machine, uses_processes_search=False):
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
