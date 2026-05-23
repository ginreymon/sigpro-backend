from django.db import models
from .audit_model import AuditModel


class AppSetting(AuditModel):

    class DataType(models.TextChoices):
        STRING = "STRING", "String"
        INTEGER = "INTEGER", "Integer"
        DECIMAL = "DECIMAL", "Decimal"
        BOOLEAN = "BOOLEAN", "Boolean"
        JSON = "JSON", "JSON"

    name = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=2000)
    data_type = models.CharField(
        max_length=10,
        choices=DataType.choices,
        default=DataType.STRING,
    )
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "core_app_setting"
        ordering = ["name"]
        verbose_name = "App Setting"
        verbose_name_plural = "App Settings"

    def __str__(self):
        return f"{self.name}: {self.value}"
