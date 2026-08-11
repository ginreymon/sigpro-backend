from django.db import models
from .audit_model import AuditModel


class HomeView(AuditModel):

    key = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "core_home_view"
        ordering = ["label"]
        verbose_name = "Home View"
        verbose_name_plural = "Home Views"

    def __str__(self):
        return self.label
