from django.db.models import Q
from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import AdditionalStampingTime
from apps.stamping.serializers import AdditionalStampingTimeSerializer


class AdditionalStampingTimeViewSet(BaseModelViewSet):
    queryset = AdditionalStampingTime.objects.all()
    serializer_class = AdditionalStampingTimeSerializer
    search_fields = ['code_number', 'engineering_code', 'process', 'machine__name']
    filterset_fields = [
        'code_number', 'engineering_code', 'machine', 'process',
        'standard_time', 'is_active', 'created_by', 'updated_by',
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Times for the active module: its machine type, and either no specific machine or its own machine.
        machine_type = self.request.query_params.get('module_machine_type')
        machine = self.request.query_params.get('module_machine')
        if machine_type and machine_type.isdigit():
            queryset = queryset.filter(machine_type_id=int(machine_type))
        if machine and machine.isdigit():
            queryset = queryset.filter(Q(machine__isnull=True) | Q(machine_id=int(machine)))
        return queryset
