from django.db.models import CharField
from django.db.models.functions import Cast
from django.utils import timezone

from apps.stamping.models.audit_record import AuditRecord
from apps.stamping.models.audit_record_detail import AuditRecordDetail


class AuditRecordRepository:
    """ORM access for the stamping audit blocks. An audit block is one
    AuditRecord (per OP) with one AuditRecordDetail per color."""

    @staticmethod
    def details_queryset():
        return AuditRecordDetail.objects.select_related(
            'audit_record', 'audit_record__created_by', 'audit_record__updated_by',
        ).all()

    @classmethod
    def block_details(cls, op_number, op_rowid, op_type):
        return cls.details_queryset().filter(
            audit_record__op_number=op_number,
            audit_record__op_rowid=op_rowid,
            audit_record__op_type=op_type,
        )

    @staticmethod
    def create_block(*, op_number, op_rowid, op_type, total_ordered_quantity, colors, user):
        audit_record = AuditRecord.objects.create(
            op_number=op_number,
            op_rowid=op_rowid,
            op_type=op_type,
            total_ordered_quantity=total_ordered_quantity,
            created_by=user,
            updated_by=user,
        )
        return [
            AuditRecordDetail.objects.create(
                audit_record=audit_record,
                color=entry["color"],
                sku_rowids=entry["sku_rowids"],
                ordered_quantity=entry["ordered_quantity"],
                audited_quantity=entry["audited_quantity"],
                audited_meters=entry.get("audited_meters"),
            )
            for entry in colors
        ]

    @classmethod
    def meters_by_color(cls, op_number, op_rowid, op_type) -> dict:
        return dict(
            cls.block_details(op_number, op_rowid, op_type).values_list('color', 'audited_meters')
        )

    @staticmethod
    def delete_block(op_number, op_rowid, op_type):
        # Cascade: deleting the parent AuditRecord removes its AuditRecordDetail rows.
        AuditRecord.objects.filter(
            op_number=op_number, op_rowid=op_rowid, op_type=op_type,
        ).delete()

    @staticmethod
    def mark_audited(op_number, op_rowid, op_type, user) -> int:
        # QuerySet.update() bypasses save(), so auto_now on updated_at won't
        # fire on its own — stamp it explicitly, it's what "most recently
        # audited" ordering in the audited-ops list sorts by.
        return AuditRecord.objects.filter(
            op_number=op_number, op_rowid=op_rowid, op_type=op_type,
        ).update(is_audited=True, updated_at=timezone.now(), updated_by=user)

    @staticmethod
    def find_by_document(op_type, op_number):
        return AuditRecord.objects.filter(op_type=op_type, op_number=op_number).first()

    @staticmethod
    def audited_ops(search=None):
        queryset = AuditRecord.objects.filter(is_audited=True).select_related(
            'created_by', 'updated_by',
        ).order_by('-updated_at')

        if search:
            queryset = queryset.annotate(
                op_number_str=Cast('op_number', output_field=CharField()),
            ).filter(op_number_str__icontains=search)

        return queryset
