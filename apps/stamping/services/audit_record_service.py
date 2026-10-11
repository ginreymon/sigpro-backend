from django.db import transaction

from apps.stamping.repositories.audit_record_repository import AuditRecordRepository


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
        """Replaces the whole audit block of an OP (delete + create)."""
        with transaction.atomic():
            AuditRecordRepository.delete_block(
                validated_data.get("op_number"),
                validated_data.get("op_rowid"),
                validated_data.get("op_type"),
            )
            return AuditRecordService.create_block(validated_data, user)

    @staticmethod
    def delete_block(op_number, op_rowid, op_type) -> None:
        AuditRecordRepository.delete_block(op_number, op_rowid, op_type)

    @staticmethod
    def confirm_block(op_number, op_rowid, op_type, user):
        """Marks the block as audited. Returns its details, or None when the OP
        has no audit block."""
        updated = AuditRecordRepository.mark_audited(op_number, op_rowid, op_type, user)
        if not updated:
            return None
        return AuditRecordRepository.block_details(op_number, op_rowid, op_type)

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
