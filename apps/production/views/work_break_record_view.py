from rest_framework import viewsets
from apps.production.models import WorkBreakRecord
from apps.production.serializers import WorkBreakRecordSerializer


class WorkBreakRecordViewSet(viewsets.ModelViewSet):
    queryset = WorkBreakRecord.objects.all()
    serializer_class = WorkBreakRecordSerializer
