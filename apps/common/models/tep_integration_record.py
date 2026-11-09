from django.db import models
from core.models.audit_model import TimeAuditModel, UserAuditModel


class TepIntegrationRecord(TimeAuditModel, UserAuditModel):
    """Common TEP state of the records of a production order (ProductionRecord
    and StampingRecord). The work data lives in
    `apps.common.models.op_work_record.OpWorkRecord`.
    """

    # TEP submission (integration) the record is associated with; null until it
    # has been submitted (it also goes back to null on every save()). Referenced
    # by string so that `common` does not import `integration`.
    tep_submission = models.ForeignKey(
        "integration.TepSubmission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tep_%(class)ss",
    )

    # Whether the record has already been processed in a TEP submission: becomes
    # True when `tep_submission` is assigned (see register_submission) and goes
    # back to False on every save() (create or update).
    tep_processed = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Creating or modifying a record leaves it pending for TEP: no submission
        # and not processed. register_submission marks them with
        # QuerySet.update(), which does not go through here.
        self.tep_submission = None
        self.tep_processed = False
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = {*update_fields, "tep_submission", "tep_processed"}
        super().save(*args, **kwargs)
