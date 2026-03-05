from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.group_view import GroupViewSet
from .views.permission_view import PermissionViewSet
from .views.user_view import UserViewSet

router = DefaultRouter()
router.register(r"role", GroupViewSet, basename="role")
router.register(r"permission", PermissionViewSet, basename="permission")
router.register(r"account", UserViewSet, basename="account")

urlpatterns = [
    path("", include(router.urls)),
]
