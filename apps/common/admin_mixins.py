class AuditReadOnlyMixin:
    """Audit columns are filled by the app, never by hand."""

    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]


class ReadOnlyAdminMixin:
    """Derived/intermediate data: browse only, no add/change/delete."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
