from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.group_view import GroupViewSet
from .views.permission_view import PermissionViewSet
from .views.user_view import UserViewSet
from .views.employee_directory_view import EmployeeDirectoryViewSet

router = DefaultRouter()
router.register(r"role", GroupViewSet, basename="role")
router.register(r"permission", PermissionViewSet, basename="permission")
router.register(r"account", UserViewSet, basename="account")
router.register(r"employee-directory", EmployeeDirectoryViewSet, basename="employee-directory")

urlpatterns = [
    path("", include(router.urls)),
]
