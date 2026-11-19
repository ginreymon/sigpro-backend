from core.views.base_model_view import BaseModelViewSet
from django.contrib.auth.models import Permission
from apps.user.serializers.permission_serializer import PermissionSerializer
from core import option_keys as opt


class PermissionViewSet(BaseModelViewSet):
    # Django permissions do not authorize the API (menu options do): read-only catalog.
    http_method_names = ["get", "head", "options"]
    read_options = (opt.ROLES,)

    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer