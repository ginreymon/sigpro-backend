from django.core.exceptions import ValidationError
from django.db import models
from .audit_model import AuditModel
from .app_setting_data_type import AppSettingDataType


class AppSetting(AuditModel):

    name = models.CharField(max_length=100, unique=True)
    key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    value = models.CharField(max_length=2000)
    data_type = models.ForeignKey(
        AppSettingDataType,
        on_delete=models.PROTECT,
        related_name="app_settings",
    )
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "core_app_setting"
        ordering = ["name"]
        verbose_name = "App Setting"
        verbose_name_plural = "App Settings"

    def clean(self):
        qs = AppSetting.objects.exclude(pk=self.pk)
        if self.key:
            if qs.filter(name=self.key).exists():
                raise ValidationError({'key': f"'{self.key}' ya existe como nombre."})
            if qs.filter(key=self.name).exists():
                raise ValidationError({'name': f"'{self.name}' ya existe como clave."})

    def __str__(self):
        return f"{self.name}: {self.value}"
