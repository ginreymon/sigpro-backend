from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/core/", include("core.urls")),
    path("api/v1/user/", include("apps.user.user_urls")),
    path("api/v1/auth/", include("apps.user.auth_urls")),
    path("api/v1/production/", include("apps.production.urls")),
]
