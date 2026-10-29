from apps.common.repositories.op_progress_repository import OpProgressRepository


class OpProgressService:
    repository = OpProgressRepository

    @classmethod
    def get_op_progress(cls, start_date: str, end_date: str, area_id: int | None = None) -> list[dict]:
        return cls.repository.get_op_progress(start_date, end_date, area_id)
