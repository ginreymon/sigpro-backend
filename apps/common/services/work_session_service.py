from apps.common.repositories.work_session_repository import WorkSessionRepository


class WorkSessionService:
    repository = WorkSessionRepository

    @classmethod
    def list_work_sessions(cls, **filters) -> tuple[int, list[dict]]:
        """Returns (total count, page rows). The SP repeats `total_count` in every row."""
        rows = cls.repository.list_work_sessions(**filters)
        count = rows[0]["total_count"] if rows else 0
        for row in rows:
            row.pop("total_count", None)
        return count, rows
