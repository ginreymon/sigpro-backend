from django.db import models
from django.contrib.auth.models import User
from core.models import TimeAuditModel, UserAuditModel
from apps.production.models import EmployeeLocal


class UserEmployeeLink(TimeAuditModel, UserAuditModel):

    django_user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="employee_link"
    )

    employee_local = models.OneToOneField(
        EmployeeLocal, on_delete=models.CASCADE, related_name="user_links"
    )

    def __str__(self):
        return f"{self.employee_local.rowid} - {self.django_user.username}"
