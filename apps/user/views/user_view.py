from django.contrib.auth.models import User
from core.permissions import OptionWritePermission
from core.views.base_model_view import BaseModelViewSet
from apps.user.serializers.user_update_serializer import UserUpdateSerializer
from rest_framework.response import Response
from rest_framework import status


class UserViewSet(BaseModelViewSet):
    permission_classes = [OptionWritePermission]
    option_url = "users"
    queryset = User.objects.select_related("employee_link__employee_local").prefetch_related("groups").order_by("username")
    search_fields = [
        "username",
        "email",
        "employee_link__employee_local__first_name",
        "employee_link__employee_local__last_name1",
        "employee_link__employee_local__id_number",
    ]
    serializer_class = UserUpdateSerializer

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)
