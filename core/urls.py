from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.views.module_view import ModuleViewSet
from core.views.option_view import OptionViewSet
from core.views.menu_view import MenuViewSet
from core.views.group_option_view import GroupOptionViewSet
from core.views.app_setting_view import AppSettingViewSet
from core.views.home_view_view import HomeViewViewSet
from core.views.role_home_view_view import RoleHomeViewViewSet


router = DefaultRouter()
router.register(r"menu-modules", ModuleViewSet)
router.register(r"menu-options", OptionViewSet)
router.register(r"group-option", GroupOptionViewSet)
router.register(r"app-settings", AppSettingViewSet)
router.register(r"home-views", HomeViewViewSet)
router.register(r"role-home-views", RoleHomeViewViewSet)
router.register(r"", MenuViewSet, basename="menu")

urlpatterns = [
    path("", include(router.urls)),
]
