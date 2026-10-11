from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/core/", include("core.urls")),
    path("api/v1/user/", include("apps.user.user_urls")),
    path("api/v1/auth/", include("apps.user.auth_urls")),
    path("api/v1/production/", include("apps.production.urls")),
    path("api/v1/stamping/", include("apps.stamping.urls")),
    path("api/v1/integration/", include("apps.integration.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

handler404 = "core.exceptions.api_not_found"
handler500 = "core.exceptions.api_server_error"
