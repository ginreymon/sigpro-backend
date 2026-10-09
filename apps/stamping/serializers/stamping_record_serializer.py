from decimal import Decimal
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db import transaction
from apps.common.serializers.op_record_serializer import OpRecordSerializer, to_decimal
from apps.stamping.models.stamping_record import StampingRecord
from apps.stamping.models.additional_stamping_time import AdditionalStampingTime
from apps.stamping.models.stamping_record_additional_time import StampingRecordAdditionalTime
from apps.stamping.repositories.op_stamping_repository import OPStampingRepository


class AdditionalTimeSelectionSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=AdditionalStampingTime.objects.all())
    count = serializers.IntegerField(min_value=1, default=1)


class StampingRecordSerializer(OpRecordSerializer):

    additional_times = AdditionalTimeSelectionSerializer(
        many=True, required=False, write_only=True
    )
    # additional_times is write_only (create/update payload) — this is the
    # only way to read which additional times a record currently has
    # (e.g. to preload the edit form).
    additional_times_detail = serializers.SerializerMethodField(read_only=True)

    def get_additional_times_detail(self, obj):
        return [
            {"id": row.additional_stamping_time_id, "count": row.count}
            for row in obj.additional_time_selections.all()
        ]

    class Meta(OpRecordSerializer.Meta):
        model = StampingRecord

    def prepare_create(self, validated_data):
        completed = to_decimal(validated_data.get("completed_quantity"))

        if completed > 0:
            order_detail = OPStampingRepository.get_detalle_estampacion_op_json(
                validated_data["op_type"], validated_data["op_number"]
            )

            pending = Decimal("0")
            sam = validated_data.get("stamping_reference_sam")
            if order_detail and sam:
                sam_detail = next(
                    (s for s in order_detail.get("referenceSams") or [] if s.get("id") == sam.id),
                    None,
                )
                if sam_detail:
                    pending = Decimal(str(sam_detail["pending_qty"]))

            if completed > pending:
                raise ValidationError({
                    "non_field_errors": (
                        f"La cantidad ({completed}) supera lo pendiente por estampar ({pending})."
                    )
                })

        validated_data["completed_quantity"] = completed

        return validated_data

    @transaction.atomic
    def create(self, validated_data):
        additional_times = validated_data.pop("additional_times", [])

        instance = super().create(validated_data)

        StampingRecordAdditionalTime.objects.bulk_create([
            StampingRecordAdditionalTime(
                stamping_record=instance,
                additional_stamping_time=item["id"],
                count=item["count"],
                created_by=validated_data.get("created_by"),
                updated_by=validated_data.get("updated_by"),
            )
            for item in additional_times
        ])

        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        additional_times = validated_data.pop("additional_times", None)

        if "completed_quantity" in validated_data:
            completed = to_decimal(validated_data.get("completed_quantity"))

            if completed > 0:
                op_type = validated_data.get("op_type", instance.op_type)
                op_number = validated_data.get("op_number", instance.op_number)
                sam = validated_data.get("stamping_reference_sam", instance.stamping_reference_sam)

                order_detail = OPStampingRepository.get_detalle_estampacion_op_json(op_type, op_number)

                # pending_qty already excludes what this same instance has
                # stamped today — that quantity is added back so the record is
                # not penalized for its own previous contribution when edited.
                pending = Decimal("0")
                if order_detail and sam:
                    sam_detail = next(
                        (s for s in order_detail.get("referenceSams") or [] if s.get("id") == sam.id),
                        None,
                    )
                    if sam_detail:
                        pending = Decimal(str(sam_detail["pending_qty"])) + Decimal(str(instance.completed_quantity))

                if completed > pending:
                    raise ValidationError({
                        "non_field_errors": (
                            f"La cantidad ({completed}) supera lo pendiente por estampar ({pending})."
                        )
                    })

            validated_data["completed_quantity"] = completed

        instance = super().update(instance, validated_data)

        if additional_times is not None:
            existing = {
                row.additional_stamping_time_id: row
                for row in instance.additional_time_selections.all()
            }
            incoming_ids = set()

            for item in additional_times:
                additional_stamping_time = item["id"]
                incoming_ids.add(additional_stamping_time.id)
                row = existing.get(additional_stamping_time.id)
                if row:
                    if row.count != item["count"]:
                        row.count = item["count"]
                        row.save(update_fields=["count"])
                else:
                    StampingRecordAdditionalTime.objects.create(
                        stamping_record=instance,
                        additional_stamping_time=additional_stamping_time,
                        count=item["count"],
                        created_by=validated_data.get("updated_by"),
                        updated_by=validated_data.get("updated_by"),
                    )

            for additional_stamping_time_id, row in existing.items():
                if additional_stamping_time_id not in incoming_ids:
                    row.delete()

        return instance
