from apps.production.models import Module, WorkBreak, WorkBreakRecord, WorkSession, WorkSessionActivity


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
