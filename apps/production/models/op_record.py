from django.db import models
from django.utils import timezone
from core.models.audit_model import TimeAuditModel, UserAuditModel


class OpRecord(TimeAuditModel, UserAuditModel):
    """Campos y comportamiento comunes de los registros de una OP
    (ProductionRecord y StampingRecord).

    `work_session_activity` no se declara aquí: cada registro usa un
    `related_name` propio (production_records / stamping_records).
    """

    op_rowid = models.BigIntegerField(null=True, blank=True)
    op_number = models.IntegerField(null=True, blank=True)
    op_type = models.CharField(max_length=10, null=True, blank=True)

    ordered_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    completed_quantity = models.DecimalField(max_digits=10, decimal_places=2)

    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def close(self):
        if self.end_time:
            return
        self.end_time = timezone.now()
        self.save(update_fields=["end_time"])
