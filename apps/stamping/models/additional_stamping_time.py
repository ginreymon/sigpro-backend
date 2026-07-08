from django.db import models
from core.models import AuditModel
from .stamping_machine import StampingMachine


class AdditionalStampingTime(AuditModel):
    code_number = models.CharField(max_length=50)
    engineering_code = models.CharField(max_length=50)
    machine = models.ForeignKey(StampingMachine, on_delete=models.PROTECT, related_name='additional_stamping_times')
    process = models.CharField(max_length=100)
    # excel cell has numbered steps ("1. ... 2. ...") -> stored as array, item "1" at index 0
    process_description = models.JSONField(null=True, blank=True)
    standard_time = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    class Meta:
        ordering = ["code_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["code_number", "engineering_code"],
                name="unique_code_number_engineering_code",
            ),
        ]

    def __str__(self):
        return f"{self.code_number} - {self.process}"
