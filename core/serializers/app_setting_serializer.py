from core.models.app_setting import AppSetting
from core.serializers.audit_serializer import AuditSerializer


class AppSettingSerializer(AuditSerializer):

    class Meta:
        model = AppSetting
        fields = "__all__"
