from django.db import models
from django.conf import settings
from apps.production.models.employee_local import EmployeeLocal
from apps.production.models.work_session_activity_employee import WorkSessionActivityEmployee
from apps.production.models.work_shift import WorkShift
from core.models.audit_model import TimeAuditModel, UserAuditModel
from django.utils import timezone
from django.db.models import Q


class WorkSession(TimeAuditModel, UserAuditModel):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="work_sessions"
    )

    work_shift = models.ForeignKey(
        WorkShift, on_delete=models.PROTECT, related_name="work_sessions"
    )   

    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    total_time = models.DurationField(null=True, blank=True)

    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ["started_at"]
        indexes = [
            models.Index(fields=["started_at"]),
            models.Index(fields=["user", "is_closed"]),          
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_closed=False),
                name="unique_active_session_per_user",
            )
        ]

    def get_active_activity(self):
        return (
            self.work_session_activities.filter(ended_at__isnull=True, is_active=True)
            .order_by("-started_at", "-id")
            .select_related("module")
            .first()
        )

    def close_all_open_records(self):
        from apps.production.models.production_record import ProductionRecord
        ProductionRecord.objects.filter(
            work_session_activity__work_session=self,
            end_time__isnull=True,
        ).update(end_time=timezone.now())

    def start_activity(self, module, employee_ids=None, created_by=None):
        self.close_all_open_records()

        activity = self.get_active_activity()
        if activity:
            activity.close()

        resolved_created_by = created_by or self.created_by

        activity = self.work_session_activities.create(
            module=module,
            created_by=resolved_created_by,
        )

        if employee_ids:
            employees = EmployeeLocal.objects.filter(id__in=employee_ids)

            activity.employee_snapshots.bulk_create(
                [
                    WorkSessionActivityEmployee(
                        work_session_activity=activity,
                        employee=emp,
                        created_by=resolved_created_by,
                    )
                    for emp in employees
                ]
            )

        return activity

    def continue_activity(self, employee_ids=None, created_by=None):
                
        last_activity = self.get_active_activity()

        if not last_activity:
            last_activity = (
                self.work_session_activities
                .order_by("-started_at")
                .first()
            )

        if not last_activity:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("No previous activity found to continue from")

        module = last_activity.module
        previous_employee_ids = list(
            last_activity.employee_snapshots
            .values_list("employee_id", flat=True)
        )

        resolved_employee_ids = employee_ids if employee_ids is not None else previous_employee_ids

        return self.start_activity(
            module=module,
            employee_ids=resolved_employee_ids,
            created_by=created_by,
        )

    def close_session(self):
        if self.is_closed:
            return

        if not self.started_at:
            raise ValueError("Session has no start time")

        activity = self.get_active_activity()
        if activity:
            activity.close()

        self.ended_at = timezone.now()
        self.total_time = self.ended_at - self.started_at
        self.is_closed = True

        self.save(update_fields=["ended_at", "total_time", "is_closed"])

    def save(self, *args, **kwargs):
        if self.started_at and self.ended_at and not self.is_closed:
            self.total_time = self.ended_at - self.started_at
            self.is_closed = True

        super().save(*args, **kwargs)
