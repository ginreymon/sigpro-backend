from django.db import models
from core.models import AuditModel
from .additional_stamping_time import AdditionalStampingTime


class AdditionalStampingTimeStep(AuditModel):
    additional_stamping_time = models.ForeignKey(
        AdditionalStampingTime, on_delete=models.CASCADE, related_name="steps"
    )
    order = models.PositiveIntegerField()
    description = models.CharField(max_length=255)
    standard_time = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    class Meta:
        db_table = "stamping_additional_stamping_time_step"
        ordering = ["additional_stamping_time", "order"]

    def __str__(self):
        return f"{self.additional_stamping_time.code_number} - paso {self.order}"
