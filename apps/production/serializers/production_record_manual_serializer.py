from rest_framework import serializers

from apps.production.serializers.production_record_serializer import ProductionRecordSerializer
from apps.production.services.module_downtime_gap_service import apply_manual_duration


class ProductionRecordManualDurationSerializer(ProductionRecordSerializer):
    """
    Variante de ProductionRecordSerializer para el registro con duración
    manual: además de los campos normales, recibe `duration_seconds` y
    calcula start_time = now - duración / end_time = now, generando el
    ModuleDowntime que cubre el hueco previo si corresponde.

    No reemplaza ni modifica ProductionRecordSerializer — el endpoint y el
    flujo de creación normal (POST /production-records/) siguen intactos.
    """
    duration_seconds = serializers.IntegerField(write_only=True, min_value=1)

    def create(self, validated_data):
        duration_seconds = validated_data.pop("duration_seconds")

        # Reutiliza el create() existente (validaciones de cantidades, manejo
        # de actividad, etc.) — no se duplica esa lógica.
        instance = super().create(validated_data)

        work_session = instance.work_session_activity.work_session
        apply_manual_duration(
            record=instance,
            work_session=work_session,
            duration_seconds=duration_seconds,
            link_field="production_record",
        )

        return instance
