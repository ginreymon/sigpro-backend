from django.contrib import admin

from apps.common.admin_mixins import AuditReadOnlyMixin, ReadOnlyAdminMixin
from apps.integration.models import TepDetail, TepDetailRecord, TepSubmission, WorkCenterProductionArea


@admin.register(TepSubmission)
class TepSubmissionAdmin(ReadOnlyAdminMixin, AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["id", "document_number", "date", "work_center_id", "employee_id", "shift", "status", "error_type", "sent_at"]
    list_filter = ["status", "error_type", "date", "shift"]
    search_fields = ["document_number", "employee_id", "work_center_id"]
    ordering = ["-id"]
    list_per_page = 50


@admin.register(TepDetail)
class TepDetailAdmin(ReadOnlyAdminMixin, AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["id", "submission", "op_document_number", "item_reference", "completed_quantity", "start_time", "end_time"]
    list_filter = ["time_mode", "operation_completed"]
    search_fields = ["op_document_number", "item_reference", "barcode"]
    raw_id_fields = ["submission"]
    ordering = ["-id"]
    list_per_page = 50


@admin.register(TepDetailRecord)
class TepDetailRecordAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["detail", "origin_id", "record_id"]
    raw_id_fields = ["detail"]
    ordering = ["-id"]
    list_per_page = 50


@admin.register(WorkCenterProductionArea)
class WorkCenterProductionAreaAdmin(admin.ModelAdmin):
    list_display = ["work_center", "production_area", "is_active"]
    list_filter = ["is_active", "production_area"]
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 50
