from django.db import models
from core.models import TimeAuditModel, UserAuditModel
from .module import Module
from .employee_local import EmployeeLocal


class ModuleAssignee(TimeAuditModel, UserAuditModel):

    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    employee = models.ForeignKey(EmployeeLocal, on_delete=models.CASCADE)

    class Meta:
        db_table = "production_module_assignee"
        unique_together = ("module", "employee")
        ordering = ["module"]

    def __str__(self):
        return f"{self.employee} assigned to {self.module}"
