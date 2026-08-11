from core.models.home_view import HomeView
from core.serializers.audit_serializer import AuditSerializer


class HomeViewSerializer(AuditSerializer):

    class Meta:
        model = HomeView
        fields = "__all__"
