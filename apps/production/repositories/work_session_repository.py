from apps.people.models import EmployeeLocal
from apps.production.models import (
    Module,
    WorkBreak,
    WorkBreakRecord,
    WorkSession,
    WorkSessionActivity,
    WorkSessionActivityEmployee,
    WorkShiftSnapshot,
)


class WorkSessionRepository:
    """ORM access for work sessions."""

    @staticmethod
    def detail_queryset():
        return (
            WorkSession.objects.all()
            .select_related("work_shift", "user")
            .prefetch_related(
                "work_session_activities__module",
                "work_session_activities__employee_snapshots__employee",
                "work_session_activities__work_break_records",
                "work_session_activities__production_records",
            )
        )

    @classmethod
    def get_detail(cls, pk):
        return cls.detail_queryset().get(pk=pk)

    @classmethod
    def find_open_session_of(cls, user):
        return cls.detail_queryset().filter(is_closed=False, user=user).first()

    @classmethod
    def find_last_session_of(cls, user):
        return cls.detail_queryset().filter(user=user).order_by("-started_at", "-id").first()

    @staticmethod
    def lock_open_session_of(user):
        """Open session of the user, locked for the rest of the transaction."""
        return WorkSession.objects.select_for_update().filter(user=user, is_closed=False).first()

    @staticmethod
    def lock_by_id(pk):
        return WorkSession.objects.select_for_update().select_related("work_shift").get(pk=pk)

    @staticmethod
    def find_module_with_location(module_id):
        return Module.objects.select_related("location").filter(id=module_id).first()

    @staticmethod
    def create(**fields):
        return WorkSession.objects.create(**fields)

    @staticmethod
    def update(session, fields: dict):
        for attribute, value in fields.items():
            setattr(session, attribute, value)
        session.save()
        return session

    @staticmethod
    def find_shift_snapshot(work_session):
        return WorkShiftSnapshot.objects.filter(work_session=work_session).first()

    @staticmethod
    def create_shift_snapshot(**fields):
        return WorkShiftSnapshot.objects.create(**fields)

    @staticmethod
    def active_employee_ids(activity) -> set:
        return set(activity.employee_snapshots.values_list("employee_id", flat=True))

    @staticmethod
    def active_apprentice_ids(activity) -> set:
        return set(
            activity.employee_snapshots.filter(is_apprentice=True).values_list("employee_id", flat=True)
        )

    @staticmethod
    def replace_activity_employees(activity, employee_ids, apprentice_ids, minutes_per_hour, created_by):
        """Replaces the employee snapshot of `activity`."""
        apprentice_set = set(apprentice_ids or [])
        WorkSessionActivityEmployee.objects.filter(work_session_activity=activity).delete()
        WorkSessionActivityEmployee.objects.bulk_create([
            WorkSessionActivityEmployee(
                work_session_activity=activity,
                employee=employee,
                is_apprentice=employee.id in apprentice_set,
                worked_minutes_per_hour=minutes_per_hour.get(employee.id),
                created_by=created_by,
            )
            for employee in EmployeeLocal.objects.filter(id__in=employee_ids)
        ])


class WorkSessionActivityRepository:
    """ORM access for work session activities and their breaks."""

    @staticmethod
    def detail_queryset():
        return (
            WorkSessionActivity.objects.all()
            .select_related("module", "work_session")
            .prefetch_related("work_break_records", "production_records")
        )

    @staticmethod
    def find_work_break(pk):
        return WorkBreak.objects.filter(pk=pk).first()

    @staticmethod
    def save_break_record(record: WorkBreakRecord) -> WorkBreakRecord:
        record.save()
        return record
