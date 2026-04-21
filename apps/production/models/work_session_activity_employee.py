from core.models.audit_model import AuditModel
from django.db import models
from apps.production.models.employee_local import EmployeeLocal

class WorkSessionActivityEmployee(AuditModel):

    work_session_activity = models.ForeignKey(
        "production.WorkSessionActivity",
        on_delete=models.CASCADE,
        related_name="employee_snapshots"       
    )

    employee = models.ForeignKey(EmployeeLocal, on_delete=models.PROTECT)

    class Meta:
        unique_together = ("work_session_activity", "employee")
        indexes = [
            models.Index(fields=["work_session_activity", "employee"]),
        ]

    def __str__(self):
        return f"{self.employee} - {self.work_session_activity}"
