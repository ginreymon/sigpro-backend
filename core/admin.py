from django.contrib import admin

from core.models import Module, Option, GroupOption, AppSetting, AppSettingDataType, HomeView, RoleHomeView

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


@admin.register(HomeView)
class HomeViewAdmin(admin.ModelAdmin):
    list_display = ["key", "label", "is_active", "created_by", "updated_by", "created_at", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["key", "label"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]


@admin.register(RoleHomeView)
class RoleHomeViewAdmin(admin.ModelAdmin):
    list_display = ["group", "home_view", "is_active", "created_by", "updated_by", "created_at", "updated_at"]
    list_filter = ["is_active", "home_view"]
    search_fields = ["group__name", "home_view__key"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]
