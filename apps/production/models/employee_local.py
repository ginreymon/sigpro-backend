from django.db import models
from core.models import TimeAuditModel, ActiveModel
from core.models import LocalBaseModel


class EmployeeLocal(TimeAuditModel, ActiveModel, LocalBaseModel):

    rowid = models.BigIntegerField(unique=True)

    first_name = models.CharField(max_length=255)
    last_name1 = models.CharField(max_length=255)
    last_name2 = models.CharField(max_length=255, blank=True, null=True)
    id_number = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["rowid"]

    def __str__(self):
        return f"{self.first_name} {self.last_name1}"
