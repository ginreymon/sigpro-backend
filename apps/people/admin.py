from django.contrib import admin

from apps.common.admin_mixins import AuditReadOnlyMixin
from apps.people.models import AuthUserEmployee


@admin.register(AuthUserEmployee)
class AuthUserEmployeeAdmin(AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["auth_user", "employee_local", "created_at"]
    search_fields = ["auth_user__username"]
    raw_id_fields = ["auth_user", "employee_local"]
    ordering = ["-created_at"]
    list_per_page = 50
