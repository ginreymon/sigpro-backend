from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/core/", include("core.urls")),
    path("api/v1/user/", include("apps.user.user_urls")),
    path("api/v1/auth/", include("apps.user.auth_urls")),
    path("api/v1/production/", include("apps.production.urls")),
    path("api/v1/stamping/", include("apps.stamping.urls")),
    path("api/v1/integration/", include("apps.integration.urls")),
]

handler404 = "core.exceptions.api_not_found"
handler500 = "core.exceptions.api_server_error"
