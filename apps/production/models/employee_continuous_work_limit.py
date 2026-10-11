from django.db import models
from core.models.audit_model import AuditModel
from apps.people.models import EmployeeLocal


class EmployeeContinuousWorkLimit(AuditModel):

    employee = models.OneToOneField(
        EmployeeLocal,
        on_delete=models.CASCADE,
        related_name="continuous_work_limit",
    )

    # Minutos por hora que el empleado debe trabajar de forma continua.
    # Sirve como valor por defecto de worked_minutes_per_hour en
    # WorkSessionActivityEmployee, consumido por dbo.fn_peso_empleado.
    continuous_work_minutes = models.PositiveSmallIntegerField()
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "production_employee_continuous_work_limit"
        ordering = ["employee"]

    def __str__(self):
        return f"{self.employee} - {self.continuous_work_minutes} min"
