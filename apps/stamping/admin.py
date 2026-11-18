from django.contrib import admin

from apps.common.admin_mixins import AuditReadOnlyMixin, ReadOnlyAdminMixin
from apps.stamping.models import (
    AdditionalStampingTime,
    AdditionalStampingTimeStep,
    AuditRecord,
    AuditRecordDetail,
    StampingFabricType,
    StampingLayoutForm,
    StampingLocation,
    StampingMachine,
    StampingMachineType,
    StampingModuleMachine,
    StampingPiece,
    StampingProcess,
    StampingRecord,
    StampingRecordAdditionalTime,
    StampingReferenceSam,
    StampingStampTypeDescription,
    StampingTechnique,
)


class NameCatalogAdmin(AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["name", "is_active", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["name"]
    ordering = ["name"]
    list_per_page = 50


for _model in (
    StampingMachineType,
    StampingPiece,
    StampingLocation,
    StampingStampTypeDescription,
    StampingFabricType,
    StampingTechnique,
    StampingLayoutForm,
):
    admin.site.register(_model, NameCatalogAdmin)


@admin.register(StampingMachine)
class StampingMachineAdmin(AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["name", "machine_type", "is_active"]
    list_filter = ["is_active", "machine_type"]
    search_fields = ["name"]
    ordering = ["name"]
    list_per_page = 50


@admin.register(StampingProcess)
class StampingProcessAdmin(AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["name", "machine", "is_active"]
    list_filter = ["is_active", "machine"]
    search_fields = ["name"]
    ordering = ["name"]
    list_per_page = 50


@admin.register(StampingModuleMachine)
class StampingModuleMachineAdmin(AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["module", "machine", "uses_processes_search", "is_active"]
    list_filter = ["is_active", "uses_processes_search", "machine"]
    search_fields = ["machine__name"]
    raw_id_fields = ["module"]
    list_per_page = 50


@admin.register(AdditionalStampingTime)
class AdditionalStampingTimeAdmin(AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["code_number", "engineering_code", "process", "machine", "machine_type", "standard_time_minutes", "is_active"]
    list_filter = ["is_active", "machine_type", "machine"]
    search_fields = ["engineering_code", "process"]
    ordering = ["code_number"]
    list_per_page = 50


@admin.register(AdditionalStampingTimeStep)
class AdditionalStampingTimeStepAdmin(ReadOnlyAdminMixin, AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["additional_stamping_time", "order", "description", "standard_time_minutes", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["description", "additional_stamping_time__engineering_code"]
    list_select_related = ["additional_stamping_time"]
    list_per_page = 50


@admin.register(StampingReferenceSam)
class StampingReferenceSamAdmin(AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["reference_code", "rowid_item", "machine_type", "piece", "technique", "fabric_type", "sam", "is_active"]
    list_filter = ["is_active", "machine_type", "technique", "fabric_type", "layout_form"]
    search_fields = ["reference_code"]
    list_select_related = ["machine_type", "piece", "technique", "fabric_type"]
    ordering = ["reference_code"]
    list_per_page = 50


@admin.register(StampingRecord)
class StampingRecordAdmin(AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["id", "op_number", "op_type", "ordered_quantity", "completed_quantity", "start_time", "end_time", "tep_processed"]
    list_filter = ["tep_processed", "op_type", "start_time"]
    search_fields = ["op_number"]
    raw_id_fields = ["tep_submission", "work_session_activity", "stamping_reference_sam"]
    ordering = ["-id"]
    list_per_page = 50


@admin.register(StampingRecordAdditionalTime)
class StampingRecordAdditionalTimeAdmin(ReadOnlyAdminMixin, AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["stamping_record", "additional_stamping_time", "count", "standard_time_minutes"]
    search_fields = ["stamping_record__op_number"]
    raw_id_fields = ["stamping_record", "additional_stamping_time"]
    ordering = ["-id"]
    list_per_page = 50


@admin.register(AuditRecord)
class AuditRecordAdmin(AuditReadOnlyMixin, admin.ModelAdmin):
    list_display = ["op_number", "op_type", "total_ordered_quantity", "is_audited", "updated_at"]
    list_filter = ["is_audited", "op_type"]
    search_fields = ["op_number"]
    ordering = ["-id"]
    list_per_page = 50


@admin.register(AuditRecordDetail)
class AuditRecordDetailAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["audit_record", "color", "ordered_quantity", "audited_quantity"]
    search_fields = ["audit_record__op_number", "color"]
    raw_id_fields = ["audit_record"]
    ordering = ["-id"]
    list_per_page = 50
