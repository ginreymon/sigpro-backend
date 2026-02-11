from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.module_view import ModuleViewSet
from .views.option_view import OptionViewSet
from .views.menu_view import MenuViewSet


router = DefaultRouter()
router.register(r"menu-modules", ModuleViewSet)
router.register(r"menu-options", OptionViewSet)
router.register(r"", MenuViewSet, basename="menu")

urlpatterns = [
    path("", include(router.urls)),
]
