from django.db import models
from core.models import AuditModel
from .work_center_local import WorkCenterLocal


class Module(AuditModel):

    name = models.CharField(max_length=255,unique=True)
    number = models.IntegerField(unique=True)
    operator_count = models.IntegerField()
    location = models.CharField(max_length=255)

    work_center = models.ForeignKey(
        WorkCenterLocal,
        on_delete=models.PROTECT,
        related_name="modules",
        null=False,
        blank=False,
    )

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number} - {self.name}"
