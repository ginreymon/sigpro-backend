from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.views.module_view import ModuleViewSet
from core.views.option_view import OptionViewSet
from core.views.menu_view import MenuViewSet
from core.views.group_option_view import GroupOptionViewSet


router = DefaultRouter()
router.register(r"menu-modules", ModuleViewSet)
router.register(r"menu-options", OptionViewSet)
router.register(r"group-option", GroupOptionViewSet)
router.register(r"", MenuViewSet, basename="menu")

urlpatterns = [
    path("", include(router.urls)),
]
