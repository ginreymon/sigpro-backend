from core.models.home_view import HomeView
from core.serializers.home_view_serializer import HomeViewSerializer
from core.views.audit_model_view import AuditModelViewSet


class HomeViewViewSet(AuditModelViewSet):
    queryset = HomeView.objects.all()
    serializer_class = HomeViewSerializer
