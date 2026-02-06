from django.db import models
from core.models import TimeAuditModel, ActiveModel
from core.models import LocalBaseModel


class WorkCenterLocal(TimeAuditModel, ActiveModel, LocalBaseModel):

    rowid = models.BigIntegerField(unique=True)
    is_deleted = models.BooleanField(default=False)

    code = models.CharField(max_length=255)
    description = models.TextField()
    short_description = models.CharField(max_length=255)

    class Meta:
        ordering = ["rowid"]

    def __str__(self):
        return f"{self.code} {self.short_description}"
