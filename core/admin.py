from django.contrib import admin

from core.models import Module, Option, GroupOption, AppSetting, AppSettingDataType

admin.site.register(Module)
admin.site.register(Option)
admin.site.register(GroupOption)
admin.site.register(AppSettingDataType)


@admin.register(AppSetting)
class AppSettingAdmin(admin.ModelAdmin):
    list_display = ["name", "value", "data_type", "is_active", "created_by", "updated_by", "created_at", "updated_at"]
    list_filter = ["data_type", "is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]
