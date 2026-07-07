from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import AdditionalStampingTime
from apps.stamping.serializers import AdditionalStampingTimeSerializer


class AdditionalStampingTimeViewSet(BaseModelViewSet):
    queryset = AdditionalStampingTime.objects.all()
    serializer_class = AdditionalStampingTimeSerializer
    # process_description is JSONField, unsupported by django-filter's auto filterset
    filterset_fields = [
        'code_number', 'engineering_code', 'machine', 'process',
        'standard_time', 'is_active', 'created_by', 'updated_by',
    ]
