from django.contrib import admin

# Register your models here.
from apps.production.models import (
    Module,
    ModuleAssignee,
    ProductionRecord,
    WorkBreakRecord,
    ModuleDowntime,
    WorkBreak,
    WorkCenterLocal,
    WorkSessionActivity,
    WorkSession,
    WorkShift,
    WorkSessionActivityEmployee,
    ProductionArea,
)
from apps.people.models import EmployeeLocal

admin.site.register([
    Module,
    EmployeeLocal,
    ModuleAssignee,
    ProductionRecord,
    WorkBreakRecord,
    ModuleDowntime,
    WorkBreak,
    WorkCenterLocal,
    WorkSessionActivity,
    WorkSession,
    WorkShift,
    WorkSessionActivityEmployee,
    ProductionArea
])

from apps.common.admin_mixins import AuditReadOnlyMixin, ReadOnlyAdminMixin  # noqa: E402
from apps.production.models import (  # noqa: E402
    EmployeeContinuousWorkLimit,
    ModuleUserAccount,
    ProductionAreaCostCenter,
    ReferenceSam,
    SkuItemLocal,
    WorkShiftSnapshot,
)


@admin.register(ProductionAreaCostCenter)
class ProductionAreaCostCenterAdmin(AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["production_area", "cost_center_rowid", "is_active"]
    list_filter = ["is_active", "production_area"]
    search_fields = ["cost_center_rowid"]
    list_per_page = 50


@admin.register(ModuleUserAccount)
class ModuleUserAccountAdmin(AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["module", "user", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["user__username"]
    raw_id_fields = ["module", "user"]
    list_per_page = 50


@admin.register(EmployeeContinuousWorkLimit)
class EmployeeContinuousWorkLimitAdmin(AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["employee", "continuous_work_minutes", "description", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["description"]
    raw_id_fields = ["employee"]
    list_per_page = 50


@admin.register(WorkShiftSnapshot)
class WorkShiftSnapshotAdmin(ReadOnlyAdminMixin, AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["work_session", "work_shift", "location", "start_time", "end_time"]
    raw_id_fields = ["work_session", "work_shift", "location"]
    ordering = ["-id"]
    list_per_page = 50


@admin.register(ReferenceSam)
class ReferenceSamAdmin(AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["rowid_item", "sam", "is_active", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["rowid_item"]
    ordering = ["rowid_item"]
    list_per_page = 50


@admin.register(SkuItemLocal)
class SkuItemLocalAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Local copy of SIESA items: synced, not edited by hand."""

    list_display = ["reference", "description", "size", "color", "barcode", "status", "is_active"]
    list_filter = ["is_active", "status", "brand", "line"]
    search_fields = ["reference", "barcode", "description"]
    ordering = ["reference"]
    list_per_page = 50
