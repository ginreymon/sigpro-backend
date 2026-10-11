from rest_framework.exceptions import ValidationError
from apps.production.models import ModuleAssignee, WorkSessionActivity, EmployeeContinuousWorkLimit
from apps.people.models import EmployeeLocal
from apps.production.models.work_session_activity_employee import WorkSessionActivityEmployee


def validate_employees_active(employee_ids):
    if not employee_ids:
        return

    valid_ids = set(
        EmployeeLocal.objects.filter(
            id__in=employee_ids, is_deleted=False, is_active=True
        ).values_list("id", flat=True)
    )
    invalid_ids = set(employee_ids) - valid_ids

    if invalid_ids:
        raise ValidationError(
            f"Empleado(s) inactivo(s) o eliminado(s): {', '.join(str(i) for i in sorted(invalid_ids))}"
        )


def validate_module_conflict(module, current_session=None):
    qs = WorkSessionActivity.objects.filter(
        module=module,
        is_active=True,
        ended_at__isnull=True,
        work_session__is_closed=False,
    ).select_related("work_session__user__employee_link__employee_local")
    if current_session is not None:
        qs = qs.exclude(work_session=current_session)

    conflict = qs.first()
    if conflict:
        raise ValidationError(
            f"El módulo '{module.name}' ya está en uso por {_holder_name(conflict.work_session.user)}. "
            "Espera a que finalice su jornada o elige otro módulo."
        )


def _holder_name(user):
    employee_link = getattr(user, "employee_link", None)
    if employee_link:
        employee = employee_link.employee_local
        return f"{employee.first_name} {employee.last_name1}"
    return user.get_full_name() or user.username


def validate_employee_conflicts(employee_ids, current_activity):
    conflicts = (
        WorkSessionActivityEmployee.objects.filter(
            employee_id__in=employee_ids,
            work_session_activity__is_active=True,
            work_session_activity__ended_at__isnull=True,
            work_session_activity__work_session__is_closed=False,
        )
        .exclude(work_session_activity=current_activity)
        .select_related("employee", "work_session_activity__module")
    )

    if not conflicts.exists():
        return

    errors = [
        f"{c.employee.first_name} {c.employee.last_name1} ya está asignado al módulo "
        f"'{c.work_session_activity.module.name}'"
        for c in conflicts
    ]
    raise ValidationError(errors)


def get_continuous_work_minutes_map(employee_ids):
    return dict(
        EmployeeContinuousWorkLimit.objects.filter(
            employee_id__in=employee_ids, is_active=True
        ).values_list("employee_id", "continuous_work_minutes")
    )


def sync_module_assignees(module, created_by):
    active_employee_ids = set(
        WorkSessionActivityEmployee.objects.filter(
            work_session_activity__module=module,
            work_session_activity__is_active=True,
            work_session_activity__ended_at__isnull=True,
            work_session_activity__work_session__is_closed=False,
        ).values_list("employee_id", flat=True)
    )

    current_assignee_ids = set(
        ModuleAssignee.objects.filter(module=module).values_list("employee_id", flat=True)
    )

    to_add = active_employee_ids - current_assignee_ids
    to_remove = current_assignee_ids - active_employee_ids

    if to_remove:
        ModuleAssignee.objects.filter(module=module, employee_id__in=to_remove).delete()

    ModuleAssignee.objects.bulk_create([
        ModuleAssignee(module=module, employee_id=emp_id, created_by=created_by)
        for emp_id in to_add
    ])
