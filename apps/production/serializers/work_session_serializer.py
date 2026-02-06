from rest_framework import serializers
from apps.production.models.work_session import WorkSession


class WorkSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkSession
        fields = "__all__"
