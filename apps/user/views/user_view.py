from django.contrib.auth.models import User
from core.views.base_model_view import BaseModelViewSet
from apps.user.serializers.user_update_serializer import UserUpdateSerializer
from rest_framework.response import Response
from rest_framework import status


class UserViewSet(BaseModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)
