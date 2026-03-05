from core.views.base_model_view import BaseModelViewSet
from django.contrib.auth.models import Permission
from apps.user.serializers.permission_serializer import PermissionSerializer


class PermissionViewSet(BaseModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer