from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.models.app_setting import AppSetting
from core.serializers.app_setting_serializer import AppSettingSerializer
from core.views.audit_model_view import AuditModelViewSet


class AppSettingViewSet(AuditModelViewSet):
    queryset = AppSetting.objects.all()
    serializer_class = AppSettingSerializer

    @action(detail=False, methods=['get'], url_path='values', permission_classes=[IsAuthenticated])
    def values(self, request):
        names    = request.query_params.get('names', '')
        ids      = request.query_params.get('ids', '')
        keys     = request.query_params.get('keys', '')
        all_keys = request.query_params.get('all_keys', '')

        qs = AppSetting.objects.filter(is_active=True)

        if names:
            qs = qs.filter(name__in=[n.strip() for n in names.split(',')])
        elif ids:
            qs = qs.filter(id__in=[i.strip() for i in ids.split(',')])
        elif keys:
            qs = qs.filter(key__in=[k.strip() for k in keys.split(',')])
        elif all_keys:
            qs = qs.filter(key__isnull=False)
        else:
            return Response([])

        return Response(list(qs.values('id', 'name', 'key', 'value')))
