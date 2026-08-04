from django.db import models
from .audit_model import AuditModel


class AppSettingDataType(AuditModel):

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)   

    class Meta:
        db_table = "core_app_setting_data_type"
        ordering = ["code"]
       
    def __str__(self):
        return self.name
