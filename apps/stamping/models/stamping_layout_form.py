from django.db import models
from core.models import AuditModel


class StampingLayoutForm(AuditModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "stamping_stamping_layout_form"
        ordering = ['name']

    def __str__(self):
        return self.name
