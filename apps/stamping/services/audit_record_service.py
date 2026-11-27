import logging

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.production.services.op_production_service import OPProductionService
from apps.stamping.repositories.audit_record_repository import AuditRecordRepository
from apps.stamping.services.op_stamping_service import OPStampingService

logger = logging.getLogger(__name__)

# StampingMachineType.id of CALANDRA.
CALANDRA_MACHINE_TYPE_ID = 4


class AuditRecordService:
    """Rules for the stamping audit blocks. Audit records are always handled as a
    whole block per OP (op_number/op_rowid/op_type), never row by row."""

    @staticmethod
    def create_block(validated_data: dict, user) -> list:
        with transaction.atomic():
            return AuditRecordRepository.create_block(
                op_number=validated_data.get("op_number"),
                op_rowid=validated_data.get("op_rowid"),
                op_type=validated_data.get("op_type"),
                total_ordered_quantity=validated_data["total_ordered_quantity"],
                colors=validated_data["colors"],
                user=user,
            )

    @staticmethod
    def replace_block(validated_data: dict, user) -> list:
        """Replaces the whole audit block of an OP (delete + create). A color sent
        without the `audited_meters` key keeps the meters it had, so a partial
        payload never erases previously recorded meters (null clears them)."""
        op_number = validated_data.get("op_number")
        op_rowid = validated_data.get("op_rowid")
        op_type = validated_data.get("op_type")
        with transaction.atomic():
            previous_meters = AuditRecordRepository.meters_by_color(op_number, op_rowid, op_type)
            for entry in validated_data["colors"]:
                if "audited_meters" not in entry:
                    entry["audited_meters"] = previous_meters.get(entry["color"])
            AuditRecordRepository.delete_block(op_number, op_rowid, op_type)
            return AuditRecordService.create_block(validated_data, user)

    @staticmethod
    def delete_block(op_number, op_rowid, op_type) -> None:
        AuditRecordRepository.delete_block(op_number, op_rowid, op_type)

    @staticmethod
    def confirm_block(op_number, op_rowid, op_type, user):
        """Marks the block as audited. Returns its details, or None when the OP
        has no audit block. CALANDRA orders need meters in every color first."""
        if AuditRecordService._is_calandra(op_type, op_number):
            missing = [
                d.color for d in AuditRecordRepository.block_details(op_number, op_rowid, op_type)
                if d.audited_meters is None
            ]
            if missing:
                raise ValidationError({
                    "audited_meters": "Ingresa los metros de todos los colores antes de aprobar: "
                                      + ", ".join(missing) + ".",
                })
        updated = AuditRecordRepository.mark_audited(op_number, op_rowid, op_type, user)
        if not updated:
            return None
        return AuditRecordRepository.block_details(op_number, op_rowid, op_type)

    @staticmethod
    def _is_calandra(op_type, op_number) -> bool:
        """True when the OP's machine type (same source as production-orders/processes)
        is CALANDRA. Any lookup failure counts as "not CALANDRA" so other machine
        types keep their current approval flow."""
        if op_type is None or op_number is None:
            return False
        try:
            data = OPStampingService.get_ordenes_produccion_proceso_json(op_type, op_number)
        except Exception:
            logger.warning("Machine type lookup failed for %s %s", op_type, op_number, exc_info=True)
            return False
        return bool(data) and data.get("machineTypeId") == CALANDRA_MACHINE_TYPE_ID

    @staticmethod
    def status_for_document(op_type, op_number) -> dict:
        """Audit state of an OP, without the per-color detail."""
        audit_record = AuditRecordRepository.find_by_document(op_type, op_number)

        if not audit_record:
            return {
                "exists": False,
                "is_audited": False,
                "total_ordered_quantity": None,
                "total_audited_quantity": None,
                "matches_total": None,
            }

        return {
            "exists": True,
            "is_audited": audit_record.is_audited,
            "total_ordered_quantity": audit_record.total_ordered_quantity,
            "total_audited_quantity": audit_record.total_audited_quantity,
            "matches_total": audit_record.matches_total,
        }

    @staticmethod
    def audited_ops(search=None):
        return AuditRecordRepository.audited_ops(search)

    @staticmethod
    def attach_cut_tracking(records) -> None:
        """Sets `cut_tracking` (dict or None) on each record, one SP call per
        distinct OP. Swap the loop for a batch query if this gets slow."""
        cache = {}
        for record in records:
            key = (record.op_type, record.op_number)
            if key not in cache:
                cache[key] = OPProductionService.get_cut_tracking(*key)
            record.cut_tracking = cache[key]
