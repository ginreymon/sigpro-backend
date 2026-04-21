from django.contrib import admin

# Register your models here.
from apps.production.models import (
    Module,
    EmployeeLocal,
    ModuleAssignee,
    ProductionRecord,
    WorkBreakRecord,
    WorkBreak,
    WorkCenterLocal,
    WorkSessionActivity,
    WorkSession,
    WorkShift,
    WorkSessionActivityEmployee,
)

admin.site.register([
    Module,
    EmployeeLocal,
    ModuleAssignee,
    ProductionRecord,
    WorkBreakRecord,
    WorkBreak,
    WorkCenterLocal,
    WorkSessionActivity,
    WorkSession,
    WorkShift,
    WorkSessionActivityEmployee,
])