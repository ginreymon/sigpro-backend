from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError
from core.serializers.audit_serializer import AuditSerializer


def to_decimal(value) -> Decimal:
    """Normalizes a possibly empty/None quantity to a Decimal (0 when empty)."""
    return Decimal(str(value or 0))


class OpRecordSerializer(AuditSerializer):
    """Common creation flow of the records of a production order
    (ProductionRecordSerializer and StampingRecordSerializer).

    create() is a template method: it requires the order identity, calls
    `prepare_create()` (per-record validation/normalization, overridden by
    each child), saves the record and closes it at its start time.

    Children must declare their own `Meta(OpRecordSerializer.Meta)` with the
    `model`.
    """

    class Meta:
        fields = "__all__"
        read_only_fields = ["start_time", "end_time"]

    @staticmethod
    def require_op_identity(validated_data):
        missing = [f for f in ("op_number", "op_type") if not validated_data.get(f)]
        if missing:
            raise ValidationError({f: "Este campo es obligatorio." for f in missing})

    def prepare_create(self, validated_data):
        """Hook: validates/normalizes `validated_data` before saving and
        returns it. Runs inside the create() transaction."""
        return validated_data

    def close_at_creation(self, instance):
        # TODO: the time spent per OP must be computed here instead of
        # closing the record at its own start time (zero duration).
        instance.end_time = instance.start_time
        instance.save(update_fields=["end_time"])

    @transaction.atomic
    def create(self, validated_data):
        self.require_op_identity(validated_data)
        validated_data = self.prepare_create(validated_data)

        instance = super().create(validated_data)
        self.close_at_creation(instance)

        return instance
