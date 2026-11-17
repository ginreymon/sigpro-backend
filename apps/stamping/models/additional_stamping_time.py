from django.db import models
from core.models import AuditModel
from .stamping_machine import StampingMachine
from .stamping_machine_type import StampingMachineType


class AdditionalStampingTime(AuditModel):
    code_number = models.CharField(max_length=50)
    engineering_code = models.CharField(max_length=50)
    machine = models.ForeignKey(StampingMachine, on_delete=models.PROTECT, null=True, blank=True, related_name='additional_stamping_times')
    machine_type = models.ForeignKey(StampingMachineType, on_delete=models.PROTECT, related_name='additional_stamping_times')
    process = models.CharField(max_length=100)
    standard_time_minutes = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    class Meta:
        db_table = "stamping_additional_stamping_time"
        ordering = ["engineering_code", "code_number", "machine__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["code_number", "engineering_code"],
                name="unique_code_number_engineering_code",
                
            ),
        ]

    def save(self, *args, **kwargs):
        # Si hay machine, machine_type se deriva de ahí (nunca se elige de forma
        # independiente). Sin machine, machine_type se elige a mano en el form.
        if self.machine_id:
            self.machine_type_id = self.machine.machine_type_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code_number} - {self.process}"
