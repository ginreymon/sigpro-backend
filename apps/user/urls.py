from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.auth_view import AuthViewSet


router = DefaultRouter()
router.register(r"", AuthViewSet, basename="auth")


urlpatterns = [
    path("", include(router.urls)),
]
