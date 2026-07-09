from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingStampTypeDescription
from apps.stamping.serializers import StampingStampTypeDescriptionSerializer


class StampingStampTypeDescriptionViewSet(BaseModelViewSet):
    queryset = StampingStampTypeDescription.objects.all()
    serializer_class = StampingStampTypeDescriptionSerializer
