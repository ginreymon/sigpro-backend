from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import AdditionalStampingTime
from apps.stamping.serializers import AdditionalStampingTimeSerializer
from core import option_keys as opt


class AdditionalStampingTimeViewSet(BaseModelViewSet):
    write_options = (opt.MACHINES_CONFIG,)

    queryset = AdditionalStampingTime.objects.all()
    serializer_class = AdditionalStampingTimeSerializer
    search_fields = ['code_number', 'engineering_code', 'process', 'machine__name']
    filterset_fields = [
        'code_number', 'engineering_code', 'machine', 'process',
        'standard_time_minutes', 'is_active', 'created_by', 'updated_by',
    ]
