from django.db import models
from django.utils import timezone
from core.models.audit_model import TimeAuditModel, UserAuditModel


class OpRecord(TimeAuditModel, UserAuditModel):
    """Campos y comportamiento comunes de los registros de una OP
    (ProductionRecord y StampingRecord).

    `work_session_activity` no se declara aquí: cada registro usa un
    `related_name` propio (production_records / stamping_records).
    """

    op_rowid = models.BigIntegerField(null=True, blank=True)
    op_number = models.IntegerField(null=True, blank=True)
    op_type = models.CharField(max_length=10, null=True, blank=True)

    ordered_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    completed_quantity = models.DecimalField(max_digits=10, decimal_places=2)

    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    # Envío TEP (integration) al que quedó asociado el registro; null mientras
    # no se haya enviado (también vuelve a null en cada save()). Referencia por texto para no importar `integration`
    # desde `production` (evita un ciclo de importaciones).
    tep_submission = models.ForeignKey(
        "integration.TepSubmission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tep_%(class)ss",
    )

    # Indica si el registro ya fue procesado en un envío TEP: pasa a True
    # cuando se le asigna `tep_submission` (ver register_submission) y vuelve a
    # False en cada save() (alta o modificación).
    tep_processed = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Crear o modificar un registro lo deja pendiente de TEP: sin envío y sin
        # procesar. register_submission los marca con QuerySet.update(), que no
        # pasa por aquí.
        self.tep_submission = None
        self.tep_processed = False
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = {*update_fields, "tep_submission", "tep_processed"}
        super().save(*args, **kwargs)

    def close(self):
        if self.end_time:
            return
        self.end_time = timezone.now()
        self.save(update_fields=["end_time"])
