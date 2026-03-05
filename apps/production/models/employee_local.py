from django.db import models
from core.models import TimeAuditModel, ActiveModel
from core.models import LocalBaseModel


class EmployeeLocal(TimeAuditModel, ActiveModel, LocalBaseModel):

    rowid = models.BigIntegerField(unique=True)

    first_name = models.CharField(max_length=255)
    last_name1 = models.CharField(max_length=255)
    last_name2 = models.CharField(max_length=255, blank=True, null=True)
    id_number = models.CharField(max_length=50, unique=True)

    @property
    def has_account(self):
        return hasattr(self, "user_link")

    @property
    def username(self):
        if self.has_account:
            return self.user_link.django_user.username
        return None

    @property
    def user_id(self):
        if self.has_account:
            return self.user_link.django_user.id
        return None

    @property
    def is_account_active(self):
        if self.has_account:
            return self.user_link.django_user.is_active
        return False
    
    @property
    def groups(self):       
        if self.has_account:
            return list(self.user_link.django_user.groups.values("id", "name"))
        return []

    class Meta:
        ordering = ["rowid"]

    def __str__(self):
        return f"{self.first_name} {self.last_name1}"
