from core.models.role_home_view import RoleHomeView
from core.serializers.role_home_view_serializer import RoleHomeViewSerializer
from core.views.audit_model_view import AuditModelViewSet
from core import option_keys as opt


class RoleHomeViewViewSet(AuditModelViewSet):
    write_options = (opt.ROLES,)
    read_options = (opt.ROLES,)

    queryset = RoleHomeView.objects.select_related('group', 'home_view').all()
    serializer_class = RoleHomeViewSerializer
