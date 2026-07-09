from decimal import Decimal
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, F
from apps.production.models.production_record import ProductionRecord
from apps.production.models.work_session_activity import WorkSessionActivity
from apps.production.models.work_session_activity_employee import WorkSessionActivityEmployee
from core.serializers.audit_serializer import AuditSerializer


class ProductionRecordSerializer(AuditSerializer):
    server_now = serializers.SerializerMethodField()
    is_paused = serializers.SerializerMethodField()

    class Meta:
        model = ProductionRecord
        fields = "__all__"
        read_only_fields = ["start_time", "end_time", "server_now", "is_paused"]

    def get_server_now(self, obj):
        return timezone.now()

    def get_is_paused(self, obj):
        activity = self.context.get("activity")
        if activity is not None:
            return activity.is_paused
        return obj.work_session_activity.is_paused

    def _open_new_activity(self, activity):
        """
        Close all open records and current activity, open a new activity on the same
        module/session, and copy the employee snapshot. Returns the new activity.
        """
        if activity.work_session.is_closed:
            raise ValidationError("La sesión de trabajo está cerrada.")

        user = self.context["request"].user

        activity.close()

        new_activity = activity.work_session.work_session_activities.create(
            module=activity.module,
            created_by=user,
        )

        old_employees = activity.employee_snapshots.select_related("employee").all()
        WorkSessionActivityEmployee.objects.bulk_create([
            WorkSessionActivityEmployee(
                work_session_activity=new_activity,
                employee=rel.employee,
                created_by=rel.created_by,
                is_apprentice=rel.is_apprentice,
            )
            for rel in old_employees
        ])

        return new_activity

    @transaction.atomic
    def create(self, validated_data):
        missing = [f for f in ("op_number", "op_type") if not validated_data.get(f)]
        if missing:
            raise ValidationError({f: "Este campo es obligatorio." for f in missing})

        activity = (
            WorkSessionActivity.objects
            .select_for_update()
            .select_related("work_session")
            .get(pk=validated_data["work_session_activity"].pk)
        )
        validated_data["work_session_activity"] = activity

        if not activity.is_active:
            raise ValidationError("La actividad no está activa.")

        if activity.work_session.is_closed:
            raise ValidationError("La sesión de trabajo está cerrada.")

        last_record = activity.production_records.order_by("-start_time").first()

        if last_record is not None and last_record.sku_rowid != validated_data["sku_rowid"]:
            validated_data["work_session_activity"] = self._open_new_activity(activity)

        completed = Decimal(str(validated_data.get("completed_quantity") or 0))
        scrap = Decimal(str(validated_data.get("scrap_quantity") or 0))
        rejected = Decimal(str(validated_data.get("rejected_quantity") or 0))
        has_quantities = completed > 0 or scrap > 0 or rejected > 0

        if has_quantities:
            ordered = Decimal(str(validated_data["ordered_quantity"]))
            sku_rowid = validated_data["sku_rowid"]
            op_rowid = validated_data["op_rowid"]
            existing_sum = (
                ProductionRecord.objects.filter(sku_rowid=sku_rowid, op_rowid=op_rowid)
                .aggregate(total=Sum(F("completed_quantity") + F("scrap_quantity") + F("rejected_quantity")))
                ["total"] or Decimal("0")
            )
            new_total = existing_sum + completed + scrap + rejected
            if new_total > ordered:
                raise ValidationError({
                    "non_field_errors": (
                        f"La suma de cantidades ({new_total}) supera la cantidad ordenada ({ordered})."
                    )
                })

        validated_data["completed_quantity"] = completed
        validated_data["scrap_quantity"] = scrap
        validated_data["rejected_quantity"] = rejected

        instance = super().create(validated_data)
        instance.end_time = instance.start_time
        instance.save(update_fields=["end_time"])

        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        completed = Decimal(str(validated_data.get("completed_quantity") or 0))
        scrap = Decimal(str(validated_data.get("scrap_quantity") or 0))
        rejected = Decimal(str(validated_data.get("rejected_quantity") or 0))
        has_quantities = completed > 0 or scrap > 0 or rejected > 0

        if has_quantities:
            existing_sum = (
                ProductionRecord.objects.filter(sku_rowid=instance.sku_rowid, op_rowid=instance.op_rowid)
                .exclude(pk=instance.pk)
                .aggregate(total=Sum(F("completed_quantity") + F("scrap_quantity") + F("rejected_quantity")))
                ["total"] or Decimal("0")
            )
            new_total = existing_sum + completed + scrap + rejected
            if new_total > instance.ordered_quantity:
                raise ValidationError({
                    "non_field_errors": (
                        f"La suma de cantidades ({new_total}) supera la cantidad ordenada ({instance.ordered_quantity})."
                    )
                })

        instance.completed_quantity = completed
        instance.scrap_quantity = scrap
        instance.rejected_quantity = rejected
        instance.save(update_fields=["completed_quantity", "scrap_quantity", "rejected_quantity"])

        return instance
