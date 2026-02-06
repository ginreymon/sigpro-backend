from rest_framework import viewsets
from apps.production.models import WorkBreak
from apps.production.serializers import WorkBreakSerializer


class WorkBreakViewSet(viewsets.ModelViewSet):
    queryset = WorkBreak.objects.all()
    serializer_class = WorkBreakSerializer
