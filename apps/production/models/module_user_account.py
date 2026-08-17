from django.contrib.auth.models import User
from django.db import models
from core.models import AuditModel
from .module import Module


class ModuleUserAccount(AuditModel):

    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="assigned_users",
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_module",
    )

    class Meta:
        db_table = "production_module_user_account"

    def __str__(self):
        return f"{self.user.username} - {self.module}"
