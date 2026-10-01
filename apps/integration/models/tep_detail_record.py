from django.db import models

from core.models import TimeAuditModel

from .tep_detail import TepDetail


class TepDetailRecord(TimeAuditModel):
    """Registro de producción o estampación que respalda un `TepDetail`.

    Una fila por id de `register_ids` del request: `record_id` es el id de
    `ProductionRecord` (origin_id=1) o `StampingRecord` (origin_id=2). Permite
    validar que un registro no se envíe dos veces a SIESA.
    """

    detail = models.ForeignKey(TepDetail, on_delete=models.CASCADE, related_name="records")
    origin_id = models.SmallIntegerField()
    record_id = models.BigIntegerField()

    class Meta:
        db_table = "integration_tep_detail_record"
        indexes = [models.Index(fields=["origin_id", "record_id"])]

    def __str__(self):
        return f"origin {self.origin_id} / record {self.record_id}"
