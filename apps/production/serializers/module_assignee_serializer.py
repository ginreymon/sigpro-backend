from rest_framework import serializers
from apps.production.models.module_assignee import ModuleAssignee


class ModuleAssigneeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleAssignee
        fields = "__all__"
