from decimal import Decimal
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db import transaction
from apps.stamping.models.stamping_record import StampingRecord
from apps.stamping.models.additional_stamping_time import AdditionalStampingTime
from apps.stamping.models.stamping_record_additional_time import StampingRecordAdditionalTime
from apps.stamping.repositories.op_stamping_repository import OPStampingRepository
from core.serializers.audit_serializer import AuditSerializer


class AdditionalTimeSelectionSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=AdditionalStampingTime.objects.all())
    count = serializers.IntegerField(min_value=1, default=1)


class StampingRecordSerializer(AuditSerializer):

    additional_times = AdditionalTimeSelectionSerializer(
        many=True, required=False, write_only=True
    )

    class Meta:
        model = StampingRecord
        fields = "__all__"
        read_only_fields = ["start_time", "end_time"]

    @transaction.atomic
    def create(self, validated_data):
        additional_times = validated_data.pop("additional_times", [])

        missing = [f for f in ("op_number", "op_type") if not validated_data.get(f)]
        if missing:
            raise ValidationError({f: "Este campo es obligatorio." for f in missing})

        completed = Decimal(str(validated_data.get("completed_quantity") or 0))

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

        instance = super().create(validated_data)
        instance.end_time = instance.start_time
        instance.save(update_fields=["end_time"])

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
