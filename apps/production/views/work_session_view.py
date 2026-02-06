from rest_framework import viewsets
from apps.production.models import WorkSession
from apps.production.serializers import WorkSessionSerializer


class WorkSessionViewSet(viewsets.ModelViewSet):
    queryset = WorkSession.objects.all()
    serializer_class = WorkSessionSerializer
