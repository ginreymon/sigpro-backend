from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from apps.production.models.production_record import ProductionRecord
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
        return obj.work_session_activity.is_paused

    def _open_new_activity(self, activity):
        """
        Close all open records and current activity, open a new activity on the same
        module/session, and copy the employee snapshot. Returns the new activity.
        """
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
            )
            for rel in old_employees
        ])

        return new_activity

    @transaction.atomic
    def create(self, validated_data):
        missing = [f for f in ("op_number", "op_type") if not validated_data.get(f)]
        if missing:
            raise ValidationError({f: "This field is required." for f in missing})

        activity = validated_data["work_session_activity"]
        last_record = activity.production_records.order_by("-start_time").first()

        if last_record is not None and last_record.sku_rowid != validated_data["sku_rowid"]:
            validated_data["work_session_activity"] = self._open_new_activity(activity)

        validated_data["completed_quantity"] = 0
        validated_data["scrap_quantity"] = 0
        validated_data["rejected_quantity"] = 0
        return super().create(validated_data)

    def _rotate_activity(self, instance, validated_data):
        """
        Close current record and activity, open new activity (same module)
        with new record carrying updated sku/op values and zero production quantities.
        Employees are copied from the previous activity snapshot.
        """
        user = self.context["request"].user
        new_activity = self._open_new_activity(instance.work_session_activity)

        new_record = ProductionRecord.objects.create(
            work_session_activity=new_activity,
            sku_rowid=validated_data.get("sku_rowid", instance.sku_rowid),
            op_rowid=validated_data.get("op_rowid", instance.op_rowid),
            op_number=validated_data.get("op_number", instance.op_number),
            op_type=validated_data.get("op_type", instance.op_type),
            ordered_quantity=validated_data["ordered_quantity"],
            planned_quantity=validated_data["planned_quantity"],
            completed_quantity=0,
            scrap_quantity=0,
            rejected_quantity=0,
            created_by=user,
        )
        return new_record

    @transaction.atomic
    def update(self, instance, validated_data):
        sku_changed = (
            "sku_rowid" in validated_data
            and validated_data["sku_rowid"] != instance.sku_rowid
        )
        op_changed = (
            "op_rowid" in validated_data
            and validated_data["op_rowid"] != instance.op_rowid
        )

        if sku_changed or op_changed:
            missing = [f for f in ("ordered_quantity", "planned_quantity") if f not in validated_data]
            if missing:
                raise ValidationError({f: "Required when changing sku_rowid or op_rowid." for f in missing})
            return self._rotate_activity(instance, validated_data)

        closing_fields = {"completed_quantity", "scrap_quantity", "rejected_quantity"}

        if closing_fields & validated_data.keys():
            instance.end_time = timezone.now()

        return super().update(instance, validated_data)
