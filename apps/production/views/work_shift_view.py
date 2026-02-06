from rest_framework import viewsets
from apps.production.models import WorkShift
from apps.production.serializers import WorkShiftSerializer


class WorkShiftViewSet(viewsets.ModelViewSet):
    queryset = WorkShift.objects.all()
    serializer_class = WorkShiftSerializer
