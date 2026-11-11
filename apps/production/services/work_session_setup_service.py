from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.production.repositories.work_session_repository import WorkSessionRepository
from apps.production.services.employee_assignment_service import (
    get_continuous_work_minutes_map,
    sync_module_assignees,
    validate_employee_conflicts,
    validate_employees_active,
    validate_module_conflict,
)


def snapshot_shift(work_session, work_shift, audit_user) -> None:
    """
    Freezes the shift hours/location when the session is opened or its shift
    changes — if WorkShift is edited later, this historical record must not be
    affected. It is updated in place (no second snapshot) when one exists.
    """
    snapshot = WorkSessionRepository.find_shift_snapshot(work_session)

    if snapshot:
        snapshot.work_shift = work_shift
        snapshot.location = work_shift.location
        snapshot.start_time = work_shift.start_time
        snapshot.end_time = work_shift.end_time
        snapshot.updated_by = audit_user
        snapshot.save(update_fields=["work_shift", "location", "start_time", "end_time", "updated_by"])
    else:
        WorkSessionRepository.create_shift_snapshot(
            work_session=work_session,
            work_shift=work_shift,
            location=work_shift.location,
            start_time=work_shift.start_time,
            end_time=work_shift.end_time,
            created_by=audit_user,
            updated_by=audit_user,
        )


def assign_employees(work_session, employee_ids, activity=None, apprentice_ids=None) -> None:
    """Validates and stores the employees of an activity (the session's active
    one by default) and keeps the module assignees in sync."""
    if not activity:
        activity = work_session.get_active_activity()

    if not activity:
        raise ValidationError("No se encontró una actividad activa.")

    created_by = getattr(work_session, "updated_by", None) or work_session.created_by

    validate_employees_active(employee_ids)
    validate_employee_conflicts(employee_ids, activity)
    WorkSessionRepository.replace_activity_employees(
        activity,
        employee_ids,
        apprentice_ids,
        get_continuous_work_minutes_map(employee_ids),
        created_by,
    )
    sync_module_assignees(activity.module, created_by)


def create_session(validated_data: dict):
    """
    Creates a work session from the serializer's validated data, together with its
    shift snapshot and, when a module is given, its first activity and employees.
    """
    employee_ids = validated_data.pop("employee_ids", [])
    apprentice_ids = validated_data.pop("apprentice_ids", [])
    module = validated_data.pop("module_id", None)

    with transaction.atomic():
        work_session = WorkSessionRepository.create(**validated_data)

        snapshot_shift(work_session, work_session.work_shift, validated_data.get("created_by"))

        activity = None

        if module:
            validate_module_conflict(module)
            activity = work_session.start_activity(module)

        if employee_ids:
            if not activity:
                raise ValidationError("No se pueden asignar empleados sin un módulo.")

            assign_employees(work_session, employee_ids, activity, apprentice_ids)

        return work_session


def update_session(instance, validated_data: dict):
    """
    Updates a work session. A change of module, shift, employees or apprentices
    snapshots the new shift (when it changed) and opens a new activity for the
    module with the resulting employees.
    """
    employee_ids = validated_data.pop("employee_ids", None)
    apprentice_ids = validated_data.pop("apprentice_ids", None)
    module = validated_data.pop("module_id", None)

    with transaction.atomic():
        # Capture current state before any changes
        current_activity = instance.get_active_activity()
        current_module = current_activity.module if current_activity else None
        current_employee_ids = (
            WorkSessionRepository.active_employee_ids(current_activity) if current_activity else set()
        )
        current_apprentice_ids = (
            WorkSessionRepository.active_apprentice_ids(current_activity) if current_activity else set()
        )

        new_work_shift = validated_data.get("work_shift")

        module_changed = module is not None and module != current_module
        work_shift_changed = new_work_shift is not None and new_work_shift != instance.work_shift
        employees_changed = employee_ids is not None and set(employee_ids) != current_employee_ids
        apprentice_changed = apprentice_ids is not None and set(apprentice_ids) != current_apprentice_ids

        any_field_changed = module_changed or work_shift_changed or employees_changed or apprentice_changed

        instance = WorkSessionRepository.update(instance, validated_data)

        # An explicit empty employee list leaves the activity without staff: close the
        # session through the usual close_session (it also closes the active activity).
        if employee_ids is not None and not employee_ids and current_activity:
            instance.close_session()
            return instance

        if work_shift_changed:
            snapshot_shift(instance, new_work_shift, validated_data.get("updated_by"))

        if any_field_changed:
            target_module = module or current_module
            if not target_module:
                return instance

            if module_changed:
                validate_module_conflict(target_module, current_session=instance)

            activity = instance.start_activity(target_module)
            effective_ids = list(employee_ids) if employee_ids is not None else list(current_employee_ids)
            effective_apprentice_ids = (
                list(apprentice_ids) if apprentice_ids is not None else list(current_apprentice_ids)
            )
            assign_employees(instance, effective_ids, activity, effective_apprentice_ids)

        return instance
