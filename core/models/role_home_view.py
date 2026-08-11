from django.db import models
from django.contrib.auth.models import Group
from .audit_model import AuditModel
from .home_view import HomeView


class RoleHomeView(AuditModel):

    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="home_view_link")
    home_view = models.ForeignKey(HomeView, on_delete=models.PROTECT, related_name="role_links")

    class Meta:
        db_table = "core_role_home_view"
        ordering = ["group__name"]
        verbose_name = "Role Home View"
        verbose_name_plural = "Role Home Views"

    def __str__(self):
        return f"{self.group.name} -> {self.home_view.key}"
