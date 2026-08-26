from django.db import models
from django.db.models import Q, CheckConstraint
from django.core.exceptions import ValidationError
from core.models.audit_model import TimeAuditModel, UserAuditModel
from apps.production.models.work_break import WorkBreak
from apps.production.models.module import Module


class ModuleDowntime(TimeAuditModel, UserAuditModel):

    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="module_downtimes"
    )

    work_break = models.ForeignKey(
        WorkBreak,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="module_downtimes",
    )

    name = models.CharField(max_length=255, null=True, blank=True)
    custom_reason = models.TextField(null=True, blank=True)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    resumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "production_module_downtime"
        ordering = ["start_time", "end_time"]
        constraints = [
            CheckConstraint(
                name="module_work_break_or_custom_reason",
                condition=(
                    (Q(work_break__isnull=False) & Q(custom_reason__isnull=True))
                    | (
                        Q(work_break__isnull=True)
                        & Q(custom_reason__isnull=False)
                        & ~Q(custom_reason="")
                    )
                ),
            )
        ]

    def clean(self):
        if not self.work_break:
            if not self.custom_reason or not self.custom_reason.strip():
                raise ValidationError("El motivo personalizado no puede estar vacío.")

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.work_break:
            self.name = self.work_break.name
            self.custom_reason = None

            if self.start_time and not self.end_time:
                self.end_time = self.start_time + self.work_break.duration

        else:
            self.name = self.custom_reason.strip()

        super().save(*args, **kwargs)

    @property
    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return None
