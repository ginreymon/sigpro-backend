from core.models.role_home_view import RoleHomeView
from core.serializers.role_home_view_serializer import RoleHomeViewSerializer
from core.views.audit_model_view import AuditModelViewSet


class RoleHomeViewViewSet(AuditModelViewSet):
    queryset = RoleHomeView.objects.select_related('group', 'home_view').all()
    serializer_class = RoleHomeViewSerializer
