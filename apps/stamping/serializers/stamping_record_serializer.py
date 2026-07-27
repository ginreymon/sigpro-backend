from decimal import Decimal
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db import transaction
from apps.stamping.models.stamping_record import StampingRecord
from apps.stamping.repositories.op_stamping_repository import OPStampingRepository
from core.serializers.audit_serializer import AuditSerializer


class AdditionalTimeSelectionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    count = serializers.IntegerField()


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
        print(f"additional_times recibidos: {additional_times}")

        missing = [f for f in ("op_number", "op_type") if not validated_data.get(f)]
        if missing:
            raise ValidationError({f: "Este campo es obligatorio." for f in missing})

        completed = Decimal(str(validated_data.get("completed_quantity") or 0))

        if completed > 0:
            order_detail = OPStampingRepository.get_detalle_estampacion_op_json(
                validated_data["op_type"], validated_data["op_number"]
            )
            pending = Decimal(str(order_detail["pendingQty"])) if order_detail else Decimal("0")

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

        return instance
