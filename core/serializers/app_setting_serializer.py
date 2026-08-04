from rest_framework import serializers
from core.models.app_setting import AppSetting
from core.serializers.audit_serializer import AuditSerializer


class AppSettingSerializer(AuditSerializer):
    data_type_code = serializers.CharField(source='data_type.code', read_only=True)

    class Meta:
        model = AppSetting
        fields = "__all__"
