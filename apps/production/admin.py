from django.contrib import admin

# Register your models here.
from apps.production.models import (
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
    ProductionArea,
)

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