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

    def create(self, validated_data):
        missing = [f for f in ("op_number", "op_type") if not validated_data.get(f)]
        if missing:
            raise ValidationError({f: "This field is required." for f in missing})

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
        activity = instance.work_session_activity
        work_session = activity.work_session
        user = self.context["request"].user

        work_session.close_all_open_records()
        activity.close()

        new_activity = work_session.work_session_activities.create(
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

        quantity_fields = [
            "planned_quantity",
            "completed_quantity",
            "scrap_quantity",
            "rejected_quantity",
            "ordered_quantity",
        ]

        for field in quantity_fields:
            if field in validated_data and getattr(instance, field) != validated_data[field]:
                instance.end_time = timezone.now()
                break

        return super().update(instance, validated_data)
