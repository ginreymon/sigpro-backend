from django.db import transaction
from rest_framework import serializers
from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models import AdditionalStampingTime
from apps.stamping.models.additional_stamping_time_step import AdditionalStampingTimeStep


class AdditionalStampingTimeStepSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=255)
    # The API keeps exposing `standard_time` (minutes per unit); the column is standard_time_minutes.
    standard_time = serializers.DecimalField(
        source='standard_time_minutes',
        max_digits=10, decimal_places=4, required=False, allow_null=True
    )


class AdditionalStampingTimeSerializer(AuditSerializer):

    machine_name = serializers.SerializerMethodField()
    machine_type_name = serializers.SerializerMethodField()
    steps = AdditionalStampingTimeStepSerializer(many=True, required=False)
    standard_time = serializers.DecimalField(
        source='standard_time_minutes',
        max_digits=10, decimal_places=4, required=False, allow_null=True
    )

    class Meta:
        model = AdditionalStampingTime
        exclude = ['standard_time_minutes']

    def get_machine_name(self, obj):
        return obj.machine.name if obj.machine else None

    def get_machine_type_name(self, obj):
        return obj.machine_type.name if obj.machine_type else None

    @transaction.atomic
    def create(self, validated_data):
        steps_data = validated_data.pop('steps', [])
        instance = super().create(validated_data)
        self._replace_steps(instance, steps_data)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        steps_data = validated_data.pop('steps', None)
        instance = super().update(instance, validated_data)
        if steps_data is not None:
            self._replace_steps(instance, steps_data)
        return instance

    def _replace_steps(self, instance, steps_data):
        instance.steps.all().delete()
        AdditionalStampingTimeStep.objects.bulk_create([
            AdditionalStampingTimeStep(
                additional_stamping_time=instance,
                order=index,
                description=step['description'],
                standard_time_minutes=step.get('standard_time_minutes'),
                created_by=instance.created_by,
                updated_by=instance.updated_by,
            )
            for index, step in enumerate(steps_data)
        ])
