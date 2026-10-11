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