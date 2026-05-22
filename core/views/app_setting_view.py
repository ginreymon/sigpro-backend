from core.models.app_setting import AppSetting
from core.serializers.app_setting_serializer import AppSettingSerializer
from core.views.audit_model_view import AuditModelViewSet


class AppSettingViewSet(AuditModelViewSet):
    queryset = AppSetting.objects.all()
    serializer_class = AppSettingSerializer
