from core.models.home_view import HomeView
from core.serializers.home_view_serializer import HomeViewSerializer
from core.views.audit_model_view import AuditModelViewSet
from core import option_keys as opt


class HomeViewViewSet(AuditModelViewSet):
    write_options = (opt.ROLES,)
    read_options = (opt.ROLES,)

    queryset = HomeView.objects.all()
    serializer_class = HomeViewSerializer
