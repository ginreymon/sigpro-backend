from django.db import models
from core.models import TimeAuditModel, ActiveModel
from core.models import LocalBaseModel


class EmployeeLocal(TimeAuditModel, ActiveModel, LocalBaseModel):

    first_name = models.CharField(max_length=255)
    last_name1 = models.CharField(max_length=255)
    last_name2 = models.CharField(max_length=255, blank=True, null=True)
    id_number = models.CharField(max_length=50, unique=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    contract_status = models.CharField(max_length=50, blank=True, null=True)
    cost_center_rowid = models.IntegerField(blank=True, null=True)
    cost_center_description = models.CharField(max_length=255, blank=True, null=True)
    cost_group_id = models.CharField(max_length=50, blank=True, null=True)
    cost_group_description = models.CharField(max_length=255, blank=True, null=True)
   
    @property
    def has_account(self):
        return hasattr(self, "user_link")

    @property
    def username(self):
        if self.has_account:
            return self.user_link.auth_user.username
        return None

    @property
    def user_id(self):
        if self.has_account:
            return self.user_link.auth_user.id
        return None

    @property
    def is_account_active(self):
        if self.has_account:
            return self.user_link.auth_user.is_active
        return False

    @property
    def groups(self):
        if self.has_account:
            return list(self.user_link.auth_user.groups.values("id", "name"))
        return []

    class Meta:
        db_table = "production_employee_local"
        ordering = ["rowid"]

    def __str__(self):
        return f"{self.first_name} {self.last_name1}"
